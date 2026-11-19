import importlib.util
import math
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "three_line_rank_probability_calibration_e072.py"
spec = importlib.util.spec_from_file_location("e072", SCRIPT)
e072 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e072)


class RankProbabilityCalibrationE072Tests(unittest.TestCase):
    def test_normalize_expected_six_uniform(self):
        probs = e072.normalize_to_expected_six([6 / 45] * 45)
        self.assertAlmostEqual(sum(probs), 6.0, places=9)
        self.assertTrue(all(abs(p - 6 / 45) < 1e-9 for p in probs))

    def test_normalize_expected_six_preserves_order(self):
        raw = [0.05 + i * 0.002 for i in range(45)]
        norm = e072.normalize_to_expected_six(raw)
        self.assertAlmostEqual(sum(norm), 6.0, places=9)
        self.assertTrue(all(norm[i] < norm[i + 1] for i in range(44)))

    def test_tie_rule_assigns_equal_cutpoint_to_higher_bin(self):
        cuts = [0.1, 0.2, 0.3, 0.4]
        self.assertEqual(e072.assign_bin(0.1, cuts), 1)
        self.assertEqual(e072.assign_bin(0.099999, cuts), 0)
        self.assertEqual(e072.assign_bin(0.4, cuts), 4)

    def test_bin_probability_uses_fixed_beta_prior(self):
        scores = [0.0, 0.1, 0.2, 0.3, 0.4]
        labels = [1, 0, 1, 0, 0]
        probs, counts, hits = e072.fit_bin_probabilities(scores, labels, [0.0, 0.1, 0.2, 0.3])
        self.assertEqual(counts, [0, 1, 1, 1, 2])
        self.assertEqual(hits, [0, 1, 0, 1, 0])
        self.assertAlmostEqual(probs[0], 6 / 45)
        self.assertAlmostEqual(probs[2], 6 / 46)

    def test_loss_functions_are_finite(self):
        p = [6 / 45] * 45
        y = [1] * 6 + [0] * 39
        brier, logloss = e072.losses(p, y)
        self.assertTrue(math.isfinite(brier))
        self.assertTrue(math.isfinite(logloss))

    def test_moving_block_bootstrap_is_reproducible(self):
        values = [((i % 7) - 3) / 100 for i in range(150)]
        a = e072.moving_block_ci(values, seed=42, reps=200, block_length=50)
        b = e072.moving_block_ci(values, seed=42, reps=200, block_length=50)
        self.assertEqual(a, b)
        self.assertLessEqual(a["lower"], a["upper"])

    def test_study_is_not_purchase_readiness(self):
        self.assertFalse(e072.TEST_START <= e072.TRAIN_END)
        self.assertEqual(e072.TEST_END, 1250)
        self.assertFalse(e072.STUDY_ID == "")


if __name__ == "__main__":
    unittest.main()
