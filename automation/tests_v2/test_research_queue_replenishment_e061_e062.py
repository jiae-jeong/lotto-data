import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "automation" / "research_queue_v2.json"


class ResearchQueueReplenishmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        cls.tasks = cls.queue["tasks"]
        cls.by_id = {task["id"]: task for task in cls.tasks}

    def test_e061_is_registered_and_verified_as_completed_diagnostic(self):
        task = self.by_id["E061_B_MODEL_ENSEMBLE_ERROR_CORRELATION_AND_DILUTION_v1"]
        self.assertEqual(task["execution_status"], "EXECUTED_HISTORICAL_DIAGNOSTIC_ONLY")
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        root = ROOT / task["result_path"]
        verification = json.loads((root / "VERIFICATION.json").read_text(encoding="utf-8"))
        completion = json.loads((root / "COMPLETION.json").read_text(encoding="utf-8"))
        self.assertEqual(verification["status"], "PASS")
        self.assertEqual(completion["status"], "COMPLETE_DIAGNOSTIC_ONLY")
        self.assertFalse(completion["strict_pass_ready"])

    def test_e062_is_executed_as_historical_diagnostic_without_three_line_promotion(self):
        task = self.by_id["E062_B_MODEL_TRAILING_PERFORMANCE_SELECTOR_v1"]
        self.assertEqual(task["execution_status"], "EXECUTED_HISTORICAL_DIAGNOSTIC_ONLY")
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        prereg = json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))
        self.assertTrue(prereg["frozen_rule"]["no_parameter_search"])
        self.assertTrue(prereg["frozen_rule"]["no_variant_sweep"])
        root = ROOT / task["result_path"]
        result = json.loads((root / "E062_RESULT.json").read_text(encoding="utf-8"))
        self.assertEqual(result["verification"]["status"], "PASS")
        self.assertEqual(result["verification"]["manifest_entries"], 2)
        self.assertEqual(result["target_count"], 950)
        self.assertFalse(result["completion"]["strict_pass_ready"])
        with (root / "SHA256_MANIFEST.csv").open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                payload = (root / row["file"]).read_bytes()
                self.assertEqual(len(payload), int(row["bytes"]), row["file"])
                self.assertEqual(hashlib.sha256(payload).hexdigest(), row["sha256"], row["file"])

    def test_e063_is_preregistered_as_an_independent_three_line_axis_without_promotion(self):
        task = self.by_id["E063_THREE_LINE_LAST_DIGIT_OCCUPANCY_TRANSITION_v1"]
        self.assertIn(task["execution_status"], (
            "PREREGISTERED_PENDING_DEDICATED_WORKFLOW",
            "EXECUTED_HISTORICAL_STRICT_FAIL",
            "EXECUTED_HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING",
        ))
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        if task["execution_status"] != "PREREGISTERED_PENDING_DEDICATED_WORKFLOW":
            self.assertEqual(task["execution_result"]["verification_status"], "PASS")
            self.assertFalse(task["execution_result"]["strict_pass_ready"])
            self.assertFalse(task["execution_result"]["purchase_recommendation_generated"])
            result_root = ROOT / task["execution_result"]["result_path"]
            verification = json.loads((result_root / "VERIFICATION.json").read_text(encoding="utf-8"))
            completion = json.loads((result_root / "COMPLETION.json").read_text(encoding="utf-8"))
            self.assertEqual(verification["manifest_status"], "PASS")
            self.assertEqual(completion["status"], "COMPLETE")
            with (result_root / "SHA256_MANIFEST.csv").open(encoding="utf-8", newline="") as stream:
                for row in csv.DictReader(stream):
                    payload = (result_root / row["path"]).read_bytes()
                    self.assertEqual(len(payload), int(row["bytes"]), row["path"])
                    self.assertEqual(hashlib.sha256(payload).hexdigest(), row["sha256"], row["path"])
        prereg = json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))
        self.assertTrue(prereg["independent_research_axis"])
        self.assertTrue(prereg["independent_signal_family"])
        self.assertTrue(prereg["historical_exploration_only"])
        self.assertEqual(prereg["historical_data_cutoff"], 1250)
        self.assertEqual(prereg["target_rounds"], "401..1250 inclusive")
        self.assertEqual(prereg["estimator"]["prior_strength"], 45)
        self.assertFalse(prereg["estimator"]["parameter_search"])
        self.assertEqual(prereg["random_comparator"]["random_bundles_per_target"], 120)
        self.assertEqual(prereg["inference"]["bootstrap_replicates"], 4000)
        self.assertEqual(prereg["inference"]["block_length_targets"], 50)
        self.assertIsNone(prereg["prospective_confirmation"]["minimum_target_count"])
        self.assertIsNone(prereg["prospective_confirmation"]["completion_rule"])

    def test_e067_is_preregistered_as_one_historical_exploratory_axis(self):
        task = self.by_id["E067_THREE_LINE_PREVIOUS_DRAW_PRIME_COUNT_TRANSITION_v1"]
        self.assertEqual(task["kind"], "three_line_prime_count_transition")
        self.assertEqual(task["execution_mode"], "dedicated_workflow")
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        self.assertIn(task["execution_status"], (
            "PREREGISTERED_PENDING_DEDICATED_WORKFLOW",
            "EXECUTED_HISTORICAL_STRICT_FAIL",
            "EXECUTED_HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING",
        ))
        prereg = json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))
        self.assertTrue(prereg["independent_research_axis"])
        self.assertTrue(prereg["independent_signal_family"])
        self.assertTrue(prereg["historical_exploration_only"])
        self.assertEqual(prereg["historical_data_cutoff"], 1250)
        self.assertEqual(prereg["target_rounds"], "401..1250 inclusive")
        self.assertEqual(prereg["feature_definition"]["state_components"]["prime_count_bin"], "0 if count<=1; 1 if count==2; 2 if count>=3")
        self.assertFalse(prereg["estimator"]["parameter_search"])
        self.assertEqual(prereg["random_comparator"]["random_bundles_per_target"], 120)
        self.assertEqual(prereg["inference"]["bootstrap_replicates"], 4000)
        self.assertEqual(prereg["inference"]["block_length_targets"], 50)
        self.assertIsNone(prereg["prospective_confirmation"]["minimum_target_count"])
        self.assertIsNone(prereg["prospective_confirmation"]["completion_rule"])
        if task["execution_status"] != "PREREGISTERED_PENDING_DEDICATED_WORKFLOW":
            result = task["execution_result"]
            self.assertEqual(result["verification_status"], "PASS")
            self.assertFalse(result["strict_pass_ready"])
            self.assertFalse(result["purchase_recommendation_generated"])
            root = ROOT / result["result_path"]
            verification = json.loads((root / "VERIFICATION.json").read_text(encoding="utf-8"))
            completion = json.loads((root / "COMPLETION.json").read_text(encoding="utf-8"))
            self.assertEqual(verification["manifest_status"], "PASS")
            self.assertEqual(completion["status"], "COMPLETE")
            with (root / "SHA256_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as stream:
                for row in csv.DictReader(stream):
                    payload = (root / row["path"]).read_bytes()
                    self.assertEqual(len(payload), int(row["bytes"]), row["path"])
                    self.assertEqual(hashlib.sha256(payload).hexdigest(), row["sha256"], row["path"])

    def test_queue_tail_is_append_only_e061_e062_e063_e064_e066_e067(self):
        self.assertEqual([task["id"] for task in self.tasks[-6:]], [
            "E061_B_MODEL_ENSEMBLE_ERROR_CORRELATION_AND_DILUTION_v1",
            "E062_B_MODEL_TRAILING_PERFORMANCE_SELECTOR_v1",
            "E063_THREE_LINE_LAST_DIGIT_OCCUPANCY_TRANSITION_v1",
            "E064_THREE_LINE_BLOCK_PERSISTENT_NULL_CALIBRATION_v1",
            "E066_THREE_LINE_PREVIOUS_DRAW_GAP_SHAPE_TRANSITION_v1",
            "E067_THREE_LINE_PREVIOUS_DRAW_PRIME_COUNT_TRANSITION_v1",
        ])


if __name__ == "__main__":
    unittest.main()

# E063 post-push queue/evidence validation checkpoint: 2026-11-16
