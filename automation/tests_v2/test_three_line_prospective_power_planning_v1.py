import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "three_line_prospective_power_planning_v1.py"
SPEC = importlib.util.spec_from_file_location("three_line_prospective_power_planning_v1", MODULE_PATH)
STUDY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(STUDY)


class ThreeLineProspectivePowerPlanningTests(unittest.TestCase):
    def test_final_remainder_is_retained(self):
        self.assertEqual(STUDY.block_lengths(125), [50, 50, 25])
        self.assertEqual(STUDY.block_lengths(100), [50, 50])

    def test_effective_block_count_uses_remainder_weight(self):
        lengths = [50, 50, 25]
        expected = 1.0 / ((50 / 125) ** 2 + (50 / 125) ** 2 + (25 / 125) ** 2)
        self.assertAlmostEqual(STUDY.effective_block_count(lengths), expected, places=12)

    def test_binomial_tail_is_exact(self):
        self.assertAlmostEqual(STUDY.binomial_tail(4, 0.5, 3), 5 / 16, places=12)

    def test_design_grid_is_planning_only_and_retains_remainder(self):
        block_sd = {
            "max_hits": 0.1,
            "any2": 0.1,
            "any3": 0.05,
            "winning_union_coverage": 0.2,
        }
        rows = STUDY.design_grid(block_sd)
        self.assertEqual(len(rows), len(STUDY.TARGET_COUNTS) * len(STUDY.EFFECT_SIZES))
        row = next(
            x for x in rows
            if x["prospective_target_count"] == 125
            and x["standardized_effect_size_d"] == 0.5
        )
        self.assertEqual(row["final_remainder_length"], 25)
        self.assertEqual(row["block_count_including_remainder"], 3)
        for key in (
            "max_hits_ci_power_approx",
            "any2_ci_power_approx",
            "any3_ci_power_approx",
            "winning_union_coverage_ci_power_approx",
            "any2_block_share_gate_probability",
            "joint_power_independence_approx",
            "joint_power_conservative_union_lower",
        ):
            self.assertGreaterEqual(row[key], 0.0)
            self.assertLessEqual(row[key], 1.0)


if __name__ == "__main__":
    unittest.main()
