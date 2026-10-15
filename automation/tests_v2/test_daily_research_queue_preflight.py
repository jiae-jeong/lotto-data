"""Regression tests for generic daily-research queue preflight."""
import csv
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

    def _write_dedicated(self, task_id="E030_DEDICATED"):
        out = self.root / "analysis" / "dedicated" / task_id
        out.mkdir(parents=True)
        completion = out / "COMPLETION.json"
        verification = out / "VERIFICATION.json"
        report = out / "REPORT.md"
        completion.write_text(json.dumps({"study_id": task_id, "status": "COMPLETE", "executed_cases": 1}) + "\n", encoding="utf-8")
        verification.write_text(json.dumps({"status": "PASS", "future_predictions": 0}) + "\n", encoding="utf-8")
        report.write_text("dedicated evidence\n", encoding="utf-8")
        with (out / "SHA256_MANIFEST.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
            writer.writeheader()
            for path in (completion, report, verification):
                writer.writerow({"path": path.name, "bytes": preflight.engine.raw_size(path), "sha256": preflight.engine.raw_digest(path)})
        return out

    def test_failed_attempt_completion_is_never_a_completion_candidate(self):
        attempt = self.root / "analysis" / "2026-10-14" / ".attempts" / "E025_BAD" / "study"
        attempt.mkdir(parents=True)
        # Deliberately malformed generic completion; strict validation would fail if it were visited.
        (attempt / "COMPLETION.json").write_text(json.dumps({"task_id": "E025_BAD", "status": "COMPLETE"}), encoding="utf-8")
        self.assertEqual(preflight.verified_completed_tasks(self.root), {})

    def test_dedicated_terminal_completion_requires_and_passes_manifest_integrity(self):
        out = self._write_dedicated()
        completed = preflight.verified_completed_tasks(self.root)
        self.assertEqual(completed["E030_DEDICATED"], str(out))

    def test_tampered_dedicated_evidence_still_fails_closed(self):
        out = self._write_dedicated("E031_DEDICATED")
        (out / "REPORT.md").write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Evidence hash mismatch"):
            preflight.verified_completed_tasks(self.root)

    def test_completed_legacy_registration_is_skipped_before_current_validator(self):
        legacy_completed = {"id": "E030_OLD_COMPLETED", "kind": "historical_dedicated"}
        active = self.valid_task()
        self.queue.write_text(json.dumps({"tasks": [legacy_completed, active]}), encoding="utf-8")
        with patch.object(preflight, "verified_completed_tasks", return_value={legacy_completed["id"]: "/validated/e030"}):
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
        with patch.object(preflight, "verified_completed_tasks", return_value={completed["id"]: "/validated/e030"}):
            result = preflight.prepare(self.root, self.queue, self.filtered, self.status)
        self.assertFalse(result["has_work"])
        self.assertEqual(result["status"], "NO_GENERIC_RESEARCH_PENDING")
        self.assertEqual(json.loads(self.filtered.read_text(encoding="utf-8"))["tasks"], [])
        self.assertEqual(result["skipped_blocked"], [blocked["id"]])
        self.assertEqual(result["skipped_dedicated_workflow"], [dedicated["id"]])

    def test_unfinished_generic_task_still_uses_current_validator(self):
        unsafe = {"id": "E103_UNSAFE", "kind": "synthetic"}
        self.queue.write_text(json.dumps({"tasks": [unsafe]}), encoding="utf-8")
        with patch.object(preflight, "verified_completed_tasks", return_value={}):
            with self.assertRaises(ValueError):
                preflight.prepare(self.root, self.queue, self.filtered, self.status)


if __name__ == "__main__":
    unittest.main()
