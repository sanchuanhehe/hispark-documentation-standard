from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_contracts import ContractError, STAGES, load, validate_gate, validate_matrix, validate_tutorial

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples/contracts"


class GateTests(unittest.TestCase):
    def setUp(self):
        self.plan = load(EXAMPLES / "gate-plan.example.json")
        self.debt = load(EXAMPLES / "gate-report.example.json")
        self.clean = deepcopy(self.debt)
        self.clean["findings"] = []
        self.clean["summary"] = {"counts": {"known": 0, "new": 0, "resolved": 0},
                                 "by_rule": {}, "current": 0, "baseline_new": 0}

    def test_complete_zero_finding_report_passes(self):
        self.assertEqual(validate_gate(self.plan, self.clean)["result"], "passed")

    def test_baseline_new_zero_does_not_waive_known(self):
        with self.assertRaisesRegex(ContractError, "current findings"):
            validate_gate(self.plan, self.debt)

    def test_new_finding_blocks(self):
        self.debt["findings"][0]["classification"] = "new"
        self.debt["summary"] = {"counts": {"known": 0, "new": 1, "resolved": 0},
                                "by_rule": {"DOC-LINK": {"known": 0, "new": 1, "resolved": 0}},
                                "current": 1, "baseline_new": 1}
        with self.assertRaisesRegex(ContractError, "current findings"):
            validate_gate(self.plan, self.debt)

    def test_resolved_is_not_current(self):
        self.debt["findings"][0]["classification"] = "resolved"
        self.debt["summary"] = {"counts": {"known": 0, "new": 0, "resolved": 1},
                                "by_rule": {"DOC-LINK": {"known": 0, "new": 0, "resolved": 1}},
                                "current": 0, "baseline_new": 0}
        self.assertEqual(validate_gate(self.plan, self.debt)["result"], "passed")

    def test_all_unsuccessful_required_states_block(self):
        for status in ("failed", "blocked", "not_run", "not_applicable", "cancelled", "skipped", "timeout"):
            with self.subTest(status=status), self.assertRaises(ContractError):
                report = deepcopy(self.clean)
                report["checks"][0]["status"] = status
                validate_gate(self.plan, report)

    def test_missing_duplicate_or_empty_required_checks_block(self):
        for checks in ([], self.clean["checks"][:1], self.clean["checks"] * 2):
            with self.subTest(checks=checks), self.assertRaises(ContractError):
                validate_gate(self.plan, {**self.clean, "checks": checks})
        with self.assertRaises(ContractError):
            validate_gate({**self.plan, "required_checks": []}, self.clean)

    def test_no_self_reported_exception_bypass(self):
        self.debt["exceptions"] = [{"approved": True}]
        with self.assertRaises(ContractError):
            validate_gate(self.plan, self.debt)

    def test_stale_report_identity_blocks(self):
        for field in ("commit", "run_id", "scope"):
            with self.subTest(field=field), self.assertRaises(ContractError):
                validate_gate(self.plan, {**self.clean, field: "other"})

    def test_missing_report_contract_fields_block(self):
        for field in ("complete", "schema_version", "boundary", "archive", "findings", "summary"):
            report = deepcopy(self.clean)
            del report[field]
            with self.subTest(field=field), self.assertRaises(ContractError):
                validate_gate(self.plan, report)

    def test_missing_or_failed_archive_blocks(self):
        for archive in ({}, {"uploaded": False}, {"uploaded": True, "uri": "x"}):
            with self.subTest(archive=archive), self.assertRaises(ContractError):
                validate_gate(self.plan, {**self.clean, "archive": archive})

    def test_real_exit_status_and_evidence_required(self):
        for field, value in (("exit_code", 1), ("exit_code", None), ("exit_code", False),
                             ("evidence", []), ("evidence", [""])):
            report = deepcopy(self.clean)
            report["checks"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ContractError):
                validate_gate(self.plan, report)

    def test_truncated_report_and_summary_mismatch_block(self):
        for field, value in (("counts", {}), ("by_rule", {}), ("current", 0), ("baseline_new", 1)):
            report = deepcopy(self.debt)
            report["summary"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ContractError, "mismatch"):
                validate_gate(self.plan, report)
        report = deepcopy(self.debt)
        report["findings"] = []
        with self.assertRaisesRegex(ContractError, "mismatch"):
            validate_gate(self.plan, report)

    def test_finding_fields_and_classification_required(self):
        for field in ("id", "rule_id", "path", "location", "message", "classification"):
            report = deepcopy(self.debt)
            del report["findings"][0][field]
            with self.subTest(field=field), self.assertRaises(ContractError):
                validate_gate(self.plan, report)

    def test_duplicate_finding_identity_rejected(self):
        self.debt["findings"] *= 2
        with self.assertRaisesRegex(ContractError, "duplicate finding"):
            validate_gate(self.plan, self.debt)

    def test_cli_known_fixture_returns_nonzero(self):
        process = subprocess.run([sys.executable, str(ROOT / "scripts/validate_contracts.py"),
                                  "gate", str(EXAMPLES / "gate-plan.example.json"),
                                  str(EXAMPLES / "gate-report.example.json")],
                                 capture_output=True, text=True)
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads(process.stdout)["result"], "failed")


