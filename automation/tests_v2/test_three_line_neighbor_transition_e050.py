"""Frozen E050 neighbor-transition contracts."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import three_line_neighbor_transition_e050 as study
from automation import three_line_bonus_transition_e048 as shared


class ThreeLineNeighborTransitionE050Tests(unittest.TestCase):
    def test_fixed_distance_bins(self):
        previous = (10, 20, 30, 40, 44, 45)
        self.assertEqual(study.distance_bin(previous, 10), 0)
        self.assertEqual(study.distance_bin(previous, 11), 1)
        self.assertEqual(study.distance_bin(previous, 12), 2)
        self.assertEqual(study.distance_bin(previous, 13), 3)
        self.assertEqual(study.distance_bin(previous, 43), 1)
        self.assertEqual(study.distance_bin(previous, 1), 3)

    def test_training_counts_exclude_target_outcome(self):
        draws = [
            {"nums": (1, 2, 3, 4, 5, 6)},
            {"nums": (7, 8, 9, 10, 11, 12)},
            {"nums": (13, 14, 15, 16, 17, 18)},
            {"nums": (19, 20, 21, 22, 23, 24)},
        ]
        exposure_a, hits_a = study.build_training_counts(draws, 4)
        changed_target = [*draws[:-1], {"nums": (40, 41, 42, 43, 44, 45)}]
        exposure_b, hits_b = study.build_training_counts(changed_target, 4)
        self.assertEqual(exposure_a, exposure_b)
        self.assertEqual(hits_a, hits_b)
        self.assertEqual(sum(sum(row) for row in exposure_a), 45 * 2)

    def test_smoothing_formula_is_fixed(self):
        previous = (1, 2, 3, 4, 5, 6)
        exposures = [[0] * 45 for _ in range(4)]
        hits = [[0] * 45 for _ in range(4)]
        exposures[1][6] = 10
        hits[1][6] = 3
        global_counts = [0] * 45
        global_counts[6] = 100
        scores = study.score_numbers(previous, exposures, hits, global_counts, 1000, 60)
        self.assertAlmostEqual(scores[6], (3 + 60 * 0.1) / (10 + 60))

    def test_fixed_portfolio_is_disjoint_union18(self):
        scores = [float(45 - n) for n in range(45)]
        lines = shared.build_portfolio(scores)
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(len(line) == 6 for line in lines))
        self.assertEqual(len(set().union(*(set(line) for line in lines))), 18)

    def test_preregistration_is_frozen_to_active_policy(self):
        prereg = json.loads(study.PREREG_PATH.read_text(encoding="utf-8"))
        policy = json.loads(study.POLICY_PATH.read_text(encoding="utf-8"))
        study.validate_preregistration(prereg, policy)
        self.assertEqual(prereg["random_comparator"]["random_bundles_per_target"], 120)
        self.assertEqual(prereg["inference"]["block_length_targets"], 50)
        self.assertFalse(prereg["portfolio"]["parameter_tuning"])


if __name__ == "__main__":
    unittest.main()
