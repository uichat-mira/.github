#!/usr/bin/env python3
"""Idempotent GitHub branch and Draft PR delivery for a verified Mira Candidate."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


class DeliveryError(RuntimeError):
    pass


OID_RE = re.compile(r"^[0-9a-f]{40,64}$")


def command(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc


def require_success(proc: subprocess.CompletedProcess[str], label: str) -> str:
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise DeliveryError(f"{label} failed: {detail}")
    return proc.stdout.strip()


def git(repo: Path, *args: str) -> str:
    return require_success(command(["git", "-C", str(repo), *args]), f"git {' '.join(args)}")


def ensure_branch(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    if not OID_RE.fullmatch(args.base_sha) or not OID_RE.fullmatch(args.tree_oid):
        raise DeliveryError("base SHA and Candidate tree must be full Git object IDs")
    git(repo, "check-ref-format", "--branch", args.branch)
    if git(repo, "branch", "--show-current") != args.branch:
        raise DeliveryError("current local branch does not match the deterministic Candidate branch")
    if git(repo, "rev-parse", "HEAD") != args.base_sha:
        raise DeliveryError("Delivery checkout is not at the Candidate exact base")

    remote_ref = f"refs/remotes/{args.remote}/{args.branch}"
    lookup = command([
        "git", "-C", str(repo), "ls-remote", "--heads", "--exit-code",
        args.remote, f"refs/heads/{args.branch}",
    ])
    if lookup.returncode == 0:
        if not lookup.stdout.strip():
            raise DeliveryError("remote branch lookup returned success without a ref")
        git(repo, "fetch", "--no-tags", args.remote, f"refs/heads/{args.branch}:{remote_ref}")
        existing = git(repo, "rev-parse", f"{remote_ref}^{{commit}}")
        existing_tree = git(repo, "rev-parse", f"{existing}^{{tree}}")
        existing_parents = git(repo, "rev-list", "--parents", "-n", "1", existing).split()
        if (
            len(existing_parents) != 2
            or existing_parents[1] != args.base_sha
            or existing_tree != args.tree_oid
        ):
            raise DeliveryError("existing remote Candidate branch does not match exact single-parent base/tree identity")
        git(repo, "reset", "--hard", existing)
        result = {
            "commit_sha": existing,
            "commit_tree_oid": existing_tree,
            "reused_existing_branch": True,
            "branch": args.branch,
        }
        print(json.dumps(result, sort_keys=True))
        return 0

    if lookup.returncode != 2:
        raise DeliveryError(f"remote branch lookup failed: {lookup.stderr.strip() or lookup.returncode}")

    git(repo, "commit", "-m", args.commit_message)
    commit_sha = git(repo, "rev-parse", "HEAD")
    commit_tree = git(repo, "rev-parse", f"{commit_sha}^{{tree}}")
    commit_parent = git(repo, "rev-parse", f"{commit_sha}^")
    if commit_tree != args.tree_oid or commit_parent != args.base_sha:
        raise DeliveryError("new Delivery commit does not match exact Candidate base/tree identity")
    git(repo, "push", "--set-upstream", args.remote, f"HEAD:{args.branch}")
    print(json.dumps({
        "commit_sha": commit_sha,
        "commit_tree_oid": commit_tree,
        "reused_existing_branch": False,
        "branch": args.branch,
    }, sort_keys=True))
    return 0


def ensure_pr(args: argparse.Namespace) -> int:
    if not OID_RE.fullmatch(args.head_sha):
        raise DeliveryError("expected PR head SHA must be a full Git object ID")
    if not re.fullmatch(r"[A-Za-z0-9-]+", args.head_owner):
        raise DeliveryError("PR head owner is invalid")
    listed = command([
        "gh", "pr", "list",
        "--state", "all",
        "--head", f"{args.head_owner}:{args.branch}",
        "--json", "url,state,isDraft,headRefOid,baseRefName",
    ])
    raw = require_success(listed, "gh pr list")
    try:
        prs = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DeliveryError("gh pr list returned invalid JSON") from exc
    if not isinstance(prs, list):
        raise DeliveryError("gh pr list result must be an array")

    if len(prs) > 1:
        raise DeliveryError("multiple PRs already reference the deterministic Candidate branch")
    if prs:
        pr = prs[0]
        if (
            pr.get("state") != "OPEN"
            or pr.get("isDraft") is not True
            or pr.get("headRefOid") != args.head_sha
            or pr.get("baseRefName") != args.base
            or not pr.get("url")
        ):
            raise DeliveryError("existing PR is not the exact open Draft PR for this Candidate")
        print(json.dumps({"url": pr["url"], "reused_existing_pr": True}, sort_keys=True))
        return 0

    created = command([
        "gh", "pr", "create",
        "--draft",
        "--base", args.base,
        "--head", args.branch,
        "--title", args.title,
        "--body-file", args.body_file,
    ])
    url = require_success(created, "gh pr create")
    if not url.startswith("https://github.com/"):
        raise DeliveryError("gh pr create did not return a GitHub PR URL")
    print(json.dumps({"url": url, "reused_existing_pr": False}, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    branch = sub.add_parser("ensure-branch")
    branch.add_argument("--repo", required=True)
    branch.add_argument("--remote", default="origin")
    branch.add_argument("--branch", required=True)
    branch.add_argument("--base-sha", required=True)
    branch.add_argument("--tree-oid", required=True)
    branch.add_argument("--commit-message", required=True)
    branch.set_defaults(func=ensure_branch)

    pr = sub.add_parser("ensure-pr")
    pr.add_argument("--branch", required=True)
    pr.add_argument("--head-owner", required=True)
    pr.add_argument("--base", required=True)
    pr.add_argument("--head-sha", required=True)
    pr.add_argument("--title", required=True)
    pr.add_argument("--body-file", required=True)
    pr.set_defaults(func=ensure_pr)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except DeliveryError as exc:
        print(f"delivery error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
