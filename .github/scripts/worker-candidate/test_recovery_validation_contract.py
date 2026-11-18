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


def recovery_decision(
    validation_result="REPAIR",
    *,
    include_result=True,
    repair_round=0,
    lifecycle_state=None,
    contract_matches=True,
):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fingerprint_value = "sha256:" + "1" * 64
        guard_value = "sha256:" + "2" * 64
        patch_value = "sha256:" + "3" * 64
        tree_value = "b" * 40
        base_value = "a" * 40
        manifest = {
            "schema_version": 1,
            "repository": "uichat-mira/demo",
            "issue_number": 84,
            "run_id": "100",
            "run_attempt": 1,
            "repair_round": repair_round,
            "base_branch": "dev",
            "base_sha": base_value,
            "contract_fingerprint": fingerprint_value,
            "candidate_patch_sha256": patch_value,
            "candidate_tree_oid": tree_value,
        }
        pointer = {
            "schema_version": 1,
            "repository": "uichat-mira/demo",
            "issue_number": 84,
            "run_id": 100,
            "run_attempt": 1,
            "candidate_origin_run_id": 100,
            "candidate_origin_run_attempt": 1,
            "candidate_origin_repair_round": repair_round,
            "base_branch": "dev",
            "base_sha": base_value,
            "worker_branch": "feat/worker-84-100-1",
            "candidate_patch_sha256": patch_value,
            "candidate_tree_oid": tree_value,
            "contract_fingerprint": fingerprint_value,
            "ambiguity_guard": guard_value,
            "verification_state": "failure",
            "delivery_state": "skipped",
        }
        if lifecycle_state is not None:
            pointer["lifecycle_state"] = lifecycle_state
        verify = {
            "schema_version": 2,
            "job_role": "verify",
            "repository": "uichat-mira/demo",
            "run_id": "100",
            "run_attempt": "1",
            "repair_round": repair_round,
            "base_sha": base_value,
            "candidate_patch_sha256": patch_value,
            "candidate_tree_oid": tree_value,
            "contract_fingerprint": fingerprint_value,
            "terminal_status": "failure",
        }
        if include_result:
            verify["validation_result"] = validation_result
        contract = {
            "fingerprint": fingerprint_value if contract_matches else "sha256:" + "9" * 64,
            "ambiguity_guard": guard_value,
        }

        paths = {}
        for name, value in {
            "contract": contract,
            "pointer": pointer,
            "manifest": manifest,
            "verify": verify,
        }.items():
            path = root / f"{name}.json"
            path.write_text(json.dumps(value))
            paths[name] = path

        output = root / "decision.json"
        args = Args()
        args.current_contract = str(paths["contract"])
        args.pointer = str(paths["pointer"])
        args.candidate_manifest = str(paths["manifest"])
        args.verify_run = str(paths["verify"])
        args.delivery_run = None
        args.repository = "uichat-mira/demo"
        args.issue_number = 84
        args.output = str(output)
        MODULE.decide(args)
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


    def test_repair_validation_remains_recoverable(self):
        result = recovery_decision("REPAIR")
        self.assertEqual(result["mode"], "recoverable")
        self.assertTrue(result["run_worker"])
        self.assertTrue(result["reuse_candidate"])
        self.assertEqual(result["reason"], "prior_validation_repair")

    def test_blocked_validation_does_not_redispatch_worker(self):
        result = recovery_decision("BLOCKED")
        self.assertEqual(result["mode"], "recovery_failed")
        self.assertFalse(result["run_worker"])
        self.assertEqual(result["validation_result"], "BLOCKED")

    def test_validation_gap_does_not_redispatch_worker(self):
        result = recovery_decision("VALIDATION_GAP")
        self.assertEqual(result["mode"], "recovery_failed")
        self.assertFalse(result["run_worker"])
        self.assertEqual(result["validation_result"], "VALIDATION_GAP")

    def test_legacy_verify_failure_preserves_historical_recovery(self):
        result = recovery_decision(include_result=False)
        self.assertEqual(result["mode"], "recoverable")
        self.assertTrue(result["run_worker"])
        self.assertEqual(result["reason"], "prior_verification_failed")


    def test_second_repair_failure_escalates_across_runs(self):
        result = recovery_decision("REPAIR", repair_round=2)
        self.assertEqual(result["mode"], "escalated")
        self.assertFalse(result["run_worker"])
        self.assertFalse(result["reuse_candidate"])
        self.assertEqual(result["repair_round"], 2)

    def test_blocked_lifecycle_state_cannot_be_revived_by_old_repair_evidence(self):
        result = recovery_decision("REPAIR", repair_round=1, lifecycle_state="BLOCKED")
        self.assertEqual(result["mode"], "recovery_failed")
        self.assertFalse(result["run_worker"])
        self.assertEqual(result["reason"], "prior_lifecycle_blocked_requires_maintainer_review")

    def test_escalated_lifecycle_state_cannot_be_revived_by_new_dispatch(self):
        result = recovery_decision("REPAIR", repair_round=2, lifecycle_state="ESCALATED")
        self.assertEqual(result["mode"], "escalated")
        self.assertFalse(result["run_worker"])
        self.assertEqual(result["reason"], "prior_lifecycle_escalated_to_maintainer")

    def test_contract_drift_stops_for_maintainer_instead_of_restarting_worker(self):
        result = recovery_decision("REPAIR", contract_matches=False)
        self.assertEqual(result["mode"], "contract_drift")
        self.assertFalse(result["run_worker"])
        self.assertFalse(result["reuse_candidate"])

    def test_verify_evidence_repair_round_must_match_candidate_generation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = {
                "run_id": "100",
                "run_attempt": 1,
                "repair_round": 2,
                "base_sha": "a" * 40,
                "candidate_patch_sha256": "sha256:" + "3" * 64,
                "candidate_tree_oid": "b" * 40,
                "contract_fingerprint": "sha256:" + "1" * 64,
            }
            verify = {
                "job_role": "verify",
                "repository": "uichat-mira/demo",
                "run_id": "100",
                "run_attempt": "1",
                "repair_round": 1,
                "base_sha": manifest["base_sha"],
                "candidate_patch_sha256": manifest["candidate_patch_sha256"],
                "candidate_tree_oid": manifest["candidate_tree_oid"],
                "contract_fingerprint": manifest["contract_fingerprint"],
                "terminal_status": "failure",
                "validation_result": "REPAIR",
            }
            with self.assertRaises(MODULE.RecoveryError):
                MODULE.validate_verify_evidence(
                    verify,
                    repository="uichat-mira/demo",
                    manifest=manifest,
                )


if __name__ == "__main__":
    unittest.main()
