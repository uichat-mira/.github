#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("validation.py")
SPEC = importlib.util.spec_from_file_location("mira_validation", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class Args:
    pass


def init_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True)


def write_profile(root: Path, profiles: dict) -> Path:
    init_repo(root)
    path = root / "profiles.json"
    path.write_text(json.dumps({"schema_version": 1, "profiles": profiles}), encoding="utf-8")
    return path


def run_validation(root: Path, profile_file: Path, *, profile="feature", max_tier="L3", legacy_command="", restore_outcome="success"):
    if not (root / ".git").exists():
        init_repo(root)
    args = Args()
    args.repo = str(root)
    args.profile_file = str(profile_file)
    args.profile = profile
    args.max_tier = max_tier
    args.legacy_command = legacy_command
    args.restore_outcome = restore_outcome
    args.output = str(root / "report.json")
    args.log = str(root / "validation.log")
    rc = MODULE.run_validation(args)
    return rc, json.loads(Path(args.output).read_text())


class ValidationTests(unittest.TestCase):
    def test_profile_pass_respects_max_tier_without_running_l4(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            marker = root / "l4-ran"
            profile = write_profile(root, {
                "feature": {"checks": [
                    {"id": "unit", "tier": "L2", "requirement": "required", "command": "true"},
                    {"id": "package", "tier": "L4", "requirement": "optional", "command": f"touch {marker}"},
                ]}
            })
            _, report = run_validation(root, profile, max_tier="L2")
            self.assertEqual(report["result"], "PASS")
            self.assertFalse(marker.exists())
            self.assertEqual(next(x for x in report["checks"] if x["id"] == "package")["status"], "skipped")

    def test_fail_fast_stops_later_expensive_check(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            marker = root / "l4-ran"
            profile = write_profile(root, {
                "feature": {"checks": [
                    {"id": "unit", "tier": "L2", "requirement": "required", "command": "exit 2"},
                    {"id": "package", "tier": "L4", "requirement": "required", "command": f"touch {marker}"},
                ]}
            })
            _, report = run_validation(root, profile, max_tier="L4")
            self.assertEqual(report["result"], "REPAIR")
            self.assertFalse(marker.exists())
            package = next(x for x in report["checks"] if x["id"] == "package")
            self.assertEqual(package["status"], "skipped")
            self.assertIn("fail-fast", package["reason"])

    def test_required_check_above_ceiling_is_gap_not_upgrade(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            marker = root / "l4-ran"
            profile = write_profile(root, {
                "feature": {"checks": [
                    {"id": "unit", "tier": "L2", "requirement": "required", "command": "true"},
                    {"id": "package", "tier": "L4", "requirement": "required", "command": f"touch {marker}"},
                ]}
            })
            _, report = run_validation(root, profile, max_tier="L2")
            self.assertEqual(report["result"], "VALIDATION_GAP")
            self.assertFalse(marker.exists())
            self.assertEqual(report["gaps"][0]["kind"], "required_tier_above_dispatch_ceiling")

    def test_unknown_profile_is_explicit_gap(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            profile = write_profile(root, {"other": {"checks": []}})
            _, report = run_validation(root, profile, profile="missing")
            self.assertEqual(report["result"], "VALIDATION_GAP")
            self.assertEqual(report["profile_state"], "profile_missing")

    def test_unavailable_required_capability_is_gap(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            profile = write_profile(root, {
                "feature": {"checks": [
                    {"id": "missing", "tier": "L2", "requirement": "required", "command": "definitely-not-a-real-command-agt067"},
                ]}
            })
            _, report = run_validation(root, profile)
            self.assertEqual(report["result"], "VALIDATION_GAP")
            self.assertEqual(report["gaps"][0]["kind"], "capability_unavailable")

    def test_explicit_l4_runs_only_when_ceiling_allows_it(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            marker = root / "l4-ran"
            profile = write_profile(root, {
                "release-candidate": {"checks": [
                    {"id": "package", "tier": "L4", "requirement": "required", "command": f"touch {marker}"},
                ]}
            })
            _, report = run_validation(root, profile, profile="release-candidate", max_tier="L4")
            self.assertEqual(report["result"], "PASS")
            self.assertTrue(marker.exists())

    def test_legacy_command_keeps_exact_compatibility_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            marker = root / "legacy-ran"
            command = f"printf legacy > {marker}"
            _, report = run_validation(root, root / "missing.json", profile="", legacy_command=command)
            self.assertEqual(report["mode"], "legacy")
            self.assertEqual(report["result"], "PASS")
            self.assertEqual(marker.read_text(), "legacy")
            check = next(x for x in report["checks"] if x["id"] == "legacy_verification_command")
            self.assertEqual(check["command"], command)
            self.assertEqual(check["tier"], "legacy-unclassified")

    def test_invalid_profile_schema_becomes_gap(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            profile = write_profile(root, {
                "feature": {"checks": [
                    {"id": "bad", "tier": "L2", "requirement": "required"}
                ]}
            })
            _, report = run_validation(root, profile)
            self.assertEqual(report["result"], "VALIDATION_GAP")
            self.assertEqual(report["profile_state"], "profile_invalid")

    def test_restore_failure_is_blocked_and_runs_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            marker = root / "ran"
            profile = write_profile(root, {
                "feature": {"checks": [
                    {"id": "unit", "tier": "L2", "requirement": "required", "command": f"touch {marker}"}
                ]}
            })
            _, report = run_validation(root, profile, restore_outcome="failure")
            self.assertEqual(report["result"], "BLOCKED")
            self.assertFalse(marker.exists())
            self.assertEqual(report["failed_check"], "candidate_identity")


if __name__ == "__main__":
    unittest.main()
