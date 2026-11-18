from __future__ import annotations

import unittest

from automation.three_line_three_draw_membership_count_e073 import (
    BASE_RATE,
    PRIOR_STRENGTH,
    build_lag3_counts,
    lag3_scores,
    membership_state,
    update_lag3_counts,
)


class ThreeDrawMembershipCountE073Tests(unittest.TestCase):
    def test_membership_state_counts_zero_through_three(self):
        three_back = {1, 2, 3, 4, 5, 6}
        two_back = {1, 2, 7, 8, 9, 10}
        previous = {1, 11, 12, 13, 14, 15}
        self.assertEqual(membership_state(16, three_back, two_back, previous), 0)
        self.assertEqual(membership_state(3, three_back, two_back, previous), 1)
        self.assertEqual(membership_state(7, three_back, two_back, previous), 1)
        self.assertEqual(membership_state(2, three_back, two_back, previous), 2)
        self.assertEqual(membership_state(1, three_back, two_back, previous), 3)

    def test_update_records_45_exposures_and_six_successes(self):
        three_back = {1, 2, 3, 4, 5, 6}
        two_back = {1, 2, 7, 8, 9, 10}
        previous = {1, 11, 12, 13, 14, 15}
        outcome = {16, 17, 18, 19, 20, 21}
        exposures = [[0] * 46 for _ in range(4)]
        successes = [[0] * 46 for _ in range(4)]
        update_lag3_counts(three_back, two_back, previous, outcome, exposures, successes)
        self.assertEqual(sum(sum(row) for row in exposures), 45)
        self.assertEqual(sum(sum(row) for row in successes), 6)
        self.assertEqual(exposures[3][1], 1)
        self.assertEqual(exposures[2][2], 1)
        self.assertEqual(exposures[1][3], 1)
        self.assertEqual(exposures[0][16], 1)
        self.assertEqual(successes[0][16], 1)

    def test_build_counts_uses_only_outcomes_through_registered_cutoff(self):
        draws = [
            {"nums": tuple(range(1, 7))},
            {"nums": tuple(range(7, 13))},
            {"nums": tuple(range(13, 19))},
            {"nums": tuple(range(19, 25))},
            {"nums": tuple(range(25, 31))},
            {"nums": tuple(range(31, 37))},
            {"nums": tuple(range(37, 43))},
        ]
        first = build_lag3_counts(draws, 6)
        mutated_future = [dict(row) for row in draws]
        mutated_future[6] = {"nums": (1, 2, 3, 4, 5, 6)}
        second = build_lag3_counts(mutated_future, 6)
        self.assertEqual(first, second)
        self.assertEqual(sum(sum(row) for row in first[0]), 45 * 3)
        self.assertEqual(sum(sum(row) for row in first[1]), 6 * 3)

    def test_scores_use_fixed_beta_smoothing_and_four_states(self):
        exposures = [[0] * 46 for _ in range(4)]
        successes = [[0] * 46 for _ in range(4)]
        exposures[3][1] = 10
        successes[3][1] = 4
        scores = lag3_scores({1}, {1}, {1}, exposures, successes)
        expected = (4 + PRIOR_STRENGTH * BASE_RATE) / (10 + PRIOR_STRENGTH)
        self.assertAlmostEqual(scores[1], expected, places=14)
        self.assertEqual(len(scores), 45)

    def test_invalid_candidate_or_draw_is_rejected(self):
        with self.assertRaises(ValueError):
            membership_state(46, set(), set(), set())
        exposures = [[0] * 46 for _ in range(4)]
        successes = [[0] * 46 for _ in range(4)]
        with self.assertRaises(ValueError):
            update_lag3_counts({1, 2}, {3, 4, 5, 6}, {7, 8, 9, 10, 11, 12}, {13, 14, 15, 16, 17, 18}, exposures, successes)


if __name__ == "__main__":
    unittest.main()