class TutorialTests(unittest.TestCase):
    def setUp(self):
        self.contract = load(EXAMPLES / "tutorial.example.json")

    def test_repeated_linked_selector_counts_once(self):
        self.assertEqual(validate_tutorial(self.contract)["decisions"], 1)

    def test_selector_order_semantics_and_sync_drift_rejected(self):
        for key in ("labels", "semantics", "sync_group"):
            contract = deepcopy(self.contract)
            value = contract["selections"][1][key]
            contract["selections"][1][key] = value[::-1]
            with self.subTest(key=key), self.assertRaises(ContractError):
                validate_tutorial(contract)

    def test_independent_decision_count_not_widget_count(self):
        self.contract["measured"]["decisions"] = 2
        self.contract["budget"]["decisions"] = 2
        with self.assertRaisesRegex(ContractError, "decision count"):
            validate_tutorial(self.contract)

    def test_missing_or_nonpositive_time_budget_rejected(self):
        for duration in (None, "暂不承诺完成时间", 0, -1, True, float("nan"), float("inf")):
            self.contract["budget"]["target_minutes"] = duration
            with self.subTest(duration=duration), self.assertRaises(ContractError):
                validate_tutorial(self.contract)

    def test_each_leaf_budget_is_enforced(self):
        for field in ("pages", "steps", "prerequisites", "decisions", "optional_branches"):
            contract = deepcopy(self.contract)
            contract["measured"][field] = contract["budget"][field] + 1
            with self.subTest(field=field), self.assertRaises(ContractError):
                validate_tutorial(contract)

    def test_optional_branch_budget_cannot_be_raised(self):
        self.contract["budget"]["optional_branches"] = 1
        with self.assertRaises(ContractError):
            validate_tutorial(self.contract)

    def test_missing_budget_approval_or_preparation_boundary_rejected(self):
        for field in ("budget", "approval", "user_test_evidence", "timing_boundary", "includes_required_preparation"):
            contract = deepcopy(self.contract)
            del contract[field]
            with self.subTest(field=field), self.assertRaises(ContractError):
                validate_tutorial(contract)


class MatrixTests(unittest.TestCase):
    def setUp(self):
        self.matrix = {
            "scenario_id": "synthetic", "page": "synthetic-page@revision", "facts_revision": "synthetic",
            "scope": "synthetic-server-build", "boundary": "No GUI/USB/flash/hardware evidence",
            "environment": dict.fromkeys(("os", "runner", "architecture", "sdk", "tools"), "synthetic"),
            "stages": [dict(stage=name, status="not_run", required=False, criterion="synthetic",
                            reason="not executed", followup="synthetic owner/plan/date", boundary="not proven")
                       for name in sorted(STAGES)]}
        self.build = next(s for s in self.matrix["stages"] if s["stage"] == "build")
        self.build.update(status="passed", required=True, started_at="2026-01-01T00:00:00Z",
                          ended_at="2026-01-01T00:01:00Z", working_directory="synthetic",
                          command="synthetic-command", log="synthetic.log", exit_code=0,
                          config_changes=[], artifacts=[{"path": "synthetic.bin", "size_bytes": 1,
                                                         "sha256": "a" * 64}])

    def test_build_does_not_promote_flash_or_hil(self):
        result = validate_matrix(self.matrix)
        self.assertEqual(result["stages"]["build"], "passed")
        self.assertEqual(result["stages"]["flash"], "not_run")
        self.assertEqual(result["stages"]["HIL"], "not_run")

    def test_all_eight_distinct_stages_required(self):
        self.matrix["stages"][-1] = self.matrix["stages"][0]
        with self.assertRaises(ContractError):
            validate_matrix(self.matrix)

    def test_required_cannot_be_not_applicable_or_unrun(self):
        for status in ("not_applicable", "not_run", "blocked", "failed"):
            self.build["status"] = status
            with self.subTest(status=status), self.assertRaises(ContractError):
                validate_matrix(self.matrix)

    def test_verification_level_is_not_execution_status(self):
        self.build["status"] = "smoke"
        with self.assertRaises(ContractError):
            validate_matrix(self.matrix)

    def test_missing_execution_context_and_artifact_hash_rejected(self):
        for field in ("started_at", "ended_at", "working_directory", "command", "exit_code", "log", "config_changes", "artifacts"):
            matrix = deepcopy(self.matrix)
            del next(s for s in matrix["stages"] if s["stage"] == "build")[field]
            with self.subTest(field=field), self.assertRaises(ContractError):
                validate_matrix(matrix)
        self.build["artifacts"][0]["sha256"] = "wrong"
        with self.assertRaises(ContractError):
            validate_matrix(self.matrix)


class InputTests(unittest.TestCase):
    def test_missing_empty_unparseable_or_duplicate_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            with self.assertRaises(ContractError):
                load(path)
            for content in ("", "{", "{}", "[]", '{"a":1,"a":2}'):
                path.write_text(content, encoding="utf-8")
                with self.subTest(content=content), self.assertRaises(ContractError):
                    load(path)


if __name__ == "__main__":
    unittest.main()
