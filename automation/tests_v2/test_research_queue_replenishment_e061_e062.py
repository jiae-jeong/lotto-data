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
        task_id = "E061_B_MODEL_ENSEMBLE_ERROR_CORRELATION_AND_DILUTION_v1"
        self.assertEqual(sum(t["id"] == task_id for t in self.tasks), 1)
        task = self.by_id[task_id]
        self.assertEqual(task["execution_status"], "EXECUTED_HISTORICAL_DIAGNOSTIC_ONLY")
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        result_root = ROOT / task["result_path"]
        verification = json.loads((result_root / "VERIFICATION.json").read_text(encoding="utf-8"))
        completion = json.loads((result_root / "COMPLETION.json").read_text(encoding="utf-8"))
        self.assertEqual(verification["status"], "PASS")
        self.assertEqual(completion["status"], "COMPLETE_DIAGNOSTIC_ONLY")
        self.assertFalse(verification["strict_pass_ready"])

    def test_e062_is_preregistered_and_pending_without_three_line_promotion(self):
        task_id = "E062_B_MODEL_TRAILING_PERFORMANCE_SELECTOR_v1"
        self.assertEqual(sum(t["id"] == task_id for t in self.tasks), 1)
        task = self.by_id[task_id]
        self.assertEqual(task["execution_status"], "PREREGISTERED_PENDING_EXECUTION")
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        prereg = json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))
        self.assertEqual(prereg["study_id"], task_id)
        self.assertEqual(prereg["frozen_rule"]["lookback_targets"], 100)
        self.assertEqual(prereg["frozen_rule"]["evaluation_targets"], [301, 1250])
        self.assertFalse(prereg["frozen_rule"]["no_parameter_search"] is False)

    def test_queue_tail_is_append_only_e061_then_e062(self):
        self.assertEqual(
            [task["id"] for task in self.tasks[-2:]],
            [
                "E061_B_MODEL_ENSEMBLE_ERROR_CORRELATION_AND_DILUTION_v1",
                "E062_B_MODEL_TRAILING_PERFORMANCE_SELECTOR_v1",
            ],
        )


if __name__ == "__main__":
    unittest.main()
