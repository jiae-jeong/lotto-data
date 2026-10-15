"""Regression tests for generic daily-research queue preflight."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daily_research_queue_preflight_v1 as preflight


class DailyResearchQueuePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "analysis").mkdir()
        self.queue = self.root / "queue.json"
        self.filtered = self.root / "filtered.json"
        self.status = self.root / "status.json"

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def valid_task(task_id="E100_ACTIVE"):
        return {
            "id": task_id,
            "kind": "synthetic",
            "question": "Current generic task",
            "novelty": "Regression fixture",
            "spec": {
                "study_id": task_id,
                "kind": "synthetic",
                "research_question": "Current generic task",
                "data_cutoff": 1245,
                "target_rounds": [601, 1245],
                "training_cutoff_rule": "target-1",
                "primary_metric": "mean_hits",
                "secondary_metrics": ["rate_ge_2"],
                "comparator": "fixture",
                "baseline": "fixture",
                "multiplicity_correction": "none",
                "block_stability": [50],
                "tie_break": "lower number",
                "expected_output_files": [],
                "expected_record_counts": {},
                "novelty_signature": "preflight-active-regression",
                "study_class": "empirical",
            },
        }

    def test_completed_legacy_registration_is_skipped_before_current_validator(self):
        # This registration intentionally violates today's validator (no question/novelty/spec).
        # It must not block the runner once immutable completion evidence exists.
        legacy_completed = {"id": "E030_OLD_COMPLETED", "kind": "historical_dedicated"}
        active = self.valid_task()
        self.queue.write_text(json.dumps({"tasks": [legacy_completed, active]}), encoding="utf-8")

        with patch.object(preflight.daily, "completed_tasks", return_value={legacy_completed["id"]: "/validated/e030"}):
            result = preflight.prepare(self.root, self.queue, self.filtered, self.status)

        self.assertTrue(result["has_work"])
        self.assertEqual(result["skipped_completed"], [legacy_completed["id"]])
        filtered = json.loads(self.filtered.read_text(encoding="utf-8"))["tasks"]
        self.assertEqual([task["id"] for task in filtered], [active["id"]])

    def test_only_completed_blocked_and_dedicated_tasks_is_clean_noop(self):
        completed = {"id": "E030_DONE", "kind": "old"}
        blocked = self.valid_task("E101_BLOCKED")
        blocked["spec"]["study_class"] = "blocked"
        dedicated = self.valid_task("E102_DEDICATED")
        dedicated["spec"]["execution_mode"] = "dedicated_workflow"
        self.queue.write_text(json.dumps({"tasks": [completed, blocked, dedicated]}), encoding="utf-8")

        with patch.object(preflight.daily, "completed_tasks", return_value={completed["id"]: "/validated/e030"}):
            result = preflight.prepare(self.root, self.queue, self.filtered, self.status)

        self.assertFalse(result["has_work"])
        self.assertEqual(result["status"], "NO_GENERIC_RESEARCH_PENDING")
        self.assertEqual(json.loads(self.filtered.read_text(encoding="utf-8"))["tasks"], [])
        self.assertEqual(result["skipped_blocked"], [blocked["id"]])
        self.assertEqual(result["skipped_dedicated_workflow"], [dedicated["id"]])

    def test_unfinished_generic_task_still_uses_current_validator(self):
        unsafe = {"id": "E103_UNSAFE", "kind": "synthetic"}
        self.queue.write_text(json.dumps({"tasks": [unsafe]}), encoding="utf-8")
        with patch.object(preflight.daily, "completed_tasks", return_value={}):
            with self.assertRaises(ValueError):
                preflight.prepare(self.root, self.queue, self.filtered, self.status)


if __name__ == "__main__":
    unittest.main()
