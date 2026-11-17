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
        with (self.root / "lotto_data.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["round"], lineterminator="\n")
            writer.writeheader()
            writer.writerows({"round": number} for number in range(1, 1251))
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
                "data_cutoff": 1250,
                "target_rounds": [601, 1250],
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

    def _write_dedicated(self, task_id="E030_DEDICATED", verification_status=None):
        out = self.root / "analysis" / "dedicated" / task_id
        out.mkdir(parents=True)
        completion = out / "COMPLETION.json"
        verification = out / "VERIFICATION.json"
        report = out / "REPORT.md"
        completion.write_text(json.dumps({"study_id": task_id, "status": "COMPLETE", "executed_cases": 1}) + "\n", encoding="utf-8")
        verification_payload = {"study_id": task_id, "leakage_failures": 0, "future_predictions": 0}
        if verification_status is not None:
            verification_payload["status"] = verification_status
        verification.write_text(json.dumps(verification_payload) + "\n", encoding="utf-8")
        report.write_text("dedicated evidence\n", encoding="utf-8")
        with (out / "SHA256_MANIFEST.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
            writer.writeheader()
            for path in (completion, report, verification):
                writer.writerow({"path": path.name, "bytes": preflight.engine.raw_size(path), "sha256": preflight.engine.raw_digest(path)})
        return out


    def _write_registered_code_mode_task(self, task_id="E110_EXECUTED", cutoff=1250):
        relative = Path("analysis") / "2026-11-16" / "codemode_fixture" / task_id
        out = self.root / relative
        out.mkdir(parents=True)
        data_sha = preflight.engine.raw_digest(self.root / "lotto_data.csv")
        source_blob = "c" * 40
        source_file = self.root / "analysis" / "source.csv"
        source_file.write_text("round,model\\n1,A\\n", encoding="utf-8")
        source_sha = preflight.engine.raw_digest(source_file)
        result = {
            "study_id": task_id,
            "source": {
                "path": "analysis/source.csv",
                "git_blob_sha": source_blob,
                "sha256": source_sha,
                "bytes": preflight.engine.raw_size(source_file),
            },
            "canonical_data": {"rows": cutoff, "rounds": [1, cutoff], "sha256": data_sha},
            "evaluation_targets": [601, 601],
            "target_count": 1,
            "verification": {
                "status": "PASS",
                "training_cutoff_violations": 0,
                "missing_rows": 0,
                "duplicate_rows": 0,
                "future_outcomes_used": False,
                "random_baseline_executed": True,
                "manifest_entries": 2,
                "manifest_status": "PASS",
            },
            "completion": {
                "status": "COMPLETE_DIAGNOSTIC_ONLY",
                "strict_pass_ready": False,
                "purchase_recommendation_generated": False,
            },
            "predictions": [{"target": 601, "training_through": 600, "window_end": 600}],
        }
        result_path = out / "RESULT.json"
        report_path = out / "REPORT.md"
        result_path.write_text(json.dumps(result) + "\n", encoding="utf-8")
        report_path.write_text("verified code-mode diagnostic\n", encoding="utf-8")
        manifest_path = out / "SHA256_MANIFEST.csv"
        with manifest_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["file", "bytes", "sha256"], lineterminator="\n")
            writer.writeheader()
            for path in (result_path, report_path):
                writer.writerow({
                    "file": path.name,
                    "bytes": preflight.engine.raw_size(path),
                    "sha256": preflight.engine.raw_digest(path),
                })
        relative_text = relative.as_posix()
        task = {
            "id": task_id,
            "kind": "code_mode_diagnostic",
            "question": "Already executed registered code-mode diagnostic",
            "novelty": "Frozen prior diagnostic; must not be repeated",
            "data_cutoff": cutoff,
            "result_path": relative_text,
            "execution_mode": "code_mode_pre_registered",
            "execution_status": "EXECUTED_HISTORICAL_DIAGNOSTIC_ONLY",
            "execution_result": {
                "result_path": relative_text,
                "data_cutoff": cutoff,
                "data_sha256": data_sha,
                "source_git_blob_sha": source_blob,
                "source_sha256": source_sha,
                "target_count": 1,
                "verification_status": "PASS",
                "manifest_entries": 2,
                "manifest_status": "PASS",
                "strict_pass_ready": False,
                "purchase_recommendation_generated": False,
            },
            # Deliberately incomplete: terminal evidence must be checked before generic validation.
            "spec": {"data_cutoff": cutoff},
        }
        return task, out

    def test_failed_attempt_completion_is_never_a_completion_candidate(self):
        attempt = self.root / "analysis" / "2026-10-14" / ".attempts" / "E025_BAD" / "study"
        attempt.mkdir(parents=True)
        (attempt / "COMPLETION.json").write_text(json.dumps({"task_id": "E025_BAD", "status": "COMPLETE"}), encoding="utf-8")
        self.assertEqual(preflight.verified_completed_tasks(self.root), {})

    def test_dedicated_terminal_completion_allows_study_specific_status_vocabulary(self):
        out = self._write_dedicated()
        completed = preflight.verified_completed_tasks(self.root)
        self.assertEqual(completed["E030_DEDICATED"], str(out))
        # CALIBRATED is a valid study-specific terminal status, not a generic PASS string.
        other_root = Path(self.temp.name) / "other"
        (other_root / "analysis").mkdir(parents=True)
        old_root = self.root
        self.root = other_root
        try:
            out2 = self._write_dedicated("E036_CALIBRATED", "CALIBRATED")
            completed2 = preflight.verified_completed_tasks(self.root)
            self.assertEqual(completed2["E036_CALIBRATED"], str(out2))
        finally:
            self.root = old_root

    def test_explicit_dedicated_verification_failure_still_fails_closed(self):
        self._write_dedicated("E031_FAILED", "FAIL")
        with self.assertRaisesRegex(ValueError, "explicitly failed"):
            preflight.verified_completed_tasks(self.root)

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

    def test_superseded_studies_are_skipped_before_generic_execution(self):
        superseded_link = self.valid_task("E104_SUPERSEDED_LINK")
        superseded_link["superseded_by"] = "E105_REPLACEMENT"
        superseded_status = self.valid_task("E106_SUPERSEDED_STATUS")
        superseded_status["spec"]["execution_status"] = "SUPERSEDED_BEFORE_EXECUTION"
        active = self.valid_task("E107_ACTIVE")
        self.queue.write_text(json.dumps({"tasks": [superseded_link, superseded_status, active]}), encoding="utf-8")
        with patch.object(preflight, "verified_completed_tasks", return_value={}):
            result = preflight.prepare(self.root, self.queue, self.filtered, self.status)
        self.assertTrue(result["has_work"])
        self.assertEqual(
            result["skipped_superseded"],
            [superseded_link["id"], superseded_status["id"]],
        )
        filtered = json.loads(self.filtered.read_text(encoding="utf-8"))["tasks"]
        self.assertEqual([task["id"] for task in filtered], [active["id"]])

    def test_stale_cutoff_tasks_are_skipped_before_generic_execution(self):
        stale = self.valid_task("E108_STALE")
        stale["spec"]["data_cutoff"] = 1245
        stale["spec"]["target_rounds"] = [601, 1245]
        active = self.valid_task("E109_CURRENT")
        self.queue.write_text(json.dumps({"tasks": [stale, active]}), encoding="utf-8")
        with patch.object(preflight, "verified_completed_tasks", return_value={}):
            result = preflight.prepare(self.root, self.queue, self.filtered, self.status)
        self.assertTrue(result["has_work"])
        self.assertEqual(result["current_data_cutoff"], 1250)
        self.assertEqual([item["task_id"] for item in result["skipped_stale_cutoff"]], [stale["id"]])
        filtered = json.loads(self.filtered.read_text(encoding="utf-8"))["tasks"]
        self.assertEqual([task["id"] for task in filtered], [active["id"]])

    def test_missing_cutoff_legacy_tasks_are_skipped_as_stale(self):
        legacy = {
            "id": "E010_FAMILY_DECORRELATION_v1",
            "kind": "family",
            "question": "Legacy family task",
            "novelty": "No frozen current-cutoff evidence",
        }
        self.queue.write_text(json.dumps({"tasks": [legacy]}), encoding="utf-8")
        with patch.object(preflight, "verified_completed_tasks", return_value={}):
            result = preflight.prepare(self.root, self.queue, self.filtered, self.status)
        self.assertFalse(result["has_work"])
        self.assertEqual(result["status"], "NO_GENERIC_RESEARCH_PENDING")
        self.assertEqual(result["skipped_stale_cutoff"][0]["task_id"], legacy["id"])
        self.assertIsNone(result["skipped_stale_cutoff"][0]["registered_cutoff"])


    def test_verified_registered_code_mode_execution_is_skipped_before_generic_validator(self):
        task, out = self._write_registered_code_mode_task()
        self.queue.write_text(json.dumps({"tasks": [task]}), encoding="utf-8")
        with patch.object(preflight, "verified_completed_tasks", return_value={}):
            result = preflight.prepare(self.root, self.queue, self.filtered, self.status)
        self.assertFalse(result["has_work"])
        self.assertEqual(result["skipped_registered_execution"], [task["id"]])
        self.assertEqual(json.loads(self.filtered.read_text(encoding="utf-8"))["tasks"], [])


    def test_actual_e062_registered_code_mode_evidence_is_verified(self):
        repository = Path(__file__).resolve().parents[2]
        queue = json.loads((repository / "automation" / "research_queue_v2.json").read_text(encoding="utf-8"))
        task = next(item for item in queue["tasks"] if item["id"] == "E062_B_MODEL_TRAILING_PERFORMANCE_SELECTOR_v1")
        result_path = preflight._validate_registered_execution(repository, task, 1250)
        self.assertEqual(result_path, str((repository / task["result_path"]).resolve()))

    def test_tampered_registered_code_mode_evidence_fails_closed(self):
        task, out = self._write_registered_code_mode_task()
        (out / "REPORT.md").write_text("tampered\n", encoding="utf-8")
        self.queue.write_text(json.dumps({"tasks": [task]}), encoding="utf-8")
        with patch.object(preflight, "verified_completed_tasks", return_value={}):
            with self.assertRaisesRegex(ValueError, "Evidence hash mismatch"):
                preflight.prepare(self.root, self.queue, self.filtered, self.status)

    def test_executed_code_mode_task_without_verifiable_evidence_fails_closed(self):
        task = self.valid_task("E111_UNVERIFIED_EXECUTION")
        task["execution_status"] = "EXECUTED_HISTORICAL_DIAGNOSTIC_ONLY"
        task["execution_result"] = {}
        self.queue.write_text(json.dumps({"tasks": [task]}), encoding="utf-8")
        with patch.object(preflight, "verified_completed_tasks", return_value={}):
            with self.assertRaisesRegex(ValueError, "no registered result_path"):
                preflight.prepare(self.root, self.queue, self.filtered, self.status)

    def test_unfinished_generic_task_still_uses_current_validator(self):
        unsafe = {"id": "E103_UNSAFE", "kind": "synthetic", "spec": {"data_cutoff": 1250}}
        self.queue.write_text(json.dumps({"tasks": [unsafe]}), encoding="utf-8")
        with patch.object(preflight, "verified_completed_tasks", return_value={}):
            with self.assertRaises(ValueError):
                preflight.prepare(self.root, self.queue, self.filtered, self.status)


if __name__ == "__main__":
    unittest.main()
