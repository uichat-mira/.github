#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE / "candidate.py"
DELIVERY = HERE / "delivery.py"


def run(args, *, cwd=None, env=None, expect=0):
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != expect:
        raise AssertionError(
            f"expected rc={expect}, got {proc.returncode}: {args}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


def git(repo: Path, *args: str) -> str:
    return run(["git", "-C", str(repo), *args]).stdout.strip()


def make_candidate(root: Path, repo: Path, base_sha: str, out: Path):
    (repo / "candidate.txt").write_text("verified candidate\n", encoding="utf-8")
    run([
        sys.executable, str(CANDIDATE), "capture",
        "--repo", str(repo),
        "--output", str(out),
        "--repository", "uichat-mira/.github",
        "--issue-number", "73",
        "--run-id", "101",
        "--run-attempt", "1",
        "--base-branch", "main",
        "--base-sha", base_sha,
        "--contract-fingerprint", "sha256:" + "a" * 64,
        "--worker-outcome", "failure",
    ])
    git(repo, "reset", "--hard", base_sha)
    git(repo, "clean", "-fd")


def restore_and_deliver(repo: Path, branch: str, base_sha: str, tree_oid: str, candidate_dir: Path):
    git(repo, "switch", "-c", branch)
    run([
        sys.executable, str(CANDIDATE), "restore",
        "--repo", str(repo),
        "--candidate-dir", str(candidate_dir),
        "--expected-repository", "uichat-mira/.github",
        "--expected-issue-number", "73",
        "--expected-base-sha", base_sha,
        "--expected-contract-fingerprint", "sha256:" + "a" * 64,
    ])
    proc = run([
        sys.executable, str(DELIVERY), "ensure-branch",
        "--repo", str(repo),
        "--branch", branch,
        "--base-sha", base_sha,
        "--tree-oid", tree_oid,
        "--commit-message", "agent: implement issue #73",
    ])
    return json.loads(proc.stdout)


def main():
    with tempfile.TemporaryDirectory(prefix="mira-delivery-idempotency-") as td:
        root = Path(td)
        bare = root / "remote.git"
        seed = root / "seed"
        repo_a = root / "run-a"
        repo_b = root / "run-b"
        candidate_dir = root / "candidate"
        bare.mkdir()
        run(["git", "init", "--bare", str(bare)])
        seed.mkdir()
        run(["git", "init", str(seed)])
        git(seed, "config", "user.name", "Mira Delivery Fixture")
        git(seed, "config", "user.email", "fixture@example.invalid")
        (seed / "base.txt").write_text("base\n", encoding="utf-8")
        git(seed, "add", "-A")
        git(seed, "commit", "-m", "fixture base")
        git(seed, "branch", "-M", "main")
        git(seed, "remote", "add", "origin", str(bare))
        git(seed, "push", "-u", "origin", "main")
        base_sha = git(seed, "rev-parse", "HEAD")

        run(["git", "clone", str(bare), str(repo_a)])
        git(repo_a, "checkout", "main")
        git(repo_a, "config", "user.name", "Mira Delivery Fixture")
        git(repo_a, "config", "user.email", "fixture@example.invalid")
        make_candidate(root, repo_a, base_sha, candidate_dir)
        manifest = json.loads((candidate_dir / "candidate.json").read_text())
        tree_oid = manifest["candidate_tree_oid"]
        branch = "feat/worker-73-101-1"

        first = restore_and_deliver(repo_a, branch, base_sha, tree_oid, candidate_dir)
        assert first["reused_existing_branch"] is False
        first_commit = first["commit_sha"]
        assert first["commit_tree_oid"] == tree_oid
        print("PASS Delivery: first attempt creates and pushes deterministic Candidate branch")

        # A later run restores the same Candidate in a clean checkout. It must reuse,
        # not replace, the branch already pushed by the first partially completed run.
        run(["git", "clone", str(bare), str(repo_b)])
        git(repo_b, "checkout", "main")
        git(repo_b, "config", "user.name", "Mira Delivery Fixture")
        git(repo_b, "config", "user.email", "fixture@example.invalid")
        second = restore_and_deliver(repo_b, branch, base_sha, tree_oid, candidate_dir)
        assert second["reused_existing_branch"] is True
        assert second["commit_sha"] == first_commit
        print("PASS Delivery: retry reuses the exact existing branch commit")

        # Fake gh records PR creation and returns the same PR on a later retry.
        bin_dir = root / "bin"
        bin_dir.mkdir()
        state_file = root / "pr-state.json"
        count_file = root / "pr-create-count.txt"
        state_file.write_text("[]", encoding="utf-8")
        count_file.write_text("0", encoding="utf-8")
        gh = bin_dir / "gh"
        gh.write_text("""#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
state_path = os.environ["FIXTURE_PR_STATE"]
count_path = os.environ["FIXTURE_PR_COUNT"]
if args[:2] == ["pr", "list"]:
    print(open(state_path, encoding="utf-8").read())
elif args[:2] == ["pr", "create"]:
    count = int(open(count_path, encoding="utf-8").read()) + 1
    open(count_path, "w", encoding="utf-8").write(str(count))
    url = "https://github.com/uichat-mira/.github/pull/900"
    state = [{
        "url": url,
        "state": "OPEN",
        "isDraft": True,
        "headRefOid": os.environ["FIXTURE_HEAD_SHA"],
        "baseRefName": os.environ["FIXTURE_BASE_BRANCH"],
    }]
    open(state_path, "w", encoding="utf-8").write(json.dumps(state))
    print(url)
else:
    print("unsupported gh fixture command", file=sys.stderr)
    raise SystemExit(2)
""", encoding="utf-8")
        gh.chmod(0o755)
        body_file = root / "pr-body.md"
        body_file.write_text("fixture", encoding="utf-8")
        env = dict(os.environ)
        env.update({
            "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
            "FIXTURE_PR_STATE": str(state_file),
            "FIXTURE_PR_COUNT": str(count_file),
            "FIXTURE_HEAD_SHA": first_commit,
            "FIXTURE_BASE_BRANCH": "main",
        })
        first_pr = run([
            sys.executable, str(DELIVERY), "ensure-pr",
            "--branch", branch,
            "--base", "main",
            "--head-sha", first_commit,
            "--title", "agent: #73 fixture",
            "--body-file", str(body_file),
        ], env=env)
        assert json.loads(first_pr.stdout)["reused_existing_pr"] is False

        second_pr = run([
            sys.executable, str(DELIVERY), "ensure-pr",
            "--branch", branch,
            "--base", "main",
            "--head-sha", first_commit,
            "--title", "agent: #73 fixture",
            "--body-file", str(body_file),
        ], env=env)
        second_result = json.loads(second_pr.stdout)
        assert second_result["reused_existing_pr"] is True
        assert second_result["url"] == json.loads(first_pr.stdout)["url"]
        assert count_file.read_text() == "1"
        print("PASS Delivery: retry reuses existing Draft PR without duplicate creation")

        # A branch with the right name but a different tree must never be overwritten.
        bad_state = [{
            "url": "https://github.com/uichat-mira/.github/pull/901",
            "state": "OPEN",
            "isDraft": True,
            "headRefOid": "f" * 40,
            "baseRefName": "main",
        }]
        state_file.write_text(json.dumps(bad_state), encoding="utf-8")
        bad = run([
            sys.executable, str(DELIVERY), "ensure-pr",
            "--branch", branch,
            "--base", "main",
            "--head-sha", first_commit,
            "--title", "agent: #73 fixture",
            "--body-file", str(body_file),
        ], env=env, expect=2)
        assert "existing PR is not the exact open Draft PR" in bad.stderr
        print("PASS Delivery: mismatched existing PR fails closed")

    print("AGT-059 Delivery idempotency fixture suite: PASS")


if __name__ == "__main__":
    main()
