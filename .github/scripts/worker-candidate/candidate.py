#!/usr/bin/env python3
"""Capture and restore a Mira External Worker v2 Candidate.

The Candidate is an exact Git tree snapshot expressed as a binary patch from an
immutable base commit plus a versioned manifest. This tool never commits, pushes,
or mutates GitHub state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Iterable

SCHEMA_VERSION = 1
DEFAULT_MAX_PATCH_BYTES = 10 * 1024 * 1024
CONTRACT_FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEX_OID_RE = re.compile(r"^[0-9a-f]{40,64}$")
WORKER_OUTCOME_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
SENSITIVE_BASENAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    ".npmrc",
    ".pypirc",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "service-account.json",
}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
SAFE_ENV_TEMPLATE_NAMES = {".env.example", ".env.sample", ".env.template"}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
)


class CandidateError(RuntimeError):
    pass


def run_git(repo: Path, args: Iterable[str], *, index_file: Path | None = None, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    env.setdefault("LC_ALL", "C")
    if index_file is not None:
        env["GIT_INDEX_FILE"] = str(index_file)
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        raise CandidateError(f"git {' '.join(args)} failed: {stderr}")
    return proc


def git_text(repo: Path, args: Iterable[str], *, index_file: Path | None = None) -> str:
    return run_git(repo, args, index_file=index_file).stdout.decode("utf-8").strip()


def ensure_repo(repo: Path) -> None:
    if git_text(repo, ["rev-parse", "--is-inside-work-tree"]) != "true":
        raise CandidateError(f"not a Git worktree: {repo}")


def normalize_base_sha(repo: Path, base_sha: str) -> str:
    resolved = git_text(repo, ["rev-parse", f"{base_sha}^{{commit}}"])
    if not HEX_OID_RE.fullmatch(resolved):
        raise CandidateError("base SHA did not resolve to a supported Git object id")
    return resolved


def path_is_sensitive(path: str) -> bool:
    p = PurePosixPath(path)
    name = p.name.lower()
    if name in SAFE_ENV_TEMPLATE_NAMES:
        return False
    if name in SENSITIVE_BASENAMES:
        return True
    if any(name.endswith(suffix) for suffix in SENSITIVE_SUFFIXES):
        return True
    return False


def candidate_index(repo: Path, base_sha: str) -> tuple[Path, list[str]]:
    fd, raw_path = tempfile.mkstemp(prefix="mira-candidate-index-")
    os.close(fd)
    index = Path(raw_path)
    index.unlink(missing_ok=True)
    try:
        run_git(repo, ["read-tree", base_sha], index_file=index)
        run_git(repo, ["add", "-A", "--", "."], index_file=index)
        changed_raw = run_git(
            repo,
            ["diff", "--cached", "--name-only", "-z", base_sha],
            index_file=index,
        ).stdout
        changed = [part.decode("utf-8", errors="surrogateescape") for part in changed_raw.split(b"\0") if part]
        return index, changed
    except Exception:
        index.unlink(missing_ok=True)
        raise


def staged_mode_and_blob(repo: Path, index: Path, path: str) -> tuple[str | None, bytes | None]:
    raw = run_git(repo, ["ls-files", "-s", "-z", "--", path], index_file=index).stdout
    if not raw:
        return None, None
    entry = raw.split(b"\0", 1)[0].decode("utf-8", errors="surrogateescape")
    prefix, _ = entry.split("\t", 1)
    mode, oid, _stage = prefix.split(" ", 2)
    if mode == "160000":
        raise CandidateError(f"unsupported changed gitlink/submodule: {path}")
    blob = run_git(repo, ["cat-file", "blob", oid]).stdout
    return mode, blob


def enforce_safety(repo: Path, index: Path, changed_paths: list[str]) -> None:
    for path in changed_paths:
        if path_is_sensitive(path):
            raise CandidateError(f"candidate rejected by sensitive-path policy: {path}")
        _mode, blob = staged_mode_and_blob(repo, index, path)
        if blob is None:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(blob):
                raise CandidateError(f"candidate rejected by secret-content policy: {path}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    out = Path(args.output).resolve()
    ensure_repo(repo)

    base_sha = normalize_base_sha(repo, args.base_sha)
    run_git(repo, ["check-ref-format", "--branch", args.base_branch])
    if not re.fullmatch(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", args.repository):
        raise CandidateError("repository must use owner/name form")
    if not args.run_id.strip():
        raise CandidateError("run id must be non-empty")
    if not CONTRACT_FINGERPRINT_RE.fullmatch(args.contract_fingerprint):
        raise CandidateError("contract fingerprint must be sha256:<64 lowercase hex>")
    if not WORKER_OUTCOME_RE.fullmatch(args.worker_outcome):
        raise CandidateError("worker outcome must be a lowercase stable token")
    if args.issue_number < 1 or args.run_attempt < 1:
        raise CandidateError("issue number and run attempt must be positive")
    if args.max_patch_bytes < 0:
        raise CandidateError("max patch bytes must be non-negative")

    if out.exists() and any(out.iterdir()):
        raise CandidateError("candidate output directory must be empty")

    index, changed_paths = candidate_index(repo, base_sha)
    try:
        enforce_safety(repo, index, changed_paths)
        out.mkdir(parents=True, exist_ok=True)
        patch_path = out / "candidate.patch"
        patch = run_git(
            repo,
            [
                "diff",
                "--cached",
                "--binary",
                "--full-index",
                "--find-renames",
                "--no-ext-diff",
                "--no-textconv",
                base_sha,
            ],
            index_file=index,
        ).stdout
        patch_path.write_bytes(patch)
        for pattern in SECRET_PATTERNS:
            if pattern.search(patch):
                patch_path.unlink(missing_ok=True)
                raise CandidateError("candidate rejected because patch contains secret-like content")
        patch_bytes = len(patch)
        if patch_bytes > args.max_patch_bytes:
            patch_path.unlink(missing_ok=True)
            raise CandidateError(
                f"candidate patch exceeds trusted size limit: {patch_bytes} > {args.max_patch_bytes} bytes"
            )

        tree_oid = git_text(repo, ["write-tree"], index_file=index)
        if not HEX_OID_RE.fullmatch(tree_oid):
            raise CandidateError("candidate tree did not resolve to a supported Git object id")

        created_at = args.created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "repository": args.repository,
            "issue_number": args.issue_number,
            "run_id": args.run_id,
            "run_attempt": args.run_attempt,
            "base_branch": args.base_branch,
            "base_sha": base_sha,
            "contract_fingerprint": args.contract_fingerprint,
            "candidate_patch_sha256": f"sha256:{sha256_file(patch_path)}",
            "candidate_patch_bytes": patch_bytes,
            "candidate_tree_oid": tree_oid,
            "provider": args.provider or None,
            "model": args.model or None,
            "worker_outcome": args.worker_outcome,
            "created_at": created_at,
            "changed_paths": changed_paths,
            "safety": {
                "max_patch_bytes": args.max_patch_bytes,
                "sensitive_path_check": True,
                "secret_content_heuristics": True,
                "submodule_changes_supported": False,
                "raw_environment_persisted": False,
                "model_reasoning_persisted": False,
            },
        }
        (out / "candidate.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "candidate_patch_sha256": manifest["candidate_patch_sha256"],
            "candidate_tree_oid": tree_oid,
            "changed_path_count": len(changed_paths),
            "patch_bytes": patch_bytes,
        }, sort_keys=True))
    finally:
        index.unlink(missing_ok=True)
    return 0


def load_manifest(candidate_dir: Path) -> dict:
    try:
        manifest = json.loads((candidate_dir / "candidate.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateError(f"invalid candidate manifest: {exc}") from exc
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise CandidateError(f"unsupported candidate schema_version: {manifest.get('schema_version')!r}")
    required = {
        "repository", "issue_number", "run_id", "run_attempt", "base_branch", "base_sha",
        "contract_fingerprint", "candidate_patch_sha256", "candidate_patch_bytes",
        "candidate_tree_oid", "worker_outcome", "created_at",
    }
    missing = sorted(required.difference(manifest))
    if missing:
        raise CandidateError(f"candidate manifest missing required fields: {', '.join(missing)}")
    return manifest


def ensure_clean(repo: Path) -> None:
    status = run_git(repo, ["status", "--porcelain=v1", "-z"]).stdout
    if status:
        raise CandidateError("restore target must be a clean Git worktree")


def restore(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    candidate_dir = Path(args.candidate_dir).resolve()
    ensure_repo(repo)
    ensure_clean(repo)
    manifest = load_manifest(candidate_dir)

    if manifest["repository"] != args.expected_repository:
        raise CandidateError("candidate repository identity mismatch")
    if int(manifest["issue_number"]) != args.expected_issue_number:
        raise CandidateError("candidate Issue identity mismatch")
    expected_base = normalize_base_sha(repo, args.expected_base_sha)
    if manifest["base_sha"] != expected_base:
        raise CandidateError("candidate base SHA does not match trusted expected base")
    head = git_text(repo, ["rev-parse", "HEAD"])
    if head != expected_base:
        raise CandidateError("restore target HEAD is not the candidate exact base SHA")
    if args.expected_contract_fingerprint and manifest["contract_fingerprint"] != args.expected_contract_fingerprint:
        raise CandidateError("candidate contract fingerprint mismatch")
    if not CONTRACT_FINGERPRINT_RE.fullmatch(str(manifest["contract_fingerprint"])):
        raise CandidateError("candidate contract fingerprint format is invalid")

    patch_path = candidate_dir / "candidate.patch"
    if not patch_path.is_file():
        raise CandidateError("candidate patch is missing")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(manifest["candidate_patch_sha256"])):
        raise CandidateError("candidate patch digest format is invalid")
    if not HEX_OID_RE.fullmatch(str(manifest["candidate_tree_oid"])):
        raise CandidateError("candidate tree identity format is invalid")
    actual_digest = f"sha256:{sha256_file(patch_path)}"
    if manifest["candidate_patch_sha256"] != actual_digest:
        raise CandidateError("candidate patch digest mismatch")
    if int(manifest["candidate_patch_bytes"]) != patch_path.stat().st_size:
        raise CandidateError("candidate patch byte length mismatch")

    patch = patch_path.read_bytes()
    if patch:
        run_git(repo, ["apply", "--index", "--binary", "--whitespace=nowarn", "--"], input_bytes=patch)
    tree_oid = git_text(repo, ["write-tree"])
    if tree_oid != manifest["candidate_tree_oid"]:
        raise CandidateError("restored candidate tree identity mismatch")

    print(json.dumps({
        "candidate_patch_sha256": actual_digest,
        "candidate_tree_oid": tree_oid,
        "restored": True,
    }, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    cap = sub.add_parser("capture", help="freeze a workspace into a Candidate")
    cap.add_argument("--repo", required=True)
    cap.add_argument("--output", required=True)
    cap.add_argument("--repository", required=True)
    cap.add_argument("--issue-number", required=True, type=int)
    cap.add_argument("--run-id", required=True)
    cap.add_argument("--run-attempt", required=True, type=int)
    cap.add_argument("--base-branch", required=True)
    cap.add_argument("--base-sha", required=True)
    cap.add_argument("--contract-fingerprint", required=True)
    cap.add_argument("--worker-outcome", required=True)
    cap.add_argument("--provider", default="")
    cap.add_argument("--model", default="")
    cap.add_argument("--created-at", default="")
    cap.add_argument("--max-patch-bytes", type=int, default=DEFAULT_MAX_PATCH_BYTES)
    cap.set_defaults(func=capture)

    res = sub.add_parser("restore", help="restore and verify a Candidate on its exact base")
    res.add_argument("--repo", required=True)
    res.add_argument("--candidate-dir", required=True)
    res.add_argument("--expected-repository", required=True)
    res.add_argument("--expected-issue-number", required=True, type=int)
    res.add_argument("--expected-base-sha", required=True)
    res.add_argument("--expected-contract-fingerprint", default="")
    res.set_defaults(func=restore)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except CandidateError as exc:
        print(f"candidate error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
