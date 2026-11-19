import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "automation/research_queue_v2.json"
STUDY_ID = "E075_E045_SELECTOR_ORDER_CONFORMANCE_CORRECTION_v1"


class E075QueueContractTests(unittest.TestCase):
    def test_current_v3_preregistration_preserves_v1_and_v2_history(self):
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        task = next(x for x in queue["tasks"] if x.get("id") == STUDY_ID)
        self.assertEqual(task["execution_mode"], "dedicated_workflow")
        self.assertEqual(task["execution_entrypoint"],
                         "automation/three_line_research_1251_e075_corrected_v2.py")
        self.assertEqual(task["workflow_entrypoint"],
                         ".github/workflows/target-1251-e075-e045-selector-order-audit.yml")
        self.assertEqual(task["preregistration"],
                         "research/weekly_purchase/1251/E075_E045_SELECTOR_ORDER_CONFORMANCE_PREREG_20261119_V3.json")
        self.assertEqual(task["preregistration_blob_sha"],
                         "5d042c1f76f0e447900f37c966548833ec833d72")
        self.assertEqual(len(task["attempt_history"]), 2)
        self.assertEqual([x["workflow_run_id"] for x in task["attempt_history"]],
                         [44424313742, 44424750856])
        self.assertEqual(task["recovery_workflow_entrypoint"],
                         ".github/workflows/target-1251-e075-publication-recovery.yml")
        self.assertFalse(task["independent_research_axis"])
        self.assertFalse(task["independent_sample"])
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        self.assertFalse(task["spec"]["strict_pass_ready"])
        self.assertIn(task["execution_status"], (
            "PREREGISTERED_PENDING_DEDICATED_WORKFLOW",
            "EXECUTED_HISTORICAL_STRICT_FAIL",
            "EXECUTED_HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING",
        ))
        if task["execution_status"] != "PREREGISTERED_PENDING_DEDICATED_WORKFLOW":
            self.assertFalse(task["execution_result"]["strict_pass_ready"])
            self.assertFalse(task["execution_result"]["purchase_recommendation_generated"])


if __name__ == "__main__":
    unittest.main()
