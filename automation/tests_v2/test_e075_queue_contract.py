import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "automation/research_queue_v2.json"
STUDY_ID = "E075_E045_SELECTOR_ORDER_CONFORMANCE_CORRECTION_v1"


class E075QueueContractTests(unittest.TestCase):
    def test_e075_is_registered_before_execution(self):
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        matches = [x for x in queue["tasks"] if x.get("id") == STUDY_ID]
        self.assertEqual(len(matches), 1)
        task = matches[0]
        self.assertEqual(task["execution_mode"], "dedicated_workflow")
        self.assertEqual(task["execution_entrypoint"],
                         "automation/three_line_research_1251_e075_corrected_v1.py")
        self.assertEqual(task["workflow_entrypoint"],
                         ".github/workflows/target-1251-e075-e045-selector-order-audit.yml")
        self.assertEqual(task["preregistration"],
                         "research/weekly_purchase/1251/E075_E045_SELECTOR_ORDER_CONFORMANCE_PREREG_20261119.json")
        self.assertTrue(task["preregistration_blob_sha"])
        self.assertEqual(task["execution_status"], "PREREGISTERED_PENDING_DEDICATED_WORKFLOW")
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        self.assertFalse(task["spec"]["strict_pass_ready"])


if __name__ == "__main__":
    unittest.main()
