#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
RECOVERY = HERE / "recovery.py"


def run(*args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(
        [sys.executable, str(RECOVERY), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if p.returncode != expect:
        raise AssertionError(
            f"expected rc={expect}, got {p.returncode}: {args}\nstdout={p.stdout}\nstderr={p.stderr}"
        )
    return p


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fingerprint(root: Path, issue, comments, name: str):
    issue_path = root / f"{name}-issue.json"
    comments_path = root / f"{name}-comments.json"
    out = root / f"{name}-contract.json"
    write(issue_path, issue)
    write(comments_path, comments)
    run(
        "fingerprint",
        "--issue-json", str(issue_path),
        "--comments-json", str(comments_path),
        "--output", str(out),
    )
    return json.loads(out.read_text())


def pointer_body(value) -> str:
    return (
        "<!-- mira-recovery-candidate:v1\n"
        + json.dumps(value, ensure_ascii=False, sort_keys=True)
        + "\n-->\n"
        + "Mira Worker recovery pointer."
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="mira-recovery-fixture-") as td:
        root = Path(td)
        issue = {"number": 59, "title": "  Recovery\r\n", "body": "Line 1  \r\nLine 2\r\n"}

        base_comments = [
            {
                "id": 10,
                "author": "maintainer",
                "created_at": "2026-11-17T00:00:00Z",
                "updated_at": "2026-11-17T00:00:00Z",
                "body": "Status: CI is green",
            },
            {
                "id": 11,
                "author": "maintainer",
                "created_at": "2026-11-17T00:01:00Z",
                "updated_at": "2026-11-17T00:01:00Z",
                "body": "<!-- mira-contract-amendment:v1 -->\nScope change: keep Recovery fail-closed.",
            },
        ]

        fp1 = fingerprint(root, issue, base_comments, "fp1")
        fp2 = fingerprint(
            root,
            {"number": 59, "title": "Recovery", "body": "Line 1\nLine 2"},
            base_comments,
            "fp2",
        )
        assert fp1["fingerprint"] == fp2["fingerprint"]
        assert fp1["ambiguity_guard"] == fp2["ambiguity_guard"]
        assert fp1["amendment_ids"] == [11]
        assert fp1["note_ids"] == [10]
        print("PASS fingerprint: normalization and status note stability")

        changed_amendment = [dict(x) for x in base_comments]
        changed_amendment[1] = dict(changed_amendment[1], body="Contract amendment: require exact base.")
        fp3 = fingerprint(root, issue, changed_amendment, "fp3")
        assert fp3["fingerprint"] != fp1["fingerprint"]
        print("PASS fingerprint: amendment changes contract")

        ambiguous = base_comments + [{
            "id": 12,
            "author": "maintainer",
            "created_at": "2026-11-17T00:02:00Z",
            "updated_at": "2026-11-17T00:02:00Z",
            "body": "这条以后按新的处理。",
        }]
        fp4 = fingerprint(root, issue, ambiguous, "fp4")
        assert fp4["fingerprint"] == fp1["fingerprint"]
        assert fp4["ambiguity_guard"] != fp1["ambiguity_guard"]
        assert fp4["ambiguous_comment_ids"] == [12]
        print("PASS fingerprint: ambiguous trusted comment trips guard")

        changed_issue = dict(issue, body="Line 1\nLine 2\nnew contract")
        fp5 = fingerprint(root, changed_issue, base_comments, "fp5")
        assert fp5["fingerprint"] != fp1["fingerprint"]
        print("PASS fingerprint: Issue body drift detected")

        pointer_old = {
            "schema_version": 1,
            "repository": "uichat-mira/.github",
            "issue_number": 59,
            "run_id": 100,
            "run_attempt": 1,
        }
        pointer_new = dict(pointer_old, run_id=101)
        all_comments = [
            {
                "id": 1,
                "created_at": "2026-11-17T00:00:00Z",
                "user": {"login": "someone", "type": "User"},
                "body": pointer_body(dict(pointer_new, run_id=999)),
            },
            {
                "id": 2,
                "created_at": "2026-11-17T00:01:00Z",
                "user": {"login": "github-actions[bot]", "type": "Bot"},
                "body": pointer_body(pointer_old),
            },
            {
                "id": 3,
                "created_at": "2026-11-17T00:02:00Z",
                "user": {"login": "github-actions[bot]", "type": "Bot"},
                "body": pointer_body(pointer_new),
            },
        ]
        comments_path = root / "all-comments.json"
        discovered_path = root / "discovered.json"
        write(comments_path, all_comments)
        run(
            "discover-pointer",
            "--comments-json", str(comments_path),
            "--repository", "uichat-mira/.github",
            "--issue-number", "59",
            "--output", str(discovered_path),
        )
        discovered = json.loads(discovered_path.read_text())
        assert discovered["found"] is True
        assert discovered["pointer"]["run_id"] == 101
        assert discovered["pointer_count"] == 2
        print("PASS pointer: latest GitHub Actions bot pointer wins")

        manifest = {
            "schema_version": 1,
            "repository": "uichat-mira/.github",
            "issue_number": 59,
            "base_sha": "a" * 40,
            "contract_fingerprint": fp1["fingerprint"],
            "candidate_patch_sha256": "sha256:" + "b" * 64,
            "candidate_tree_oid": "c" * 40,
        }
        pointer = {
            "schema_version": 1,
            "repository": "uichat-mira/.github",
            "issue_number": 59,
            "run_id": 101,
            "run_attempt": 1,
            "base_sha": manifest["base_sha"],
            "contract_fingerprint": fp1["fingerprint"],
            "ambiguity_guard": fp1["ambiguity_guard"],
            "candidate_patch_sha256": manifest["candidate_patch_sha256"],
            "candidate_tree_oid": manifest["candidate_tree_oid"],
        }
        manifest_path = root / "manifest.json"
        pointer_path = root / "pointer.json"
        contract_path = root / "current-contract.json"
        write(manifest_path, manifest)
        write(pointer_path, pointer)
        write(contract_path, fp1)

        recover_path = root / "recover.json"
        run(
            "decide",
            "--current-contract", str(contract_path),
            "--pointer", str(pointer_path),
            "--candidate-manifest", str(manifest_path),
            "--repository", "uichat-mira/.github",
            "--issue-number", "59",
            "--output", str(recover_path),
        )
        recover = json.loads(recover_path.read_text())
        assert recover["mode"] == "recoverable"
        assert recover["run_worker"] is True
        print("PASS decision: unverified Candidate is recoverable")

        verify_fail = {
            "terminal_status": "failure",
            "candidate_patch_sha256": manifest["candidate_patch_sha256"],
            "candidate_tree_oid": manifest["candidate_tree_oid"],
        }
        verify_fail_path = root / "verify-fail.json"
        write(verify_fail_path, verify_fail)
        fail_path = root / "recover-verify-fail.json"
        run(
            "decide",
            "--current-contract", str(contract_path),
            "--pointer", str(pointer_path),
            "--candidate-manifest", str(manifest_path),
            "--verify-run", str(verify_fail_path),
            "--repository", "uichat-mira/.github",
            "--issue-number", "59",
            "--output", str(fail_path),
        )
        assert json.loads(fail_path.read_text())["reason"] == "prior_verification_failed"
        print("PASS decision: verification failure remains recoverable")

        verify_ok = dict(verify_fail, terminal_status="success")
        verify_ok_path = root / "verify-ok.json"
        write(verify_ok_path, verify_ok)
        retry_path = root / "retry.json"
        run(
            "decide",
            "--current-contract", str(contract_path),
            "--pointer", str(pointer_path),
            "--candidate-manifest", str(manifest_path),
            "--verify-run", str(verify_ok_path),
            "--repository", "uichat-mira/.github",
            "--issue-number", "59",
            "--output", str(retry_path),
        )
        retry = json.loads(retry_path.read_text())
        assert retry["mode"] == "delivery_retry_only"
        assert retry["run_worker"] is False
        print("PASS decision: verified undelivered Candidate skips model")

        delivery_ok_path = root / "delivery-ok.json"
        write(delivery_ok_path, {"terminal_status": "success"})
        complete_path = root / "complete.json"
        run(
            "decide",
            "--current-contract", str(contract_path),
            "--pointer", str(pointer_path),
            "--candidate-manifest", str(manifest_path),
            "--verify-run", str(verify_ok_path),
            "--delivery-run", str(delivery_ok_path),
            "--repository", "uichat-mira/.github",
            "--issue-number", "59",
            "--output", str(complete_path),
        )
        assert json.loads(complete_path.read_text())["mode"] == "delivery_complete"
        print("PASS decision: already delivered Candidate does not rerun model")

        drift_contract_path = root / "drift-contract.json"
        write(drift_contract_path, fp3)
        drift_path = root / "drift.json"
        run(
            "decide",
            "--current-contract", str(drift_contract_path),
            "--pointer", str(pointer_path),
            "--candidate-manifest", str(manifest_path),
            "--repository", "uichat-mira/.github",
            "--issue-number", "59",
            "--output", str(drift_path),
        )
        drift = json.loads(drift_path.read_text())
        assert drift["mode"] == "contract_drift"
        assert drift["run_worker"] is True
        assert drift["reuse_candidate"] is False
        print("PASS decision: contract drift forbids silent reuse")

        tampered = dict(manifest, candidate_tree_oid="d" * 40)
        tampered_path = root / "tampered.json"
        write(tampered_path, tampered)
        bad_path = root / "bad.json"
        run(
            "decide",
            "--current-contract", str(contract_path),
            "--pointer", str(pointer_path),
            "--candidate-manifest", str(tampered_path),
            "--repository", "uichat-mira/.github",
            "--issue-number", "59",
            "--output", str(bad_path),
        )
        bad = json.loads(bad_path.read_text())
        assert bad["mode"] == "recovery_failed"
        assert bad["run_worker"] is False
        print("PASS decision: identity mismatch fails closed")

    print("AGT-059 recovery fixture suite: PASS")


if __name__ == "__main__":
    main()
