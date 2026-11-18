#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("recovery.py")
SPEC = importlib.util.spec_from_file_location("mira_recovery", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class Args:
    pass


def fingerprint(*, profile="", max_tier="", validation_contract_sha256="", verification_command="pnpm check"):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        issue = root / "issue.json"
        comments = root / "comments.json"
        output = root / "contract.json"
        issue.write_text(json.dumps({"number": 84, "title": "AGT-067", "body": "contract"}))
        comments.write_text("[]")
        args = Args()
        args.issue_json = str(issue)
        args.comments_json = str(comments)
        args.base_branch = "dev"
        args.verification_command = verification_command
        args.validation_profile = profile
        args.validation_max_tier = max_tier
        args.validation_contract_sha256 = validation_contract_sha256
        args.output = str(output)
        MODULE.fingerprint(args)
        return json.loads(output.read_text())


class RecoveryValidationContractTests(unittest.TestCase):
    def test_legacy_fingerprint_keeps_v2_shape(self):
        result = fingerprint()
        self.assertEqual(result["fingerprint_version"], "mira-contract-v2")
        execution = result["canonical_contract"]["execution_contract"]
        self.assertEqual(set(execution), {"base_branch", "verification_command_sha256"})
        self.assertEqual(execution["base_branch"], "dev")

    def test_profile_mode_uses_validation_contract_not_legacy_command(self):
        a = fingerprint(
            profile="feature-fast",
            max_tier="L3",
            validation_contract_sha256="sha256:" + "1" * 64,
            verification_command="first legacy command",
        )
        b = fingerprint(
            profile="feature-fast",
            max_tier="L3",
            validation_contract_sha256="sha256:" + "1" * 64,
            verification_command="different legacy command",
        )
        self.assertEqual(a["fingerprint_version"], "mira-contract-v3-validation")
        self.assertEqual(a["fingerprint"], b["fingerprint"])
        execution = a["canonical_contract"]["execution_contract"]
        self.assertEqual(execution["validation_profile"], "feature-fast")
        self.assertEqual(execution["validation_max_tier"], "L3")
        self.assertNotIn("verification_command_sha256", execution)

    def test_profile_contract_change_invalidates_fingerprint(self):
        a = fingerprint(
            profile="feature-fast",
            max_tier="L3",
            validation_contract_sha256="sha256:" + "1" * 64,
        )
        b = fingerprint(
            profile="feature-fast",
            max_tier="L3",
            validation_contract_sha256="sha256:" + "2" * 64,
        )
        self.assertNotEqual(a["fingerprint"], b["fingerprint"])

    def test_max_tier_change_invalidates_fingerprint(self):
        a = fingerprint(
            profile="feature-fast",
            max_tier="L2",
            validation_contract_sha256="sha256:" + "1" * 64,
        )
        b = fingerprint(
            profile="feature-fast",
            max_tier="L3",
            validation_contract_sha256="sha256:" + "1" * 64,
        )
        self.assertNotEqual(a["fingerprint"], b["fingerprint"])


if __name__ == "__main__":
    unittest.main()
