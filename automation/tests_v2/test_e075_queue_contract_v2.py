import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "automation/research_queue_v2.json"
STUDY_ID = "E075_E045_SELECTOR_ORDER_CONFORMANCE_CORRECTION_v1"


class E075QueueContractV2Tests(unittest.TestCase):
    def test_v3_scope_and_all_three_execution_attempts_are_preserved(self):
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        task = next(x for x in queue["tasks"] if x.get("id") == STUDY_ID)
        self.assertEqual(task["execution_entrypoint"],
                         "automation/three_line_research_1251_e075_corrected_v2.py")
        self.assertEqual(task["preregistration"],
                         "research/weekly_purchase/1251/E075_E045_SELECTOR_ORDER_CONFORMANCE_PREREG_20261119_V3.json")
        self.assertEqual(len(task["attempt_history"]), 2)
        self.assertEqual(task["attempt_history"][0]["status"],
                         "FAILED_BEFORE_ANY_HISTORICAL_METRIC_OUTPUT")
        self.assertEqual(task["attempt_history"][1]["status"],
                         "CALCULATION_COMPLETE_MANIFEST_PASS_BUT_POST_RUN_VERIFIER_FAILED")
        self.assertEqual(len(task["post_v3_attempt_history"]), 1)
        attempt = task["post_v3_attempt_history"][0]
        self.assertEqual(attempt["workflow_run_id"], 44426026061)
        self.assertEqual(attempt["status"],
                         "CALCULATION_COMPLETE_OUTPUTS_VERIFIED_BUT_PERSISTENCE_FAILED")
        self.assertIn("KeyError", attempt["failure"])
        self.assertEqual(task["recovery_trigger_path"],
                         "research/weekly_purchase/1251/E075_PUBLICATION_RECOVERY_20261119.trigger")
        self.assertIn(task["execution_status"], (
            "PREREGISTERED_PENDING_DEDICATED_WORKFLOW",
            "EXECUTED_HISTORICAL_STRICT_FAIL",
            "EXECUTED_HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING",
        ))
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        self.assertFalse(task["spec"]["strict_pass_ready"])


if __name__ == "__main__":
    unittest.main()
