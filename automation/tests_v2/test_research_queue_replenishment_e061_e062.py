# E069, E071, E072, and E073 result evidence is checked after dedicated workflows publish immutable manifests.
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
        self.assertEqual(task["question"], prereg_question := json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))["research_question"])
        self.assertEqual(task["novelty"], json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))["novelty_statement"])
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

    def test_e068_is_preregistered_as_one_historical_exploratory_axis(self):
        task = self.by_id["E068_THREE_LINE_PREVIOUS_TWO_DRAW_OVERLAP_COUNT_TRANSITION_v1"]
        self.assertEqual(task["kind"], "three_line_overlap_count_transition")
        self.assertEqual(task["execution_mode"], "dedicated_workflow")
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        self.assertIn(task["execution_status"], ("PREREGISTERED_PENDING_DEDICATED_WORKFLOW", "EXECUTED_HISTORICAL_STRICT_FAIL", "EXECUTED_HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING"))
        prereg = json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))
        self.assertEqual(task["question"], prereg["research_question"])
        self.assertEqual(task["novelty"], prereg["novelty_statement"])
        self.assertTrue(prereg["independent_research_axis"])
        self.assertTrue(prereg["independent_signal_family"])
        self.assertTrue(prereg["historical_exploration_only"])
        self.assertEqual(prereg["historical_data_cutoff"], 1250)
        self.assertEqual(prereg["target_rounds"], "401..1250 inclusive")
        self.assertEqual(prereg["feature_definition"]["state_components"]["overlap_count_bin"], "0 if overlap_count==0; 1 if overlap_count==1; 2 if overlap_count>=2")
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

    def test_e069_is_preregistered_as_one_historical_lag1_membership_axis_without_promotion(self):
        task = self.by_id["E069_THREE_LINE_PREVIOUS_DRAW_MEMBERSHIP_TRANSITION_v1"]
        self.assertEqual(task["kind"], "three_line_previous_draw_membership_transition")
        self.assertEqual(task["execution_mode"], "dedicated_workflow")
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        self.assertIn(task["execution_status"], (
            "PREREGISTERED_PENDING_DEDICATED_WORKFLOW",
            "EXECUTED_HISTORICAL_STRICT_FAIL",
            "EXECUTED_HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING",
        ))
        prereg = json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))
        self.assertEqual(task["question"], prereg["research_question"])
        self.assertEqual(task["novelty"], prereg["novelty_statement"])
        self.assertTrue(prereg["independent_research_axis"])
        self.assertTrue(prereg["independent_signal_family"])
        self.assertTrue(prereg["historical_exploration_only"])
        self.assertEqual(prereg["historical_data_cutoff"], 1250)
        self.assertEqual(prereg["target_rounds"], "401..1250 inclusive")
        self.assertEqual(prereg["feature_definition"]["class"], "For candidate n, state s is 1 if n appeared among the previous draw's six main numbers; otherwise s is 0.")
        self.assertEqual(prereg["estimator"]["prior_strength"], 45)
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

    def test_queue_tail_is_append_only_through_e076(self):
        self.assertEqual([task["id"] for task in self.tasks[-14:]], [
            "E061_B_MODEL_ENSEMBLE_ERROR_CORRELATION_AND_DILUTION_v1",
            "E062_B_MODEL_TRAILING_PERFORMANCE_SELECTOR_v1",
            "E063_THREE_LINE_LAST_DIGIT_OCCUPANCY_TRANSITION_v1",
            "E064_THREE_LINE_BLOCK_PERSISTENT_NULL_CALIBRATION_v1",
            "E066_THREE_LINE_PREVIOUS_DRAW_GAP_SHAPE_TRANSITION_v1",
            "E067_THREE_LINE_PREVIOUS_DRAW_PRIME_COUNT_TRANSITION_v1",
            "E068_THREE_LINE_PREVIOUS_TWO_DRAW_OVERLAP_COUNT_TRANSITION_v1",
            "E069_THREE_LINE_PREVIOUS_DRAW_MEMBERSHIP_TRANSITION_v1",
            "E071_THREE_LINE_PREVIOUS_BONUS_DISTANCE_TRANSITION_v1",
            "E072_THREE_LINE_RANK_PROBABILITY_CALIBRATION_v1",
            "E073_THREE_LINE_THREE_DRAW_MEMBERSHIP_COUNT_TRANSITION_v1",
            "E074_THREE_LINE_CALENDAR_MONTH_CONDITIONAL_FREQUENCY_v1",
            "E075_E045_SELECTOR_ORDER_CONFORMANCE_CORRECTION_v1",
            "E076_HISTORICAL_RECOMMENDATION_CANDIDATE_VS_ALLOCATOR_DECOMPOSITION_v1",
        ])

    def test_e073_three_draw_membership_count_is_frozen_and_never_purchase_ready(self):
        task = self.by_id["E073_THREE_LINE_THREE_DRAW_MEMBERSHIP_COUNT_TRANSITION_v1"]
        self.assertEqual(task["kind"], "three_line_three_draw_membership_count_transition")
        self.assertEqual(task["execution_mode"], "dedicated_workflow")
        self.assertEqual(task["execution_entrypoint"], "automation/three_line_three_draw_membership_count_e073.py")
        self.assertEqual(task["workflow_entrypoint"], ".github/workflows/target-1251-e073-three-draw-membership-count.yml")
        self.assertTrue(task["independent_research_axis"])
        self.assertFalse(task["independent_sample"])
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        self.assertIn(task["execution_status"], (
            "PREREGISTERED_PENDING_DEDICATED_WORKFLOW",
            "EXECUTED_HISTORICAL_STRICT_FAIL",
            "EXECUTED_HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING",
        ))
        self.assertEqual(task["spec"]["execution_status"], task["execution_status"])
        prereg = json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))
        self.assertEqual(prereg["preregistration_status"], "FROZEN_BEFORE_EXECUTION")
        self.assertTrue(prereg["independent_research_axis"])
        self.assertTrue(prereg["independent_signal_family"])
        self.assertFalse(prereg["independent_sample"])
        self.assertEqual(prereg["historical_data_cutoff"], 1250)
        self.assertEqual(prereg["target_rounds"], "401..1250 inclusive")
        self.assertEqual(prereg["feature_definition"]["state_encoding"], {
            "0": "candidate absent from all three immediately preceding main draws",
            "1": "candidate present in exactly one of the three immediately preceding main draws",
            "2": "candidate present in exactly two of the three immediately preceding main draws",
            "3": "candidate present in all three immediately preceding main draws",
        })
        self.assertEqual(prereg["estimator"]["prior_strength"], 45)
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
            self.assertEqual(result["data_cutoff"], 1250)
            self.assertEqual(result["target_count"], 850)
            self.assertEqual(result["random_bundles_total"], 102000)
            self.assertEqual(result["manifest_entries"], 8)
            root = ROOT / task["result_path"]
            verification = json.loads((root / "VERIFICATION.json").read_text(encoding="utf-8"))
            self.assertEqual(verification["status"], "PASS")
            self.assertEqual(verification["training_cutoff_violations"], 0)
            self.assertEqual(verification["leakage_failures"], 0)
            self.assertEqual(verification["future_predictions"], 0)
            self.assertFalse(verification["strict_pass_ready"])
            with (root / "SHA256_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as stream:
                manifest = list(csv.DictReader(stream))
            self.assertEqual(len(manifest), 8)
            for row in manifest:
                payload = (root / row["path"]).read_bytes()
                self.assertEqual(len(payload), int(row["bytes"]), row["path"])
                self.assertEqual(hashlib.sha256(payload).hexdigest(), row["sha256"], row["path"])

    def test_e072_rank_probability_calibration_is_historical_no_edge_and_never_purchase_ready(self):
        task = self.by_id["E072_THREE_LINE_RANK_PROBABILITY_CALIBRATION_v1"]
        self.assertEqual(task["execution_status"], "EXECUTED_HISTORICAL_CALIBRATION_NO_EDGE")
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        self.assertEqual(task["result_path"], "analysis/2026-11-18/gha_44230929833_1/E072_THREE_LINE_RANK_PROBABILITY_CALIBRATION_v1")

        prereg = json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))
        self.assertEqual(prereg["preregistration_status"], "FROZEN_BEFORE_EXECUTION")
        self.assertTrue(prereg["independent_research_axis"])
        self.assertFalse(prereg["independent_sample"])
        self.assertEqual(prereg["training_targets"], [201, 600])
        self.assertEqual(prereg["evaluation_targets"], [601, 1250])
        self.assertEqual(prereg["calibration"]["bins"], 5)
        self.assertEqual(prereg["calibration"]["prior_strength"], 45)
        self.assertEqual(prereg["random_comparator"]["total_permutations"], 78000)
        self.assertEqual(prereg["inference"]["bootstrap_replicates"], 4000)
        self.assertEqual(prereg["inference"]["block_length_targets"], 50)
        self.assertEqual(prereg["variants_evaluated"], 1)
        self.assertFalse(prereg["parameter_search"])
        self.assertFalse(prereg["strict_portfolio_policy"]["strict_pass_ready"])

        result = task["execution_result"]
        self.assertEqual(result["verification_status"], "PASS")
        self.assertFalse(result["calibration_gate_pass"])
        self.assertFalse(result["strict_portfolio_pass"])
        self.assertFalse(result["strict_pass_ready"])
        self.assertFalse(result["purchase_recommendation_generated"])
        self.assertEqual(result["data_cutoff"], 1250)
        self.assertEqual(result["training_targets"], 400)
        self.assertEqual(result["evaluation_targets"], 650)
        self.assertEqual(result["random_permutations_total"], 78000)
        self.assertEqual(result["manifest_entries"], 8)

        root = ROOT / task["result_path"]
        verification = json.loads((root / "VERIFICATION.json").read_text(encoding="utf-8"))
        inference = json.loads((root / "INFERENCE.json").read_text(encoding="utf-8"))
        self.assertEqual(verification["status"], "PASS")
        self.assertEqual(verification["data_cutoff"], 1250)
        self.assertEqual(verification["evaluation_targets_count"], 650)
        self.assertEqual(verification["random_permutations_total"], 78000)
        self.assertEqual(verification["feature_cutoff_violations"], 0)
        self.assertEqual(verification["training_feature_cutoff_violations"], 0)
        self.assertEqual(verification["future_predictions"], 0)
        self.assertFalse(verification["calibrator_uses_evaluation_outcomes"])
        self.assertEqual(verification["leakage_failures"], 0)
        self.assertFalse(verification["strict_pass_ready"])
        self.assertEqual(inference["study_id"], "E072_THREE_LINE_RANK_PROBABILITY_CALIBRATION_v1")
        self.assertFalse(inference["calibration_gate_pass"])
        self.assertFalse(inference["strict_pass_ready"])

        with (root / "SHA256_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as stream:
            manifest = list(csv.DictReader(stream))
        self.assertEqual(len(manifest), 8)
        for row in manifest:
            payload = (root / row["path"]).read_bytes()
            self.assertEqual(len(payload), int(row["bytes"]), row["path"])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), row["sha256"], row["path"])


    def test_e071_bonus_distance_axis_has_verified_historical_evidence_without_readiness(self):
        task = self.by_id["E071_THREE_LINE_PREVIOUS_BONUS_DISTANCE_TRANSITION_v1"]
        self.assertEqual(task["execution_status"], "EXECUTED_HISTORICAL_STRICT_FAIL")
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        result = task["execution_result"]
        self.assertEqual(result["verification_status"], "PASS")
        self.assertFalse(result["strict_portfolio_pass"])
        self.assertFalse(result["strict_pass_ready"])
        self.assertFalse(result["purchase_recommendation_generated"])
        self.assertEqual(result["data_cutoff"], 1250)
        self.assertEqual(result["targets"], 850)
        self.assertEqual(result["random_bundles_total"], 102000)

        prereg = json.loads((ROOT / task["preregistration"]).read_text(encoding="utf-8"))
        self.assertTrue(prereg["independent_research_axis"])
        self.assertFalse(prereg["independent_sample"])
        self.assertTrue(prereg["historical_exploration_only"])
        self.assertEqual(prereg["feature_definition"]["binning"]["cutpoints"], [5, 10, 17, 25])
        self.assertEqual(prereg["feature_definition"]["binning"]["bin_counts"], [465, 370, 434, 376, 380])
        self.assertEqual(prereg["estimator"]["prior_strength"], 45)
        self.assertFalse(prereg["estimator"]["parameter_search"])
        self.assertEqual(prereg["random_comparator"]["random_bundles_per_target"], 120)
        self.assertEqual(prereg["inference"]["alpha_per_metric"], 0.0125)
        self.assertEqual(prereg["inference"]["bootstrap_replicates"], 4000)
        self.assertEqual(prereg["inference"]["block_length_targets"], 50)
        self.assertIsNone(prereg["prospective_confirmation"]["minimum_target_count"])
        self.assertIsNone(prereg["prospective_confirmation"]["completion_rule"])

        root = ROOT / result["result_path"]
        verification = json.loads((root / "VERIFICATION.json").read_text(encoding="utf-8"))
        inference = json.loads((root / "INFERENCE.json").read_text(encoding="utf-8"))
        completion = json.loads((root / "COMPLETION.json").read_text(encoding="utf-8"))
        self.assertEqual(verification["status"], "PASS")
        self.assertEqual(verification["data_cutoff"], 1250)
        self.assertEqual(verification["target_count"], 850)
        self.assertEqual(verification["random_bundles_total"], 102000)
        self.assertEqual(verification["training_cutoff_violations"], 0)
        self.assertEqual(verification["leakage_failures"], 0)
        self.assertEqual(verification["manifest_entries"], 8)
        self.assertEqual(verification["manifest_status"], "PASS")
        self.assertFalse(inference["historical_strict_gate_pass"])
        self.assertFalse(inference["strict_pass_ready"])
        self.assertEqual(inference["any2_positive_nonoverlapping_50_target_blocks"], 10)
        self.assertAlmostEqual(inference["any2_positive_block_share"], 10 / 17)
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertFalse(completion["strict_pass_ready"])

        with (root / "PREDICTIONS.csv").open(encoding="utf-8-sig", newline="") as stream:
            predictions = list(csv.DictReader(stream))
        self.assertEqual(len(predictions), 850)
        self.assertEqual([int(row["target_round"]) for row in predictions], list(range(401, 1251)))
        for row in predictions:
            target = int(row["target_round"])
            self.assertEqual(int(row["training_through_round"]), target - 1)
            self.assertEqual(int(row["previous_bonus_round"]), target - 1)
            lines = json.loads(row["model_lines"])
            self.assertEqual(len(lines), 3)
            self.assertTrue(all(len(line) == 6 and len(set(line)) == 6 for line in lines))
            self.assertEqual(len(set().union(*(set(line) for line in lines))), 18)

        with (root / "RANDOM_BASELINE.csv").open(encoding="utf-8-sig", newline="") as stream:
            random_rows = list(csv.DictReader(stream))
        self.assertEqual(len(random_rows), 850)
        self.assertTrue(all(int(row["random_bundles"]) == 120 for row in random_rows))
        with (root / "BLOCK_STABILITY.csv").open(encoding="utf-8-sig", newline="") as stream:
            blocks = list(csv.DictReader(stream))
        self.assertEqual(len(blocks), 17)
        self.assertEqual(sum(int(row["target_count"]) for row in blocks), 850)

        with (root / "SHA256_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as stream:
            manifest = list(csv.DictReader(stream))
        self.assertEqual(len(manifest), 8)
        for row in manifest:
            payload = (root / row["path"]).read_bytes()
            self.assertEqual(len(payload), int(row["bytes"]), row["path"])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), row["sha256"], row["path"])


if __name__ == "__main__":
    unittest.main()

# E063 post-push queue/evidence validation checkpoint: 2026-11-16
