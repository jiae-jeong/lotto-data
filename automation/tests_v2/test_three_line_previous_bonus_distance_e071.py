import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import three_line_previous_bonus_distance_e071 as study


def synthetic_draws():
    return [
        {"round": 1, "nums": (1, 2, 3, 4, 5, 6), "bonus": 7},
        {"round": 2, "nums": (2, 3, 4, 5, 6, 7), "bonus": 8},
        {"round": 3, "nums": (3, 4, 5, 6, 7, 8), "bonus": 9},
        {"round": 4, "nums": (4, 5, 6, 7, 8, 9), "bonus": 10},
        {"round": 5, "nums": (5, 6, 7, 8, 9, 10), "bonus": 11},
    ]


class PreviousBonusDistanceE071Tests(unittest.TestCase):
    def test_fixed_distance_bin_boundaries(self):
        self.assertEqual([study.distance_bin(x) for x in (0, 5, 6, 10, 11, 17, 18, 25, 26, 44)],
                         [0, 0, 1, 1, 2, 2, 3, 3, 4, 4])
        for invalid in (-1, 45):
            with self.assertRaises(ValueError):
                study.distance_bin(invalid)

    def test_bins_are_theoretical_not_sample_tuned(self):
        audit = study.theoretical_distance_audit()
        self.assertEqual(audit["ordered_pairs"], 2025)
        self.assertEqual(audit["cutpoints"], [5, 10, 17, 25])
        self.assertEqual(audit["cumulative_counts"], [465, 835, 1269, 1645])
        self.assertEqual(audit["bin_counts"], [465, 370, 434, 376, 380])

    def test_training_counts_use_only_pre_target_transitions(self):
        draws = synthetic_draws()
        exposures, successes = study.build_training_counts(draws, 4)
        self.assertEqual(sum(exposures[b][7] for b in range(5)), 2)
        self.assertEqual(exposures[0][7], 2)
        self.assertEqual(successes[0][7], 2)
        self.assertEqual(exposures[1][1], 2)
        self.assertEqual(successes[1][1], 0)
        self.assertEqual(exposures[0][2], 1)
        self.assertEqual(successes[0][2], 1)

    def test_target_scores_are_invariant_to_target_and_future_outcomes(self):
        draws = synthetic_draws()
        scores_a, bins_a, bonus_a = study.score_numbers_for_target(draws, 4)
        altered = [dict(row) for row in draws]
        altered[3]["nums"] = (20, 21, 22, 23, 24, 25)
        altered[3]["bonus"] = 26
        altered[4]["nums"] = (30, 31, 32, 33, 34, 35)
        altered[4]["bonus"] = 36
        scores_b, bins_b, bonus_b = study.score_numbers_for_target(altered, 4)
        self.assertEqual(scores_a, scores_b)
        self.assertEqual(bins_a, bins_b)
        self.assertEqual(bonus_a, bonus_b)

    def test_fixed_uniform_prior_formula(self):
        scores, bins, _ = study.score_numbers_for_target(synthetic_draws(), 4)
        self.assertAlmostEqual(scores[7], (2 + 6) / (2 + 45))
        self.assertEqual(bins[7], 0)

    def test_e045_portfolio_remains_three_disjoint_lines_union18(self):
        base = study.load_base()
        scores = {n: 1.0 / n for n in range(1, 46)}
        lines = study.make_three_line_portfolio(scores, base)
        self.assertEqual(len(lines), 3)
        self.assertEqual(len(set().union(*(set(line) for line in lines))), 18)
        self.assertTrue(all(len(line) == 6 for line in lines))
        self.assertTrue(all(not (set(lines[i]) & set(lines[j]))
                            for i in range(3) for j in range(i + 1, 3)))

    def test_frozen_preregistration_matches_unchanged_policy(self):
        root = Path(__file__).resolve().parents[2]
        prereg = json.loads((root / study.PREREG_REL).read_text(encoding="utf-8"))
        policy = json.loads((root / study.POLICY_REL).read_text(encoding="utf-8"))
        study.validate_preregistration(prereg, policy)


if __name__ == "__main__":
    unittest.main()
