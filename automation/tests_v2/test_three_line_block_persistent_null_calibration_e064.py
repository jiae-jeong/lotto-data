import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "automation/research_queue_v2.json"
PREREG_PATH = ROOT / "research/weekly_purchase/1251/E064_THREE_LINE_BLOCK_PERSISTENT_NULL_CALIBRATION_PREREG_20261116.json"
POLICY_PATH = ROOT / "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
RUNNER = "automation/three_line_block_persistent_null_calibration_e064.js"
TEST = "automation/tests_v2/test_three_line_block_persistent_null_calibration_e064.py"
WORKFLOW = ".github/workflows/target-1251-e064-block-persistent-null-calibration.yml"
BASE = "automation/three_line_research_1251_v1.py"
POLICY = "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"


def blob_sha(rel):
    return subprocess.check_output(
        ["git", "rev-parse", f"HEAD:{rel}"], cwd=ROOT, text=True
    ).strip()


class E064BlockPersistentNullCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        cls.tasks = cls.queue["tasks"]
        cls.by_id = {task["id"]: task for task in cls.tasks}
        cls.prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    def test_e064_is_appended_after_e063_without_rewriting_prior_tasks(self):
        self.assertEqual(
            [task["id"] for task in self.tasks[-4:]],
            [
                "E061_B_MODEL_ENSEMBLE_ERROR_CORRELATION_AND_DILUTION_v1",
                "E062_B_MODEL_TRAILING_PERFORMANCE_SELECTOR_v1",
                "E063_THREE_LINE_LAST_DIGIT_OCCUPANCY_TRANSITION_v1",
                "E064_THREE_LINE_BLOCK_PERSISTENT_NULL_CALIBRATION_v1",
            ],
        )
        task = self.by_id["E064_THREE_LINE_BLOCK_PERSISTENT_NULL_CALIBRATION_v1"]
        self.assertEqual(task["kind"], "three_line_block_persistent_null_calibration")
        self.assertEqual(task["execution_mode"], "dedicated_workflow")
        self.assertEqual(task["execution_entrypoint"], RUNNER)
        self.assertEqual(task["workflow_entrypoint"], WORKFLOW)
        self.assertEqual(task["preregistration"], str(PREREG_PATH.relative_to(ROOT)))
        self.assertIn(
            task["execution_status"],
            ("PREREGISTERED_PENDING_DEDICATED_WORKFLOW", "EXECUTED_NULL_CALIBRATION_ONLY"),
        )

    def test_preregistration_is_frozen_and_block_persistent_null_is_distinct(self):
        p = self.prereg
        self.assertEqual(p["study_id"], "E064_THREE_LINE_BLOCK_PERSISTENT_NULL_CALIBRATION_v1")
        self.assertEqual(p["preregistration_status"], "FROZEN_BEFORE_EXECUTION")
        self.assertEqual(p["evidence_class"], "NULL_GATE_CALIBRATION_ONLY_BLOCK_PERSISTENT_RANDOM_PORTFOLIO_MECHANISM")
        self.assertEqual(p["data"]["cutoff"], 1250)
        self.assertEqual(p["data"]["target_range"], [401, 1250])
        self.assertEqual(p["data"]["target_count"], 850)
        self.assertEqual(p["simulation"]["trajectories"], 1000)
        self.assertEqual(p["simulation"]["block_size"], 50)
        self.assertEqual(p["simulation"]["blocks"], 17)
        self.assertEqual(p["simulation"]["bootstrap_replicates_per_metric_per_trajectory"], 4000)
        self.assertEqual(p["null_process"]["portfolio_lifetime_targets"], 50)
        self.assertTrue(p["null_process"]["outcome_independence"])
        self.assertFalse(p["purchase_recommendation_generated"])
        self.assertFalse(p["strict_pass_ready"])

    def test_strict_policy_is_unchanged(self):
        p = self.prereg["strict_gate"]
        g = self.policy["strict_gate"]
        self.assertEqual(p["family_alpha"], g["family_alpha"])
        self.assertEqual(p["alpha_per_metric"], g["alpha_per_metric"])
        self.assertEqual(p["block_length_targets"], 50)
        self.assertEqual(p["any2_positive_nonoverlapping_50_target_block_share_min"], 0.65)
        self.assertFalse(p["thresholds_changed"])
        self.assertFalse(p["alpha_changed"])
        self.assertFalse(p["block_length_changed"])
        self.assertFalse(p["comparator_changed"])

    def test_frozen_git_blob_hashes_match(self):
        expected = self.prereg["frozen_blobs"]
        paths = {
            "runner_blob_sha": RUNNER,
            "test_blob_sha": TEST,
            "workflow_blob_sha": WORKFLOW,
            "base_runner_blob_sha": BASE,
            "policy_blob_sha": POLICY,
        }
        for key, rel in paths.items():
            with self.subTest(path=rel):
                self.assertEqual(blob_sha(rel), expected[key])

    def test_existing_e063_and_purchase_readiness_are_not_promoted(self):
        e063 = self.by_id["E063_THREE_LINE_LAST_DIGIT_OCCUPANCY_TRANSITION_v1"]
        self.assertEqual(e063["execution_status"], "EXECUTED_HISTORICAL_STRICT_FAIL")
        self.assertFalse(e063["execution_result"]["strict_pass_ready"])
        self.assertFalse(e063["execution_result"]["purchase_recommendation_generated"])
        self.assertFalse(self.prereg["strict_pass_ready"])


if __name__ == "__main__":
    unittest.main()
