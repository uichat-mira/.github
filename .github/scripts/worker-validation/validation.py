#!/usr/bin/env python3
"""Trusted Validation Profile helper for Mira External Worker."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

TIERS = ("L0", "L1", "L2", "L3", "L4", "L5")
TIER_INDEX = {tier: index for index, tier in enumerate(TIERS)}
PROFILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
CHECK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
REQUIREMENTS = {"required", "optional", "not_applicable"}
FAILURE_RESULTS = {"REPAIR", "BLOCKED"}
MAX_CHECKS = 24
MAX_COMMAND_CHARS = 4096
MAX_LOG_BYTES = 120_000


class ValidationError(RuntimeError):
    pass


def load_json(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid JSON {path}: {exc}") from exc


def dump_json(value: Any, path: str | Path | None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validate_max_tier(value: str) -> str:
    if value not in TIERS:
        raise ValidationError(f"invalid max tier {value!r}; expected one of {', '.join(TIERS)}")
    return value


def selected_profile(profile_file: str | Path, profile_name: str) -> tuple[dict[str, Any] | None, str, list[str]]:
    errors: list[str] = []
    path = Path(profile_file)
    if not path.is_file():
        return None, "profile_file_missing", ["repository profile file .github/mira-validation-profiles.json is unavailable"]
    try:
        root = load_json(path)
    except ValidationError as exc:
        return None, "profile_file_invalid", [str(exc)]
    if not isinstance(root, dict) or root.get("schema_version") != 1 or not isinstance(root.get("profiles"), dict):
        return None, "profile_file_invalid", ["profile file must have schema_version=1 and an object profiles map"]
    profile = root["profiles"].get(profile_name)
    if not isinstance(profile, dict):
        return None, "profile_missing", [f"validation profile {profile_name!r} is not defined by the repository base"]
    checks = profile.get("checks")
    if not isinstance(checks, list):
        return None, "profile_invalid", ["selected profile checks must be an array"]
    if len(checks) > MAX_CHECKS:
        return None, "profile_invalid", [f"selected profile has {len(checks)} checks; maximum is {MAX_CHECKS}"]

    normalized_checks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(checks):
        if not isinstance(raw, dict):
            errors.append(f"check[{index}] must be an object")
            continue
        cid = raw.get("id")
        tier = raw.get("tier")
        requirement = raw.get("requirement", "required")
        command = raw.get("command")
        failure_result = raw.get("failure_result", "REPAIR")
        if not isinstance(cid, str) or not CHECK_RE.fullmatch(cid):
            errors.append(f"check[{index}] has invalid id")
            continue
        if cid in seen_ids:
            errors.append(f"duplicate check id {cid!r}")
            continue
        seen_ids.add(cid)
        if tier not in TIERS[1:]:
            errors.append(f"check {cid!r} must use tier L1-L5; L0 is reserved for Candidate identity")
            continue
        if requirement not in REQUIREMENTS:
            errors.append(f"check {cid!r} has invalid requirement")
            continue
        if failure_result not in FAILURE_RESULTS:
            errors.append(f"check {cid!r} has invalid failure_result")
            continue
        if requirement == "not_applicable":
            if command not in {None, ""}:
                errors.append(f"check {cid!r} is not_applicable and must not define command")
                continue
            command = None
        else:
            if not isinstance(command, str) or not command.strip():
                errors.append(f"check {cid!r} requires a non-empty command")
                continue
            if len(command) > MAX_COMMAND_CHARS:
                errors.append(f"check {cid!r} command exceeds {MAX_COMMAND_CHARS} characters")
                continue
            command = command.strip()
        normalized_checks.append({
            "id": cid,
            "tier": tier,
            "requirement": requirement,
            "command": command,
            "failure_result": failure_result,
            "_order": index,
        })
    if errors:
        return None, "profile_invalid", errors

    normalized_checks.sort(key=lambda item: (TIER_INDEX[item["tier"]], item["_order"]))
    for item in normalized_checks:
        item.pop("_order", None)

    # Only executable semantics participate in the profile contract identity.
    # Human description changes must not invalidate a recoverable Candidate.
    normalized = {
        "checks": normalized_checks,
    }
    return normalized, "available", []


def contract(args: argparse.Namespace) -> int:
    profile_name = args.profile or ""
    if not profile_name:
        legacy = args.legacy_command or ""
        legacy_available = bool(legacy.strip())
        payload = {
            "schema_version": 1,
            "mode": "legacy",
            "profile": None,
            "max_tier": None,
            "profile_state": "not_requested",
            "profile_sha256": None,
            "legacy_command_sha256": (
                "sha256:" + hashlib.sha256(legacy.encode("utf-8")).hexdigest() if legacy else None
            ),
            "result": "PASS" if legacy_available else "VALIDATION_GAP",
            "gaps": ([] if legacy_available else ["legacy verification_command is empty"]),
        }
        payload["contract_sha256"] = sha256_json(payload)
        dump_json(payload, args.output)
        return 0

    try:
        max_tier = validate_max_tier(args.max_tier)
        tier_error = None
    except ValidationError as exc:
        max_tier = args.max_tier
        tier_error = str(exc)

    if tier_error:
        profile, state, errors = None, "invalid_dispatch_contract", [tier_error]
        contract_result = "BLOCKED"
    elif not PROFILE_RE.fullmatch(profile_name):
        profile, state, errors = None, "profile_invalid", ["invalid validation profile identifier"]
        contract_result = "VALIDATION_GAP"
    else:
        profile, state, errors = selected_profile(args.profile_file, profile_name)
        contract_result = "PASS" if profile is not None else "VALIDATION_GAP"

    payload = {
        "schema_version": 1,
        "mode": "profile",
        "profile": profile_name,
        "max_tier": max_tier,
        "profile_state": state,
        "profile_sha256": sha256_json(profile) if profile is not None else None,
        "legacy_command_sha256": None,
        "result": contract_result,
        "gaps": errors,
    }
    payload["contract_sha256"] = sha256_json(payload)
    dump_json(payload, args.output)
    return 0


def _append_log(log_path: Path, data: bytes) -> bool:
    existing = log_path.stat().st_size if log_path.exists() else 0
    remaining = max(0, MAX_LOG_BYTES - existing)
    truncated = len(data) > remaining
    with log_path.open("ab") as fh:
        if remaining:
            fh.write(data[:remaining])
        if truncated and remaining > 0:
            marker = b"\n[validation log truncated]\n"
            size = log_path.stat().st_size
            if size + len(marker) <= MAX_LOG_BYTES:
                fh.write(marker)
    return truncated


def _candidate_state_digest(repo: str) -> str:
    h = hashlib.sha256()
    for command in (
        ["git", "diff", "--binary", "--"],
        ["git", "diff", "--cached", "--binary", "--"],
    ):
        proc = subprocess.run(command, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode != 0:
            raise ValidationError(proc.stderr.decode("utf-8", errors="replace") or "git diff failed")
        h.update(b"\0".join(part.encode("utf-8") for part in command))
        h.update(b"\0")
        h.update(proc.stdout)

    proc = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise ValidationError(proc.stderr.decode("utf-8", errors="replace") or "git ls-files failed")
    for raw in sorted(part for part in proc.stdout.split(b"\0") if part):
        rel = raw.decode("utf-8", errors="surrogateescape")
        path = Path(repo) / rel
        h.update(b"untracked\0")
        h.update(raw)
        h.update(b"\0")
        if path.is_symlink():
            h.update(b"symlink\0")
            h.update(path.readlink().as_posix().encode("utf-8", errors="surrogateescape"))
        elif path.is_file():
            h.update(path.read_bytes())
        else:
            h.update(b"special")
    return "sha256:" + h.hexdigest()


def _run_command(command: str, cwd: str, log_path: Path, label: str) -> tuple[int, int, bool]:
    started = time.monotonic()
    header = f"\n## {label}\n$ {command}\n".encode("utf-8")
    truncated = _append_log(log_path, header)
    proc = subprocess.Popen(
        ["bash", "-lc", command],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.stdout is None:
        raise ValidationError("validation command stdout pipe is unavailable")
    while True:
        chunk = proc.stdout.read(64 * 1024)
        if not chunk:
            break
        truncated = _append_log(log_path, chunk) or truncated
    return_code = proc.wait()
    duration_ms = int((time.monotonic() - started) * 1000)
    return return_code, duration_ms, truncated


def _check_record(
    *,
    cid: str,
    tier: str,
    requirement: str,
    command: str | None,
    status: str,
    duration_ms: int = 0,
    exit_code: int | None = None,
    reason: str | None = None,
    failure_result: str | None = None,
) -> dict[str, Any]:
    return {
        "id": cid,
        "tier": tier,
        "requirement": requirement,
        "command": command,
        "status": status,
        "duration_ms": duration_ms,
        "exit_code": exit_code,
        "reason": reason,
        "failure_result": failure_result,
    }


def run_validation(args: argparse.Namespace) -> int:
    repo = str(Path(args.repo).resolve())
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_bytes(b"")
    profile_name = args.profile or ""
    max_tier = args.max_tier
    mode = "profile" if profile_name else "legacy"
    checks: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    overall = "PASS"
    failed_check: str | None = None

    if args.restore_outcome == "success":
        checks.append(_check_record(
            cid="candidate_identity", tier="L0", requirement="required",
            command=None, status="passed",
        ))
    else:
        checks.append(_check_record(
            cid="candidate_identity", tier="L0", requirement="required",
            command=None, status="failed",
            reason=f"clean-room restore outcome: {args.restore_outcome}",
            failure_result="BLOCKED",
        ))
        overall = "BLOCKED"
        failed_check = "candidate_identity"

    profile_state = "not_requested"
    profile_sha256 = None
    profile: dict[str, Any] | None = None

    if mode == "profile":
        tier_valid = True
        try:
            max_tier = validate_max_tier(max_tier)
        except ValidationError as exc:
            tier_valid = False
            profile_state = "invalid_dispatch_contract"
            if overall == "PASS":
                overall = "BLOCKED"
            gaps.append({
                "kind": "invalid_dispatch_contract",
                "tier": None,
                "required": True,
                "message": str(exc),
            })

        if tier_valid:
            if not PROFILE_RE.fullmatch(profile_name):
                profile_state = "profile_invalid"
                profile_errors = ["invalid validation profile identifier"]
            else:
                profile, profile_state, profile_errors = selected_profile(args.profile_file, profile_name)
            profile_sha256 = sha256_json(profile) if profile is not None else None
            if profile is None:
                for message in profile_errors:
                    gaps.append({
                        "kind": profile_state,
                        "tier": None,
                        "required": True,
                        "message": message,
                    })
                if overall == "PASS":
                    overall = "VALIDATION_GAP"

    if overall == "PASS":
        if mode == "profile" and TIER_INDEX["L1"] > TIER_INDEX[max_tier]:
            checks.append(_check_record(
                cid="candidate_diff", tier="L1", requirement="required",
                command="git diff --check && git diff --cached --check", status="skipped",
                reason=f"dispatch max tier is {max_tier}",
            ))
            gaps.append({
                "kind": "required_tier_above_dispatch_ceiling",
                "tier": "L1",
                "required": True,
                "check_id": "candidate_diff",
                "message": f"required built-in check 'candidate_diff' at L1 exceeds dispatch max tier {max_tier}",
            })
            overall = "VALIDATION_GAP"
        else:
            diff_command = "git diff --check && git diff --cached --check"
            rc, duration_ms, truncated = _run_command(diff_command, repo, log_path, "L1 candidate_diff")
            checks.append(_check_record(
                cid="candidate_diff", tier="L1", requirement="required",
                command=diff_command, status=("passed" if rc == 0 else "failed"),
                duration_ms=duration_ms, exit_code=rc,
                reason=("validation log truncated" if truncated else None),
                failure_result=("REPAIR" if rc != 0 else None),
            ))
            if rc != 0:
                overall = "REPAIR"
                failed_check = "candidate_diff"

    if overall == "PASS":
        if mode == "legacy":
            command = (args.legacy_command or "").strip()
            if not command:
                overall = "VALIDATION_GAP"
                gaps.append({
                    "kind": "legacy_command_missing",
                    "tier": "legacy-unclassified",
                    "required": True,
                    "message": "legacy verification_command is empty",
                })
            else:
                rc, duration_ms, truncated = _run_command(command, repo, log_path, "legacy verification_command")
                checks.append(_check_record(
                    cid="legacy_verification_command",
                    tier="legacy-unclassified",
                    requirement="required",
                    command=command,
                    status=("passed" if rc == 0 else "failed"),
                    duration_ms=duration_ms,
                    exit_code=rc,
                    reason=("validation log truncated" if truncated else None),
                    failure_result=("REPAIR" if rc != 0 else None),
                ))
                if rc != 0:
                    overall = "REPAIR"
                    failed_check = "legacy_verification_command"
        else:
            if profile is None:
                raise ValidationError("profile-mode validation reached execution without a resolved profile")
            for spec in profile["checks"]:
                    cid = spec["id"]
                    tier = spec["tier"]
                    requirement = spec["requirement"]
                    command = spec["command"]
                    if requirement == "not_applicable":
                        checks.append(_check_record(
                            cid=cid, tier=tier, requirement=requirement,
                            command=None, status="not_applicable",
                        ))
                        continue
                    if TIER_INDEX[tier] > TIER_INDEX[max_tier]:
                        checks.append(_check_record(
                            cid=cid, tier=tier, requirement=requirement,
                            command=command, status="skipped",
                            reason=f"dispatch max tier is {max_tier}",
                        ))
                        if requirement == "required":
                            gaps.append({
                                "kind": "required_tier_above_dispatch_ceiling",
                                "tier": tier,
                                "required": True,
                                "check_id": cid,
                                "message": f"required check {cid!r} at {tier} exceeds dispatch max tier {max_tier}",
                            })
                            overall = "VALIDATION_GAP"
                        continue

                    if overall != "PASS":
                        checks.append(_check_record(
                            cid=cid, tier=tier, requirement=requirement,
                            command=command, status="skipped",
                            reason=f"fail-fast after {failed_check or overall}",
                        ))
                        continue

                    before_state = _candidate_state_digest(repo)
                    rc, duration_ms, truncated = _run_command(command, repo, log_path, f"{tier} {cid}")
                    after_state = _candidate_state_digest(repo)
                    if after_state != before_state:
                        checks.append(_check_record(
                            cid=cid, tier=tier, requirement=requirement,
                            command=command, status="mutated_candidate",
                            duration_ms=duration_ms, exit_code=rc,
                            reason="validation command changed tracked or non-ignored Candidate state",
                            failure_result="BLOCKED",
                        ))
                        overall = "BLOCKED"
                        failed_check = cid
                        continue

                    if rc == 127:
                        checks.append(_check_record(
                            cid=cid, tier=tier, requirement=requirement,
                            command=command, status="unavailable",
                            duration_ms=duration_ms, exit_code=rc,
                            reason="command/capability unavailable (exit 127)",
                        ))
                        gaps.append({
                            "kind": "capability_unavailable",
                            "tier": tier,
                            "required": requirement == "required",
                            "check_id": cid,
                            "message": f"check {cid!r} could not execute because its capability was unavailable",
                        })
                        if requirement == "required":
                            overall = "VALIDATION_GAP"
                            failed_check = cid
                        continue

                    checks.append(_check_record(
                        cid=cid, tier=tier, requirement=requirement,
                        command=command, status=("passed" if rc == 0 else "failed"),
                        duration_ms=duration_ms, exit_code=rc,
                        reason=("validation log truncated" if truncated else None),
                        failure_result=(spec["failure_result"] if rc != 0 else None),
                    ))
                    if rc != 0 and requirement == "required":
                        overall = spec["failure_result"]
                        failed_check = cid

    report = {
        "schema_version": 1,
        "mode": mode,
        "profile": profile_name or None,
        "max_tier": (max_tier if mode == "profile" else None),
        "profile_state": profile_state,
        "profile_sha256": profile_sha256,
        "result": overall,
        "failed_check": failed_check,
        "checks": checks,
        "gaps": gaps,
        "log": {
            "path": str(log_path),
            "max_bytes": MAX_LOG_BYTES,
            "bytes": log_path.stat().st_size if log_path.exists() else 0,
        },
    }
    dump_json(report, args.output)
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("contract")
    c.add_argument("--profile-file", required=True)
    c.add_argument("--profile", default="")
    c.add_argument("--max-tier", default="L3")
    c.add_argument("--legacy-command", default="")
    c.add_argument("--output")
    c.set_defaults(func=contract)

    r = sub.add_parser("run")
    r.add_argument("--repo", required=True)
    r.add_argument("--profile-file", required=True)
    r.add_argument("--profile", default="")
    r.add_argument("--max-tier", default="L3")
    r.add_argument("--legacy-command", default="")
    r.add_argument("--restore-outcome", required=True)
    r.add_argument("--output", required=True)
    r.add_argument("--log", required=True)
    r.set_defaults(func=run_validation)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except ValidationError as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
