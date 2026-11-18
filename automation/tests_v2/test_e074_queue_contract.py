import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "automation" / "research_queue_v2.json"
STUDY_ID = "E074_THREE_LINE_CALENDAR_MONTH_CONDITIONAL_FREQUENCY_v1"

class E074QueueContractTests(unittest.TestCase):
    def test_e074_preregistration_and_result_contract(self):
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        task = next(x for x in queue["tasks"] if x["id"] == STUDY_ID)
        self.assertEqual(task["kind"], "three_line_calendar_month_conditional_frequency")
        self.assertEqual(task["execution_mode"], "dedicated_workflow")
        self.assertEqual(task["execution_entrypoint"], "automation/three_line_calendar_month_frequency_e074.py")
        self.assertEqual(task["workflow_entrypoint"], ".github/workflows/target-1251-e074-calendar-month-frequency.yml")
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        self.assertIn(task["execution_status"], ("PREREGISTERED_PENDING_DEDICATED_WORKFLOW","EXECUTED_HISTORICAL_STRICT_FAIL","EXECUTED_HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING"))
        self.assertEqual(task["spec"]["execution_status"], task["execution_status"])
        prereg = json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))
        self.assertEqual(prereg["preregistration_status"], "FROZEN_BEFORE_EXECUTION")
        self.assertTrue(prereg["independent_research_axis"])
        self.assertTrue(prereg["independent_signal_family"])
        self.assertFalse(prereg["independent_sample"])
        self.assertEqual(prereg["historical_data_cutoff"], 1250)
        self.assertEqual(prereg["target_rounds"], "401..1250 inclusive")
        self.assertEqual(prereg["feature_definition"]["conditioning"], "calendar month of target draw date")
        self.assertEqual(prereg["estimator"]["prior_strength"], 45)
        self.assertEqual(prereg["estimator"]["prior_successes"], 6)
        self.assertFalse(prereg["estimator"]["parameter_search"])
        self.assertEqual(prereg["random_comparator"]["random_bundles_per_target"], 120)
        self.assertEqual(prereg["inference"]["alpha_per_metric"], 0.0125)
        self.assertEqual(prereg["inference"]["bootstrap_replicates"], 4000)
        self.assertEqual(prereg["inference"]["block_length_targets"], 50)
        self.assertIsNone(prereg["prospective_confirmation"]["minimum_target_count"])
        self.assertIsNone(prereg["prospective_confirmation"]["completion_rule"])
        if task["execution_status"] != "PREREGISTERED_PENDING_DEDICATED_WORKFLOW":
            result = task["execution_result"]
            self.assertEqual(result["verification_status"], "PASS")
            self.assertFalse(result["strict_portfolio_pass"])
            self.assertFalse(result["strict_pass_ready"])
            self.assertFalse(result["purchase_recommendation_generated"])
            self.assertEqual(result["target_count"], 850)
            self.assertEqual(result["random_bundles_total"], 102000)
            self.assertEqual(result["manifest_entries"], 8)
            root = ROOT / task["result_path"]
            verification = json.loads((root / "VERIFICATION.json").read_text(encoding="utf-8"))
            self.assertEqual(verification["status"], "PASS")
            self.assertEqual(verification["training_cutoff_violations"], 0)
            self.assertEqual(verification["leakage_failures"], 0)
            self.assertEqual(verification["future_predictions"], 0)
            with (root / "SHA256_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as stream:
                manifest = list(csv.DictReader(stream))
            self.assertEqual(len(manifest), 8)
            for row in manifest:
                payload = (root / row["path"]).read_bytes()
                self.assertEqual(len(payload), int(row["bytes"]))
                self.assertEqual(hashlib.sha256(payload).hexdigest(), row["sha256"])

if __name__ == "__main__":
    unittest.main()
