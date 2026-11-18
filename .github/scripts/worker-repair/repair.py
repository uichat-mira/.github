#!/usr/bin/env python3
"""Bounded Return-to-Worker state and handoff helper for Mira External Worker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

VALIDATION_RESULTS = {"PASS", "REPAIR", "BLOCKED", "VALIDATION_GAP"}
PRECONDITIONS = {"ok", "contract_drift", "identity_mismatch", "security", "permission", "corrupted_identity"}
MAX_REPAIR_ROUNDS = 2
MAX_CONTEXT_BYTES = 64 * 1024
MAX_ISSUE_BODY_CHARS = 20_000
MAX_AMENDMENTS = 24
MAX_AMENDMENT_BODY_CHARS = 4_000


class RepairError(RuntimeError):
    pass


def load_json(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RepairError(f"invalid JSON {path}: {exc}") from exc


def dump_json(value: Any, path: str | Path | None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if len(text.encode("utf-8")) > MAX_CONTEXT_BYTES and path:
        raise RepairError(f"structured repair output exceeds {MAX_CONTEXT_BYTES} bytes")
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def normalize_round(value: int) -> int:
    if value < 0 or value > MAX_REPAIR_ROUNDS:
        raise RepairError(f"completed repair rounds must be 0-{MAX_REPAIR_ROUNDS}")
    return value


def decide(args: argparse.Namespace) -> int:
    completed = normalize_round(args.completed_rounds)
    result = args.validation_result
    if result not in VALIDATION_RESULTS:
        raise RepairError(f"unsupported validation result {result!r}")
    if args.precondition not in PRECONDITIONS:
        raise RepairError(f"unsupported repair precondition {args.precondition!r}")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "validation_result": result,
        "completed_repair_rounds": completed,
        "repair_round_limit": MAX_REPAIR_ROUNDS,
        "state": None,
        "run_worker": False,
        "next_repair_round": None,
        "reason": None,
    }

    if args.precondition != "ok":
        payload.update(
            state="BLOCKED",
            reason=f"repair_precondition_{args.precondition}",
        )
    elif result == "PASS":
        payload.update(state="VERIFIED", reason="validation_passed")
    elif result == "BLOCKED":
        payload.update(state="BLOCKED", reason="validation_blocked")
    elif result == "VALIDATION_GAP":
        payload.update(state="BLOCKED", reason="validation_gap_requires_maintainer_review")
    elif completed >= MAX_REPAIR_ROUNDS:
        payload.update(
            state="ESCALATED",
            next_repair_round=completed + 1,
            reason="repair_round_limit_exhausted",
        )
    else:
        payload.update(
            state="RETURNED",
            run_worker=True,
            next_repair_round=completed + 1,
            reason="validation_repair_returned_to_worker",
        )

    dump_json(payload, args.output)
    return 0


def _safe_issue(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RepairError("issue snapshot must be an object")
    number = raw.get("number", raw.get("issue_number"))
    if not isinstance(number, int) or number < 1:
        raise RepairError("issue snapshot has invalid number")
    title = raw.get("title")
    body = raw.get("body") or ""
    if not isinstance(title, str) or not isinstance(body, str):
        raise RepairError("issue title/body must be strings")
    if len(body) > MAX_ISSUE_BODY_CHARS:
        body = body[:MAX_ISSUE_BODY_CHARS] + "\n[issue body truncated]"
    return {"number": number, "title": title, "body": body}


def _safe_amendments(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raise RepairError("trusted amendments snapshot must be an array")
    if len(raw) > MAX_AMENDMENTS:
        raise RepairError(f"trusted amendments exceed {MAX_AMENDMENTS}")
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        body = item.get("body") or ""
        if not isinstance(body, str):
            continue
        if len(body) > MAX_AMENDMENT_BODY_CHARS:
            body = body[:MAX_AMENDMENT_BODY_CHARS] + "\n[amendment truncated]"
        out.append({
            "id": item.get("id"),
            "author": item.get("author"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "body": body,
        })
    return out


def _safe_candidate(raw: Any, *, expected_round: int) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise RepairError("candidate manifest must use schema_version=1")
    repair_round = raw.get("repair_round", 0)
    if repair_round != expected_round:
        raise RepairError(
            f"source Candidate repair round {repair_round!r} does not match expected {expected_round}"
        )
    fields = (
        "repository",
        "issue_number",
        "run_id",
        "run_attempt",
        "repair_round",
        "base_branch",
        "base_sha",
        "contract_fingerprint",
        "candidate_patch_sha256",
        "candidate_tree_oid",
        "provider",
        "model",
        "worker_outcome",
        "created_at",
    )
    result = {key: raw.get(key) for key in fields}
    result["repair_round"] = repair_round
    return result


def _safe_validation(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise RepairError("Validation Report must use schema_version=1")
    if raw.get("result") != "REPAIR":
        raise RepairError("Return-to-Worker context requires Validation REPAIR")

    checks = raw.get("checks")
    gaps = raw.get("gaps")
    if not isinstance(checks, list) or not isinstance(gaps, list):
        raise RepairError("Validation Report checks/gaps must be arrays")

    safe_checks = []
    for item in checks[:32]:
        if not isinstance(item, dict):
            continue
        safe_checks.append({
            key: item.get(key)
            for key in (
                "id",
                "tier",
                "requirement",
                "status",
                "duration_ms",
                "exit_code",
                "reason",
                "failure_result",
            )
        })
    safe_gaps = []
    for item in gaps[:24]:
        if not isinstance(item, dict):
            continue
        safe_gaps.append({
            key: item.get(key)
            for key in ("kind", "tier", "required", "check_id", "message")
        })

    return {
        "result": raw.get("result"),
        "profile": raw.get("profile"),
        "max_tier": raw.get("max_tier"),
        "profile_state": raw.get("profile_state"),
        "profile_sha256": raw.get("profile_sha256"),
        "failed_check": raw.get("failed_check"),
        "checks": safe_checks,
        "gaps": safe_gaps,
    }


def context(args: argparse.Namespace) -> int:
    repair_round = args.repair_round
    if repair_round < 1 or repair_round > MAX_REPAIR_ROUNDS:
        raise RepairError(f"repair round must be 1-{MAX_REPAIR_ROUNDS}")

    issue = _safe_issue(load_json(args.issue_json))
    amendments = _safe_amendments(load_json(args.amendments_json))
    candidate = _safe_candidate(
        load_json(args.candidate_manifest),
        expected_round=repair_round - 1,
    )
    validation = _safe_validation(load_json(args.validation_report))

    if candidate.get("issue_number") != issue["number"]:
        raise RepairError("Candidate Issue does not match repair Issue")

    payload = {
        "schema_version": 1,
        "state": "RETURNED",
        "repair_round": repair_round,
        "issue": issue,
        "trusted_amendments": amendments,
        "candidate": candidate,
        "validation": validation,
        "evidence": {
            "validation_artifact_name": args.validation_artifact_name,
        },
        "worker_instruction": {
            "continue_same_issue": True,
            "preserve_correct_work": True,
            "address_trusted_failure_first": True,
            "restart_discovery_without_evidence": False,
            "previous_worker_narrative_is_trusted_pass": False,
            "github_mutation_authority": False,
        },
        "content_policy": (
            "structured trusted handoff only; no provider credentials, environment dumps, "
            "private reasoning, raw model transcript, or raw validation log"
        ),
    }
    dump_json(payload, args.output)
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("decide")
    d.add_argument("--validation-result", required=True)
    d.add_argument("--completed-rounds", required=True, type=int)
    d.add_argument("--precondition", default="ok")
    d.add_argument("--output")
    d.set_defaults(func=decide)

    c = sub.add_parser("context")
    c.add_argument("--issue-json", required=True)
    c.add_argument("--amendments-json", required=True)
    c.add_argument("--candidate-manifest", required=True)
    c.add_argument("--validation-report", required=True)
    c.add_argument("--validation-artifact-name", required=True)
    c.add_argument("--repair-round", required=True, type=int)
    c.add_argument("--output", required=True)
    c.set_defaults(func=context)

    return p


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except RepairError as exc:
        print(f"repair error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
