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

    def test_queue_tail_is_append_only_e061_then_e062(self):
        self.assertEqual([task["id"] for task in self.tasks[-2:]], [
            "E061_B_MODEL_ENSEMBLE_ERROR_CORRELATION_AND_DILUTION_v1",
            "E062_B_MODEL_TRAILING_PERFORMANCE_SELECTOR_v1",
        ])


if __name__ == "__main__":
    unittest.main()
