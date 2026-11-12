#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE / "candidate.py"
FINGERPRINT = "sha256:" + hashlib.sha256(b"AGT-056 fixture contract").hexdigest()
REPOSITORY = "uichat-mira/.github-fixture"
ISSUE = 56


def run(cmd, *, cwd=None, expect=0):
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != expect:
        raise AssertionError(
            f"command returned {p.returncode}, expected {expect}: {cmd}\n"
            f"stdout={p.stdout}\nstderr={p.stderr}"
        )
    return p


def git(repo, *args):
    return run(["git", *args], cwd=repo).stdout.strip()


def init_repo(root: Path) -> tuple[Path, str]:
    repo = root / "source"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Mira Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "tracked.txt").write_text("base\n")
    (repo / "rename-me.txt").write_text("rename payload\n")
    (repo / "delete-me.txt").write_text("delete me\n")
    (repo / "mode.sh").write_text("#!/bin/sh\necho base\n")
    (repo / "binary.bin").write_bytes(b"\x00base\x01")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    return repo, git(repo, "rev-parse", "HEAD")


def capture(repo: Path, out: Path, base: str, *, max_bytes=None, expect=0):
    cmd = [
        sys.executable, str(CANDIDATE), "capture",
        "--repo", str(repo),
        "--output", str(out),
        "--repository", REPOSITORY,
        "--issue-number", str(ISSUE),
        "--run-id", "fixture-run",
        "--run-attempt", "1",
        "--base-branch", "main",
        "--base-sha", base,
        "--contract-fingerprint", FINGERPRINT,
        "--worker-outcome", "failure",
        "--provider", "fixture",
        "--model", "fixture-model",
        "--created-at", "2026-11-12T00:00:00Z",
    ]
    if max_bytes is not None:
        cmd += ["--max-patch-bytes", str(max_bytes)]
    return run(cmd, expect=expect)


def clone_at(root: Path, source: Path, base: str, name="restore") -> Path:
    target = root / name
    run(["git", "clone", "-q", str(source), str(target)])
    git(target, "checkout", "-q", base)
    return target


def restore(repo: Path, cand: Path, base: str, *, expect=0):
    return run([
        sys.executable, str(CANDIDATE), "restore",
        "--repo", str(repo),
        "--candidate-dir", str(cand),
        "--expected-repository", REPOSITORY,
        "--expected-issue-number", str(ISSUE),
        "--expected-base-sha", base,
        "--expected-contract-fingerprint", FINGERPRINT,
    ], expect=expect)


def assert_round_trip(name, mutate, verify=None):
    with tempfile.TemporaryDirectory(prefix=f"mira-{name}-") as td:
        root = Path(td)
        repo, base = init_repo(root)
        mutate(repo)
        staged_before = git(repo, "diff", "--cached", "--name-status")
        cand = root / "candidate"
        capture(repo, cand, base)
        staged_after = git(repo, "diff", "--cached", "--name-status")
        assert staged_before == staged_after, "capture polluted the caller Git index"
        restored = clone_at(root, repo, base)
        restore(restored, cand, base)
        manifest = json.loads((cand / "candidate.json").read_text())
        tree = git(restored, "write-tree")
        assert tree == manifest["candidate_tree_oid"]
        if verify:
            verify(restored, cand)
        print(f"PASS round-trip: {name}")


def verify_rename(_repo: Path, candidate_dir: Path):
    patch = (candidate_dir / "candidate.patch").read_bytes()
    assert b"rename from rename-me.txt" in patch, "rename metadata missing"


def main():
    assert_round_trip("tracked-modify", lambda r: (r / "tracked.txt").write_text("changed\n"))
    assert_round_trip("untracked-add", lambda r: (r / "new.txt").write_text("new\n"))
    assert_round_trip("delete", lambda r: (r / "delete-me.txt").unlink())
    assert_round_trip(
        "rename",
        lambda r: (r / "rename-me.txt").rename(r / "renamed.txt"),
        verify_rename,
    )
    assert_round_trip("binary", lambda r: (r / "binary.bin").write_bytes(b"\x00changed\xff\x10"))
    assert_round_trip(
        "executable-bit",
        lambda r: os.chmod(r / "mode.sh", (r / "mode.sh").stat().st_mode | stat.S_IXUSR),
    )
    assert_round_trip("symlink", lambda r: os.symlink("tracked.txt", r / "tracked-link"))
    assert_round_trip("empty-change", lambda _r: None)

    with tempfile.TemporaryDirectory(prefix="mira-negative-") as td:
        root = Path(td)
        repo, base = init_repo(root)
        (repo / "tracked.txt").write_text("candidate\n")
        cand = root / "candidate"
        capture(repo, cand, base)

        tampered = root / "tampered"
        shutil.copytree(cand, tampered)
        with (tampered / "candidate.patch").open("ab") as f:
            f.write(b"\n# tampered\n")
        restored = clone_at(root, repo, base, "restore-digest")
        p = restore(restored, tampered, base, expect=2)
        assert "digest mismatch" in p.stderr
        print("PASS negative: patch digest mismatch")

        wrong = clone_at(root, repo, base, "restore-wrong-base")
        (wrong / "other.txt").write_text("other\n")
        git(wrong, "add", "-A")
        git(
            wrong,
            "-c", "user.name=Mira Fixture",
            "-c", "user.email=fixture@example.invalid",
            "commit", "-qm", "other",
        )
        p = restore(wrong, cand, base, expect=2)
        assert "HEAD is not" in p.stderr
        print("PASS negative: wrong base")

        bad_tree = root / "bad-tree"
        shutil.copytree(cand, bad_tree)
        manifest_path = bad_tree / "candidate.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["candidate_tree_oid"] = "0" * len(manifest["candidate_tree_oid"])
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        restored = clone_at(root, repo, base, "restore-tree")
        p = restore(restored, bad_tree, base, expect=2)
        assert "tree identity mismatch" in p.stderr
        print("PASS negative: tree identity mismatch")

    with tempfile.TemporaryDirectory(prefix="mira-sensitive-") as td:
        root = Path(td)
        repo, base = init_repo(root)
        (repo / ".env").write_text("API" + "_KEY=" + "fixture-secret-value\n")
        p = capture(repo, root / "candidate", base, expect=2)
        assert "sensitive-path policy" in p.stderr
        print("PASS negative: sensitive path rejected")

    with tempfile.TemporaryDirectory(prefix="mira-size-") as td:
        root = Path(td)
        repo, base = init_repo(root)
        (repo / "large.txt").write_text("x" * 4096)
        p = capture(repo, root / "candidate", base, max_bytes=64, expect=2)
        assert "exceeds trusted size limit" in p.stderr
        print("PASS negative: oversized candidate rejected")

    with tempfile.TemporaryDirectory(prefix="mira-secret-content-") as td:
        root = Path(td)
        repo, base = init_repo(root)
        (repo / "config.txt").write_text(
            "-----BEGIN " + "PRIVATE KEY-----\n"
            "fixture-material\n"
            "-----END " + "PRIVATE KEY-----\n"
        )
        p = capture(repo, root / "candidate", base, expect=2)
        assert "secret-like content" in p.stderr or "secret-content policy" in p.stderr
        print("PASS negative: obvious secret content rejected")

    print("AGT-056 fixture suite: PASS")


if __name__ == "__main__":
    main()
