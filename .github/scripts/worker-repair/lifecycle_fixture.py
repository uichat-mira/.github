#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CANDIDATE = ROOT / "worker-candidate" / "candidate.py"
VALIDATION = ROOT / "worker-validation" / "validation.py"
REPAIR = HERE / "repair.py"
DELIVERY = ROOT / "worker-candidate" / "delivery.py"

REPOSITORY = "uichat-mira/repair-fixture"
ISSUE = 85
RUN_ID = "123"
RUN_ATTEMPT = "1"
FINGERPRINT = "sha256:" + "a" * 64


def run(args, *, cwd=None, env=None, expect=0):
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != expect:
        raise AssertionError(
            f"expected rc={expect}, got {proc.returncode}: {args}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


def git(repo: Path, *args: str) -> str:
    return run(["git", "-C", str(repo), *args]).stdout.strip()


def clone_main(bare: Path, target: Path) -> Path:
    run(["git", "clone", "-q", str(bare), str(target)])
    git(target, "checkout", "-q", "main")
    git(target, "config", "user.name", "Mira Repair Fixture")
    git(target, "config", "user.email", "fixture@example.invalid")
    return target


def capture(repo: Path, out: Path, base_sha: str, repair_round: int):
    run([
        sys.executable, str(CANDIDATE), "capture",
        "--repo", str(repo),
        "--output", str(out),
        "--repository", REPOSITORY,
        "--issue-number", str(ISSUE),
        "--run-id", RUN_ID,
        "--run-attempt", RUN_ATTEMPT,
        "--repair-round", str(repair_round),
        "--base-branch", "main",
        "--base-sha", base_sha,
        "--contract-fingerprint", FINGERPRINT,
        "--worker-outcome", "success",
        "--provider", "fixture",
        "--model", "fixture-model",
        "--created-at", "2026-11-18T00:00:00Z",
    ])
    return json.loads((out / "candidate.json").read_text())


def restore(repo: Path, candidate: Path, base_sha: str, repair_round: int):
    proc = run([
        sys.executable, str(CANDIDATE), "restore",
        "--repo", str(repo),
        "--candidate-dir", str(candidate),
        "--expected-repository", REPOSITORY,
        "--expected-issue-number", str(ISSUE),
        "--expected-repair-round", str(repair_round),
        "--expected-base-sha", base_sha,
        "--expected-contract-fingerprint", FINGERPRINT,
    ])
    return json.loads(proc.stdout)


def validate(repo: Path, profile: Path, root: Path, label: str):
    report = root / f"{label}-validation.json"
    log = root / f"{label}-validation.log"
    run([
        sys.executable, str(VALIDATION), "run",
        "--repo", str(repo),
        "--profile-file", str(profile),
        "--profile", "repair-fixture",
        "--max-tier", "L2",
        "--legacy-command", "",
        "--restore-outcome", "success",
        "--output", str(report),
        "--log", str(log),
    ])
    return json.loads(report.read_text()), report


def main():
    with tempfile.TemporaryDirectory(prefix="mira-return-loop-") as td:
        root = Path(td)
        bare = root / "remote.git"
        seed = root / "seed"
        run(["git", "init", "--bare", str(bare)])
        seed.mkdir()
        run(["git", "init", "-q", str(seed)])
        git(seed, "config", "user.name", "Mira Repair Fixture")
        git(seed, "config", "user.email", "fixture@example.invalid")
        (seed / "app.txt").write_text("base\n")
        git(seed, "add", "-A")
        git(seed, "commit", "-qm", "base")
        git(seed, "branch", "-M", "main")
        git(seed, "remote", "add", "origin", str(bare))
        git(seed, "push", "-q", "-u", "origin", "main")
        base_sha = git(seed, "rev-parse", "HEAD")

        profile = root / "profiles.json"
        profile.write_text(json.dumps({
            "schema_version": 1,
            "profiles": {
                "repair-fixture": {
                    "checks": [{
                        "id": "behavior",
                        "tier": "L2",
                        "requirement": "required",
                        "command": "grep -qx good app.txt",
                        "failure_result": "REPAIR",
                    }]
                }
            },
        }))

        # Initial Worker produces a bad-but-durable Candidate generation 0.
        work0 = clone_main(bare, root / "worker-0")
        (work0 / "app.txt").write_text("bad\n")
        candidate0 = root / "candidate-0"
        manifest0 = capture(work0, candidate0, base_sha, 0)
        assert manifest0["repair_round"] == 0

        verify0 = clone_main(bare, root / "verify-0")
        restore(verify0, candidate0, base_sha, 0)
        report0, report0_path = validate(verify0, profile, root, "round-0")
        assert report0["result"] == "REPAIR"
        assert report0["failed_check"] == "behavior"

        # Trusted repair context contains Issue + canonical amendments + Candidate + Validation,
        # not the previous model's narrative or raw log.
        issue = root / "issue.json"
        issue.write_text(json.dumps({
            "number": ISSUE,
            "title": "AGT-068 fixture",
            "body": "Repair the same Candidate until the behavior check passes.",
        }))
        contract = root / "contract.json"
        contract.write_text(json.dumps({
            "canonical_contract": {
                "trusted_amendments": [{
                    "id": 1,
                    "author": "maintainer",
                    "body": "Scope change: preserve correct work.",
                }]
            }
        }))
        context = root / "repair-context.json"
        run([
            sys.executable, str(REPAIR), "context",
            "--issue-json", str(issue),
            "--contract-json", str(contract),
            "--candidate-manifest", str(candidate0 / "candidate.json"),
            "--validation-report", str(report0_path),
            "--validation-artifact-name", "fixture-verify-round-0",
            "--repair-round", "1",
            "--output", str(context),
        ])
        repair_context = json.loads(context.read_text())
        assert repair_context["repair_round"] == 1
        assert repair_context["candidate"]["repair_round"] == 0
        assert repair_context["validation"]["result"] == "REPAIR"
        assert repair_context["validation"]["failed_check"] == "behavior"
        assert repair_context["worker_instruction"]["address_trusted_failure_first"] is True

        # Simulated Worker continuation restores Candidate #0 and changes only the rejected behavior.
        repair1 = clone_main(bare, root / "repair-1")
        restore(repair1, candidate0, base_sha, 0)
        assert (repair1 / "app.txt").read_text() == "bad\n"
        (repair1 / "app.txt").write_text("good\n")
        candidate1 = root / "candidate-1"
        manifest1 = capture(repair1, candidate1, base_sha, 1)
        assert manifest1["repair_round"] == 1
        assert manifest1["candidate_tree_oid"] != manifest0["candidate_tree_oid"]
        assert (candidate0 / "candidate.json").exists()
        assert (root / "round-0-validation.json").exists()

        # New generation is independently restored and validated on a clean checkout.
        verify1 = clone_main(bare, root / "verify-1")
        branch = "feat/worker-85-123-1"
        git(verify1, "switch", "-c", branch)
        restored1 = restore(verify1, candidate1, base_sha, 1)
        assert restored1["candidate_tree_oid"] == manifest1["candidate_tree_oid"]
        report1, _ = validate(verify1, profile, root, "round-1")
        assert report1["result"] == "PASS"
        assert git(verify1, "write-tree") == manifest1["candidate_tree_oid"]

        # Existing Delivery primitive accepts the repaired exact tree and produces the deterministic branch.
        delivery = json.loads(run([
            sys.executable, str(DELIVERY), "ensure-branch",
            "--repo", str(verify1),
            "--branch", branch,
            "--base-sha", base_sha,
            "--tree-oid", manifest1["candidate_tree_oid"],
            "--commit-message", "agent: implement issue #85 repair fixture",
        ]).stdout)
        assert delivery["commit_tree_oid"] == manifest1["candidate_tree_oid"]
        assert delivery["reused_existing_branch"] is False

        # Fake only the GitHub transport so the Draft-PR contract is exercised without repository mutation.
        bin_dir = root / "bin"
        bin_dir.mkdir()
        state_file = root / "pr-state.json"
        state_file.write_text("[]")
        gh = bin_dir / "gh"
        gh.write_text("""#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
state = os.environ["FIXTURE_PR_STATE"]
if args[:2] == ["pr", "list"]:
    print(open(state, encoding="utf-8").read())
elif args[:2] == ["pr", "create"]:
    url = "https://github.com/uichat-mira/repair-fixture/pull/1"
    open(state, "w", encoding="utf-8").write(json.dumps([{
        "url": url,
        "state": "OPEN",
        "isDraft": True,
        "headRefOid": os.environ["FIXTURE_HEAD_SHA"],
        "baseRefName": "main",
    }]))
    print(url)
else:
    raise SystemExit(2)
""")
        gh.chmod(0o755)
        body = root / "pr-body.md"
        body.write_text("repair fixture")
        env = dict(os.environ)
        env.update({
            "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
            "FIXTURE_PR_STATE": str(state_file),
            "FIXTURE_HEAD_SHA": delivery["commit_sha"],
        })
        pr = json.loads(run([
            sys.executable, str(DELIVERY), "ensure-pr",
            "--branch", branch,
            "--head-owner", "uichat-mira",
            "--base", "main",
            "--head-sha", delivery["commit_sha"],
            "--title", "agent: #85 repair fixture",
            "--body-file", str(body),
        ], env=env).stdout)
        assert pr["reused_existing_pr"] is False
        assert pr["url"].endswith("/pull/1")

        print("PASS Return-to-Worker: Candidate #0 -> REPAIR -> Candidate #1 -> PASS -> Draft PR contract")
        print("PASS traceability: rejected Candidate and Validation evidence remain present")
        print("AGT-068 bounded repair lifecycle fixture: PASS")


if __name__ == "__main__":
    main()
