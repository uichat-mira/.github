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

    canonical = {
        "fingerprint_version": "mira-contract-v1",
        "issue": {
            "number": issue.get("number"),
            "title": normalize_text(issue.get("title")).strip(),
            "body": normalize_text(issue.get("body")),
        },
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
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        user = comment.get("user") or {}
        if user.get("login") != "github-actions[bot]" or user.get("type") != "Bot":
            continue
        pointer = parse_pointer(comment.get("body") or "")
        if not pointer:
            continue
        if pointer.get("repository") != args.repository:
            continue
        if int(pointer.get("issue_number") or 0) != args.issue_number:
            continue
        pointer["_comment_id"] = comment.get("id")
        pointer["_comment_created_at"] = comment.get("created_at")
        pointers.append(pointer)

    pointers.sort(
        key=lambda x: (
            x.get("run_id") or 0,
            x.get("run_attempt") or 0,
            x.get("_comment_id") or 0,
        ),
        reverse=True,
    )
    result = {
        "schema_version": 1,
        "found": bool(pointers),
        "pointer": pointers[0] if pointers else None,
        "pointer_count": len(pointers),
    }
    dump_json(result, args.output)
    return 0


def require_equal(name: str, left: Any, right: Any) -> None:
    if left != right:
        raise RecoveryError(f"{name} mismatch")


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
        "source_run_id": pointer.get("run_id"),
        "source_run_attempt": pointer.get("run_attempt"),
        "source_base_sha": pointer.get("base_sha"),
    }

    try:
        require_equal("repository", manifest.get("repository"), args.repository)
        require_equal("issue", int(manifest.get("issue_number") or 0), args.issue_number)
        require_equal("base SHA", manifest.get("base_sha"), pointer.get("base_sha"))
        require_equal(
            "candidate patch digest",
            manifest.get("candidate_patch_sha256"),
            pointer.get("candidate_patch_sha256"),
        )
        require_equal(
            "candidate tree",
            manifest.get("candidate_tree_oid"),
            pointer.get("candidate_tree_oid"),
        )
        require_equal(
            "candidate contract fingerprint",
            manifest.get("contract_fingerprint"),
            pointer.get("contract_fingerprint"),
        )
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
            run_worker=True,
            reuse_candidate=False,
            reason="current_contract_differs_from_candidate_contract",
        )
        dump_json(result, args.output)
        return 0

    delivery = load_json(args.delivery_run) if args.delivery_run else None
    verify = load_json(args.verify_run) if args.verify_run else None

    if isinstance(delivery, dict) and delivery.get("terminal_status") == "success":
        result.update(
            mode="delivery_complete",
            run_worker=False,
            reuse_candidate=False,
            reason="prior_candidate_already_delivered",
        )
        dump_json(result, args.output)
        return 0

    if isinstance(verify, dict) and verify.get("terminal_status") == "success":
        try:
            require_equal(
                "verify patch digest",
                verify.get("candidate_patch_sha256"),
                manifest.get("candidate_patch_sha256"),
            )
            require_equal(
                "verify tree",
                verify.get("candidate_tree_oid"),
                manifest.get("candidate_tree_oid"),
            )
        except RecoveryError as exc:
            result["reason"] = str(exc)
            dump_json(result, args.output)
            return 0
        result.update(
            mode="delivery_retry_only",
            run_worker=False,
            reuse_candidate=True,
            reason="verified_candidate_not_delivered",
        )
        dump_json(result, args.output)
        return 0

    if isinstance(verify, dict) and verify.get("terminal_status") == "failure":
        result.update(
            mode="recoverable",
            run_worker=True,
            reuse_candidate=True,
            reason="prior_verification_failed",
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
