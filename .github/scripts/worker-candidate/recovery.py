#!/usr/bin/env python3
"""Deterministic Candidate Recovery helpers for Mira External Worker v2."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

RECOVERY_MARKER_START = "<!-- mira-recovery-candidate:v1"
RECOVERY_MARKER_END = "-->"
AMENDMENT_MARKER = "<!-- mira-contract-amendment:v1 -->"
NOTE_MARKER = "<!-- mira-contract-note:v1 -->"

AMENDMENT_PREFIXES = (
    "contract amendment:",
    "contract clarification:",
    "scope change:",
    "acceptance change:",
    "revision:",
    "return request:",
    "narrowing:",
    "合同修订：",
    "合同澄清：",
    "范围变更：",
    "验收变更：",
    "返工要求：",
    "缩小范围：",
)
NOTE_PREFIXES = (
    "status:",
    "progress:",
    "evidence:",
    "ci:",
    "delivery evidence:",
    "状态：",
    "进展：",
    "证据：",
    "验收证据：",
    "交付证据：",
)


class RecoveryError(RuntimeError):
    pass


def load_json(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"invalid JSON {path}: {exc}") from exc


def dump_json(value: Any, path: str | Path | None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def first_content_line(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("<!--"):
            return stripped
    return ""


def classify_comment(body: str) -> str:
    normalized = normalize_text(body)
    lower = first_content_line(normalized).casefold()
    if AMENDMENT_MARKER in normalized:
        return "amendment"
    if NOTE_MARKER in normalized:
        return "note"
    if any(lower.startswith(prefix.casefold()) for prefix in AMENDMENT_PREFIXES):
        return "amendment"
    if any(lower.startswith(prefix.casefold()) for prefix in NOTE_PREFIXES):
        return "note"
    return "ambiguous"


def fingerprint(args: argparse.Namespace) -> int:
    issue = load_json(args.issue_json)
    comments = load_json(args.comments_json)
    if not isinstance(issue, dict) or not isinstance(comments, list):
        raise RecoveryError("issue must be an object and comments must be a list")

    amendments = []
    notes = []
    ambiguous = []
    for raw in comments:
        if not isinstance(raw, dict):
            continue
        body = normalize_text(raw.get("body"))
        item = {
            "id": raw.get("id"),
            "author": raw.get("author"),
            "created_at": raw.get("created_at"),
            "updated_at": raw.get("updated_at"),
            "body": body,
        }
        kind = classify_comment(body)
        if kind == "amendment":
            amendments.append(item)
        elif kind == "note":
            notes.append(item["id"])
        else:
            ambiguous.append(item)

    amendments.sort(key=lambda x: (x.get("created_at") or "", x.get("id") or 0))
    ambiguous.sort(key=lambda x: (x.get("created_at") or "", x.get("id") or 0))

    verification_command = normalize_text(getattr(args, "verification_command", ""))
    validation_profile = normalize_text(getattr(args, "validation_profile", "")).strip()
    validation_max_tier = normalize_text(getattr(args, "validation_max_tier", "")).strip()
    validation_contract_sha256 = normalize_text(
        getattr(args, "validation_contract_sha256", "")
    ).strip()

    if validation_profile:
        fingerprint_version = "mira-contract-v3-validation"
        execution_contract = {
            "base_branch": normalize_text(getattr(args, "base_branch", "")).strip(),
            "validation_profile": validation_profile,
            "validation_max_tier": validation_max_tier,
            "validation_contract_sha256": validation_contract_sha256,
        }
    else:
        # Preserve the exact v2 legacy fingerprint shape so existing
        # verification_command Candidates remain recoverable during migration.
        fingerprint_version = "mira-contract-v2"
        execution_contract = {
            "base_branch": normalize_text(getattr(args, "base_branch", "")).strip(),
            "verification_command_sha256": (
                "sha256:" + hashlib.sha256(verification_command.encode("utf-8")).hexdigest()
                if verification_command else ""
            ),
        }

    canonical = {
        "fingerprint_version": fingerprint_version,
        "issue": {
            "number": issue.get("number"),
            "title": normalize_text(issue.get("title")).strip(),
            "body": normalize_text(issue.get("body")),
        },
        "execution_contract": execution_contract,
        "trusted_amendments": amendments,
    }
    ambiguity_payload = {
        "guard_version": "mira-contract-ambiguity-v1",
        "trusted_unclassified_comments": ambiguous,
    }
    result = {
        "schema_version": 1,
        "fingerprint_version": canonical["fingerprint_version"],
        "fingerprint": sha256_json(canonical),
        "ambiguity_guard": sha256_json(ambiguity_payload),
        "amendment_ids": [x["id"] for x in amendments],
        "note_ids": notes,
        "ambiguous_comment_ids": [x["id"] for x in ambiguous],
        "canonical_contract": canonical,
    }
    dump_json(result, args.output)
    return 0


def parse_pointer(body: str) -> dict[str, Any] | None:
    start = body.find(RECOVERY_MARKER_START)
    if start < 0:
        return None
    json_start = body.find("\n", start)
    if json_start < 0:
        return None
    end = body.find(RECOVERY_MARKER_END, json_start)
    if end < 0:
        return None
    raw = body[json_start:end].strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        return None
    return value


def discover(args: argparse.Namespace) -> int:
    comments = load_json(args.comments_json)
    if not isinstance(comments, list):
        raise RecoveryError("comments must be a list")
    pointers = []
    invalid_markers = []
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        user = comment.get("user") or {}
        if user.get("login") != "github-actions[bot]" or user.get("type") != "Bot":
            continue
        body = comment.get("body") or ""
        if RECOVERY_MARKER_START not in body:
            continue
        pointer = parse_pointer(body)
        if not pointer:
            invalid_markers.append({
                "comment_id": comment.get("id"),
                "created_at": comment.get("created_at") or "",
            })
            continue
        if pointer.get("repository") != args.repository:
            continue
        if int(pointer.get("issue_number") or 0) != args.issue_number:
            continue
        pointer["_comment_id"] = comment.get("id")
        pointer["_comment_created_at"] = comment.get("created_at") or ""
        pointers.append(pointer)

    # Candidate origin is the freshness boundary. A delayed Delivery-only retry
    # may publish later, but must never replace a Candidate from a newer run.
    pointers.sort(
        key=lambda x: (
            as_int("Candidate origin run id", x.get("candidate_origin_run_id")),
            as_int("Candidate origin run attempt", x.get("candidate_origin_run_attempt")),
            as_int("Candidate origin repair round", x.get("candidate_origin_repair_round", 0)),
            as_int("pointer run id", x.get("run_id")),
            as_int("pointer run attempt", x.get("run_attempt")),
            as_int("pointer comment id", x.get("_comment_id")),
        ),
        reverse=True,
    )

    latest_valid_comment = max(
        ((x.get("_comment_created_at") or "", as_int("pointer comment id", x.get("_comment_id"))) for x in pointers),
        default=None,
    )
    latest_invalid_marker = max(
        ((x.get("created_at") or "", as_int("invalid pointer comment id", x.get("comment_id"))) for x in invalid_markers),
        default=None,
    )
    invalid_latest_pointer = bool(
        latest_invalid_marker is not None
        and (latest_valid_comment is None or latest_invalid_marker > latest_valid_comment)
    )
    result = {
        "schema_version": 1,
        "found": bool(pointers) or invalid_latest_pointer,
        "pointer": pointers[0] if pointers and not invalid_latest_pointer else None,
        "pointer_count": len(pointers),
        "invalid_latest_pointer": invalid_latest_pointer,
        "invalid_pointer_comment_id": (
            latest_invalid_marker[1] if invalid_latest_pointer and latest_invalid_marker else None
        ),
    }
    dump_json(result, args.output)
    return 0


def require_equal(name: str, left: Any, right: Any) -> None:
    if left != right:
        raise RecoveryError(f"{name} mismatch")


def as_int(name: str, value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise RecoveryError(f"{name} is not an integer") from exc


def validate_verify_evidence(
    verify: dict[str, Any],
    *,
    repository: str,
    manifest: dict[str, Any],
) -> tuple[str, str | None]:
    require_equal("verify job role", verify.get("job_role"), "verify")
    require_equal("verify repository", verify.get("repository"), repository)
    require_equal("verify run id", as_int("verify run id", verify.get("run_id")), as_int("candidate run id", manifest.get("run_id")))
    require_equal("verify run attempt", as_int("verify run attempt", verify.get("run_attempt")), as_int("candidate run attempt", manifest.get("run_attempt")))
    require_equal(
        "verify repair round",
        as_int("verify repair round", verify.get("repair_round", 0)),
        as_int("candidate repair round", manifest.get("repair_round", 0)),
    )
    require_equal("verify base SHA", verify.get("base_sha"), manifest.get("base_sha"))
    require_equal("verify patch digest", verify.get("candidate_patch_sha256"), manifest.get("candidate_patch_sha256"))
    require_equal("verify tree", verify.get("candidate_tree_oid"), manifest.get("candidate_tree_oid"))
    require_equal("verify contract fingerprint", verify.get("contract_fingerprint"), manifest.get("contract_fingerprint"))
    status = verify.get("terminal_status")
    if status not in {"success", "failure"}:
        raise RecoveryError("verify terminal status is invalid")

    validation_result = verify.get("validation_result")
    if validation_result is not None:
        if validation_result not in {"PASS", "REPAIR", "BLOCKED", "VALIDATION_GAP"}:
            raise RecoveryError("verify validation_result is invalid")
        if status == "success" and validation_result != "PASS":
            raise RecoveryError("successful Verify evidence must report Validation PASS")
        if status == "failure" and validation_result == "PASS":
            raise RecoveryError("failed Verify evidence cannot report Validation PASS")

    return status, validation_result


def validate_delivery_evidence(
    delivery: dict[str, Any],
    *,
    repository: str,
    pointer: dict[str, Any],
    manifest: dict[str, Any],
) -> str:
    require_equal("delivery job role", delivery.get("job_role"), "delivery")
    require_equal("delivery repository", delivery.get("repository"), repository)
    require_equal("delivery run id", as_int("delivery run id", delivery.get("run_id")), as_int("pointer run id", pointer.get("run_id")))
    require_equal("delivery run attempt", as_int("delivery run attempt", delivery.get("run_attempt")), as_int("pointer run attempt", pointer.get("run_attempt")))
    require_equal("delivery base SHA", delivery.get("base_sha"), manifest.get("base_sha"))
    require_equal("delivery worker branch", delivery.get("worker_branch"), pointer.get("worker_branch"))
    require_equal("delivery patch digest", delivery.get("candidate_patch_sha256"), manifest.get("candidate_patch_sha256"))
    require_equal("delivery tree", delivery.get("candidate_tree_oid"), manifest.get("candidate_tree_oid"))
    require_equal(
        "delivery Draft PR URL",
        delivery.get("draft_pr_url") or None,
        pointer.get("draft_pr_url") or None,
    )
    status = delivery.get("terminal_status")
    if status not in {"success", "failure"}:
        raise RecoveryError("delivery terminal status is invalid")
    if status == "success":
        if not delivery.get("commit_sha") or not delivery.get("draft_pr_url"):
            raise RecoveryError("successful Delivery evidence is missing commit or Draft PR identity")
        stages = delivery.get("stages")
        if not isinstance(stages, dict) or any(stages.get(name) != "success" for name in (
            "restore", "verified_identity", "commit_push", "draft_pr", "draft_pr_boundary"
        )):
            raise RecoveryError("successful Delivery evidence has incomplete stage results")
    return status


def decide(args: argparse.Namespace) -> int:
    contract = load_json(args.current_contract)
    pointer = load_json(args.pointer)
    manifest = load_json(args.candidate_manifest)

    result = {
        "schema_version": 1,
        "mode": "recovery_failed",
        "run_worker": False,
        "reuse_candidate": False,
        "reason": None,
        "source_run_id": pointer.get("run_id") if isinstance(pointer, dict) else None,
        "source_run_attempt": pointer.get("run_attempt") if isinstance(pointer, dict) else None,
        "source_base_sha": pointer.get("base_sha") if isinstance(pointer, dict) else None,
        "repair_round": (
            int(pointer.get("candidate_origin_repair_round", 0))
            if isinstance(pointer, dict) and str(pointer.get("candidate_origin_repair_round", 0)).isdigit()
            else 0
        ),
    }

    try:
        if not isinstance(contract, dict) or not isinstance(pointer, dict) or not isinstance(manifest, dict):
            raise RecoveryError("contract, pointer, and Candidate manifest must be objects")
        require_equal("Candidate schema version", manifest.get("schema_version"), 1)
        require_equal("repository", manifest.get("repository"), args.repository)
        require_equal("pointer repository", pointer.get("repository"), args.repository)
        require_equal("issue", as_int("Candidate Issue number", manifest.get("issue_number")), args.issue_number)
        require_equal("pointer Issue number", as_int("pointer Issue number", pointer.get("issue_number")), args.issue_number)
        require_equal("Candidate origin run id", as_int("Candidate run id", manifest.get("run_id")), as_int("pointer Candidate origin run id", pointer.get("candidate_origin_run_id")))
        require_equal("Candidate origin run attempt", as_int("Candidate run attempt", manifest.get("run_attempt")), as_int("pointer Candidate origin run attempt", pointer.get("candidate_origin_run_attempt")))
        candidate_repair_round = as_int("Candidate repair round", manifest.get("repair_round", 0))
        pointer_repair_round = as_int("pointer Candidate origin repair round", pointer.get("candidate_origin_repair_round", 0))
        require_equal("Candidate origin repair round", candidate_repair_round, pointer_repair_round)
        require_equal("base branch", manifest.get("base_branch"), pointer.get("base_branch"))
        expected_worker_branch = (
            f"feat/worker-{args.issue_number}-"
            f"{as_int('Candidate run id', manifest.get('run_id'))}-"
            f"{as_int('Candidate run attempt', manifest.get('run_attempt'))}"
        )
        require_equal("Candidate worker branch", pointer.get("worker_branch"), expected_worker_branch)
        require_equal("base SHA", manifest.get("base_sha"), pointer.get("base_sha"))
        require_equal("candidate patch digest", manifest.get("candidate_patch_sha256"), pointer.get("candidate_patch_sha256"))
        require_equal("candidate tree", manifest.get("candidate_tree_oid"), pointer.get("candidate_tree_oid"))
        require_equal("candidate contract fingerprint", manifest.get("contract_fingerprint"), pointer.get("contract_fingerprint"))
        if not isinstance(pointer.get("run_id"), (int, str)) or not str(pointer.get("run_id")).isdigit():
            raise RecoveryError("pointer run id is invalid")
        if not isinstance(pointer.get("run_attempt"), (int, str)) or not str(pointer.get("run_attempt")).isdigit():
            raise RecoveryError("pointer run attempt is invalid")
    except RecoveryError as exc:
        result["reason"] = str(exc)
        dump_json(result, args.output)
        return 0

    if (
        contract.get("fingerprint") != pointer.get("contract_fingerprint")
        or contract.get("ambiguity_guard") != pointer.get("ambiguity_guard")
    ):
        result.update(
            mode="contract_drift",
            run_worker=False,
            reuse_candidate=False,
            reason="current_contract_differs_from_candidate_contract_requires_maintainer_review",
        )
        dump_json(result, args.output)
        return 0

    lifecycle_state = pointer.get("lifecycle_state")
    if lifecycle_state == "ESCALATED":
        result.update(
            mode="escalated",
            run_worker=False,
            reuse_candidate=False,
            reason="prior_lifecycle_escalated_to_maintainer",
        )
        dump_json(result, args.output)
        return 0
    if lifecycle_state == "BLOCKED":
        result.update(
            mode="recovery_failed",
            run_worker=False,
            reuse_candidate=False,
            reason="prior_lifecycle_blocked_requires_maintainer_review",
        )
        dump_json(result, args.output)
        return 0

    verify_state = pointer.get("verification_state") or "skipped"
    delivery_state = pointer.get("delivery_state") or "skipped"
    verify = load_json(args.verify_run) if args.verify_run else None
    delivery = load_json(args.delivery_run) if args.delivery_run else None

    try:
        if verify_state in {"success", "failure"}:
            if not isinstance(verify, dict):
                raise RecoveryError("trusted Verify evidence is missing")
            verify_status, validation_result = validate_verify_evidence(
                verify, repository=args.repository, manifest=manifest
            )
            require_equal("pointer Verify state", verify_status, verify_state)
        elif verify_state == "skipped":
            if verify is not None:
                raise RecoveryError("Verify evidence exists while pointer state is skipped")
            verify_status = "skipped"
            validation_result = None
        else:
            raise RecoveryError("pointer Verify state is invalid")

        if delivery_state in {"success", "failure"}:
            if not isinstance(delivery, dict):
                raise RecoveryError("trusted Delivery evidence is missing")
            delivery_status = validate_delivery_evidence(
                delivery,
                repository=args.repository,
                pointer=pointer,
                manifest=manifest,
            )
            if delivery_state == "success" and delivery_status != "success":
                raise RecoveryError("pointer reports Delivery success but evidence reports failure")
            # A failure result may mean the evidence upload failed after all Delivery side effects
            # completed. The trusted evidence itself decides whether delivery is complete.
        elif delivery_state == "skipped":
            if delivery is not None:
                raise RecoveryError("Delivery evidence exists while pointer state is skipped")
            delivery_status = "skipped"
        else:
            raise RecoveryError("pointer Delivery state is invalid")
    except RecoveryError as exc:
        result["reason"] = str(exc)
        dump_json(result, args.output)
        return 0

    if delivery_status in {"success", "failure"} and verify_status != "success":
        result["reason"] = "Delivery evidence exists without a trusted Verify PASS"
        dump_json(result, args.output)
        return 0

    if delivery_status == "success":
        result.update(
            mode="delivery_complete",
            run_worker=False,
            reuse_candidate=False,
            reason="prior_candidate_already_delivered",
        )
        dump_json(result, args.output)
        return 0

    if verify_status == "success":
        result.update(
            mode="delivery_retry_only",
            run_worker=False,
            reuse_candidate=True,
            reason="verified_candidate_not_delivered",
        )
        dump_json(result, args.output)
        return 0

    if verify_status == "failure":
        if validation_result in {"BLOCKED", "VALIDATION_GAP"}:
            result.update(
                mode="recovery_failed",
                run_worker=False,
                reuse_candidate=False,
                reason=(
                    "prior_validation_blocked"
                    if validation_result == "BLOCKED"
                    else "prior_validation_gap_requires_contract_or_maintainer_change"
                ),
                validation_result=validation_result,
            )
        elif validation_result == "REPAIR" and result["repair_round"] >= 2:
            result.update(
                mode="escalated",
                run_worker=False,
                reuse_candidate=False,
                reason="repair_round_limit_exhausted",
                validation_result=validation_result,
            )
        else:
            # Historical Verify evidence without validation_result preserves the
            # pre-AGT-067 continuation path. Structured REPAIR remains recoverable
            # only while the bounded AGT-068 repair budget is not exhausted.
            result.update(
                mode="recoverable",
                run_worker=True,
                reuse_candidate=True,
                reason=(
                    "prior_validation_repair"
                    if validation_result == "REPAIR"
                    else "prior_verification_failed"
                ),
                validation_result=validation_result,
            )
        dump_json(result, args.output)
        return 0

    result.update(
        mode="recoverable",
        run_worker=True,
        reuse_candidate=True,
        reason="prior_candidate_unverified",
    )
    dump_json(result, args.output)
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    fp = sub.add_parser("fingerprint")
    fp.add_argument("--issue-json", required=True)
    fp.add_argument("--comments-json", required=True)
    fp.add_argument("--base-branch", required=True)
    fp.add_argument("--verification-command", default="")
    fp.add_argument("--validation-profile", default="")
    fp.add_argument("--validation-max-tier", default="")
    fp.add_argument("--validation-contract-sha256", default="")
    fp.add_argument("--output")
    fp.set_defaults(func=fingerprint)

    disc = sub.add_parser("discover-pointer")
    disc.add_argument("--comments-json", required=True)
    disc.add_argument("--repository", required=True)
    disc.add_argument("--issue-number", required=True, type=int)
    disc.add_argument("--output")
    disc.set_defaults(func=discover)

    dec = sub.add_parser("decide")
    dec.add_argument("--current-contract", required=True)
    dec.add_argument("--pointer", required=True)
    dec.add_argument("--candidate-manifest", required=True)
    dec.add_argument("--verify-run")
    dec.add_argument("--delivery-run")
    dec.add_argument("--repository", required=True)
    dec.add_argument("--issue-number", required=True, type=int)
    dec.add_argument("--output")
    dec.set_defaults(func=decide)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except RecoveryError as exc:
        print(f"recovery error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
