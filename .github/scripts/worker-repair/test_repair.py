#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("repair.py")
SPEC = importlib.util.spec_from_file_location("mira_repair", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class Args:
    pass


def decision(result: str, rounds: int, precondition: str = "ok") -> dict:
    with tempfile.TemporaryDirectory() as td:
        output = Path(td) / "decision.json"
        args = Args()
        args.validation_result = result
        args.completed_rounds = rounds
        args.precondition = precondition
        args.output = str(output)
        MODULE.decide(args)
        return json.loads(output.read_text())


class RepairTests(unittest.TestCase):
    def test_first_repair_is_returned(self):
        d = decision("REPAIR", 0)
        self.assertEqual(d["state"], "RETURNED")
        self.assertTrue(d["run_worker"])
        self.assertEqual(d["next_repair_round"], 1)

    def test_second_repair_is_returned(self):
        d = decision("REPAIR", 1)
        self.assertEqual(d["state"], "RETURNED")
        self.assertTrue(d["run_worker"])
        self.assertEqual(d["next_repair_round"], 2)

    def test_third_repair_escalates_without_model(self):
        d = decision("REPAIR", 2)
        self.assertEqual(d["state"], "ESCALATED")
        self.assertFalse(d["run_worker"])
        self.assertEqual(d["next_repair_round"], 3)

    def test_non_repair_results_never_start_repair_worker(self):
        for result, state in [
            ("PASS", "VERIFIED"),
            ("BLOCKED", "BLOCKED"),
            ("VALIDATION_GAP", "BLOCKED"),
        ]:
            with self.subTest(result=result):
                d = decision(result, 0)
                self.assertEqual(d["state"], state)
                self.assertFalse(d["run_worker"])

    def test_contract_or_identity_precondition_fails_closed(self):
        for precondition in ("contract_drift", "identity_mismatch", "security", "permission", "corrupted_identity"):
            with self.subTest(precondition=precondition):
                d = decision("REPAIR", 0, precondition)
                self.assertEqual(d["state"], "BLOCKED")
                self.assertFalse(d["run_worker"])

    def test_context_is_structured_allowlist_and_binds_candidate_round(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            issue = {
                "number": 85,
                "title": "AGT-068",
                "body": "Return repairable Validation failures.",
                "private_reasoning": "must-not-survive",
            }
            contract = {
                "canonical_contract": {
                    "trusted_amendments": [{
                        "id": 7,
                        "author": "maintainer",
                        "created_at": "2026-11-18T00:00:00Z",
                        "updated_at": "2026-11-18T00:00:00Z",
                        "body": "Scope change: keep the repair bounded.",
                        "token": "must-not-survive",
                    }]
                }
            }
            candidate = {
                "schema_version": 1,
                "repository": "uichat-mira/demo",
                "issue_number": 85,
                "run_id": "100",
                "run_attempt": 1,
                "repair_round": 0,
                "base_branch": "dev",
                "base_sha": "a" * 40,
                "contract_fingerprint": "sha256:" + "1" * 64,
                "candidate_patch_sha256": "sha256:" + "2" * 64,
                "candidate_tree_oid": "b" * 40,
                "provider": "fixture",
                "model": "fixture-model",
                "worker_outcome": "success",
                "created_at": "2026-11-18T00:00:00Z",
                "secret": "must-not-survive",
            }
            validation = {
                "schema_version": 1,
                "result": "REPAIR",
                "profile": "feature",
                "max_tier": "L2",
                "profile_state": "available",
                "profile_sha256": "sha256:" + "3" * 64,
                "failed_check": "unit",
                "checks": [{
                    "id": "unit",
                    "tier": "L2",
                    "requirement": "required",
                    "status": "failed",
                    "duration_ms": 12,
                    "exit_code": 1,
                    "reason": None,
                    "failure_result": "REPAIR",
                    "raw_output": "must-not-survive",
                }],
                "gaps": [],
                "private_reasoning": "must-not-survive",
            }
            paths = {}
            for name, value in {
                "issue": issue,
                "contract": contract,
                "candidate": candidate,
                "validation": validation,
            }.items():
                path = root / f"{name}.json"
                path.write_text(json.dumps(value))
                paths[name] = path
            output = root / "context.json"
            args = Args()
            args.issue_json = str(paths["issue"])
            args.contract_json = str(paths["contract"])
            args.candidate_manifest = str(paths["candidate"])
            args.validation_report = str(paths["validation"])
            args.validation_artifact_name = "verify-artifact"
            args.repair_round = 1
            args.output = str(output)
            MODULE.context(args)
            raw = output.read_text()
            ctx = json.loads(raw)
            self.assertEqual(ctx["state"], "RETURNED")
            self.assertEqual(ctx["repair_round"], 1)
            self.assertEqual(ctx["candidate"]["repair_round"], 0)
            self.assertEqual(ctx["validation"]["failed_check"], "unit")
            self.assertFalse(ctx["worker_instruction"]["previous_worker_narrative_is_trusted_pass"])
            self.assertNotIn("must-not-survive", raw)

    def test_context_rejects_wrong_candidate_generation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            issue = {"number": 85, "title": "AGT-068", "body": "x"}
            candidate = {
                "schema_version": 1,
                "repository": "uichat-mira/demo",
                "issue_number": 85,
                "repair_round": 0,
            }
            validation = {"schema_version": 1, "result": "REPAIR", "checks": [], "gaps": []}
            contract = {"canonical_contract": {"trusted_amendments": []}}
            for name, value in {"issue": issue, "contract": contract, "candidate": candidate, "validation": validation}.items():
                (root / f"{name}.json").write_text(json.dumps(value))
            args = Args()
            args.issue_json = str(root / "issue.json")
            args.contract_json = str(root / "contract.json")
            args.candidate_manifest = str(root / "candidate.json")
            args.validation_report = str(root / "validation.json")
            args.validation_artifact_name = "verify-artifact"
            args.repair_round = 2
            args.output = str(root / "out.json")
            with self.assertRaises(MODULE.RepairError):
                MODULE.context(args)


if __name__ == "__main__":
    unittest.main()
