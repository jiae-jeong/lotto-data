import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import three_line_lag2_membership_context_e053_v1 as study


class Lag2MembershipContextE053Tests(unittest.TestCase):
    def _draws(self):
        return [
            {"round": 1, "nums": (1, 2, 3, 4, 5, 6)},
            {"round": 2, "nums": (1, 2, 7, 8, 9, 10)},
            {"round": 3, "nums": (1, 2, 11, 12, 13, 14)},
            {"round": 4, "nums": (3, 4, 15, 16, 17, 18)},
            {"round": 5, "nums": (5, 6, 19, 20, 21, 22)},
        ]

    def test_four_membership_states_are_encoded_without_bonus(self):
        old = (1, 2, 3, 4, 5, 6)
        recent = (1, 2, 7, 8, 9, 10)
        self.assertEqual(study.membership_state(11, old, recent), 0)
        self.assertEqual(study.membership_state(3, old, recent), 2)
        self.assertEqual(study.membership_state(7, old, recent), 1)
        self.assertEqual(study.membership_state(1, old, recent), 3)

    def test_unseen_state_number_pairs_shrink_to_uniform_prior(self):
        exposures = [[0] * 46 for _ in range(4)]
        successes = [[0] * 46 for _ in range(4)]
        scores = study.lag2_scores((1, 2, 3, 4, 5, 6), (7, 8, 9, 10, 11, 12), exposures, successes)
        for value in scores.values():
            self.assertAlmostEqual(value, 6.0 / 45.0, places=14)

    def test_transition_counts_use_only_two_prior_draws(self):
        draws = self._draws()
        exposures3, successes3 = study.build_lag2_counts(draws, through_round=3)
        self.assertEqual(exposures3[3][1], 1)
        self.assertEqual(successes3[3][1], 1)
        exposures4, successes4 = study.build_lag2_counts(draws, through_round=4)
        self.assertEqual(exposures4[3][1], 2)
        self.assertEqual(successes4[3][1], 1)
        # Number 15 is absent from rounds 2 and 3, then appears in round 4.
        self.assertEqual(exposures4[0][15], 2)
        self.assertEqual(successes4[0][15], 1)

    def test_future_outcomes_cannot_change_frozen_prior_counts(self):
        draws = self._draws()
        before = study.build_lag2_counts(draws, through_round=3)
        changed = [dict(item) for item in draws]
        changed[3]["nums"] = (20, 21, 22, 23, 24, 25)
        changed[4]["nums"] = (30, 31, 32, 33, 34, 35)
        after = study.build_lag2_counts(changed, through_round=3)
        self.assertEqual(before, after)

    def test_three_line_selector_is_deterministic_and_union18(self):
        base = study.load_base()
        scores = {number: float((number * 17) % 47) for number in range(1, 46)}
        first = study.make_three_line_portfolio(scores, base)
        second = study.make_three_line_portfolio(scores, base)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        union = set().union(*(set(line) for line in first))
        self.assertEqual(len(union), 18)
        self.assertTrue(all(len(line) == 6 for line in first))
        self.assertTrue(all(not (set(a) & set(b)) for i, a in enumerate(first) for b in first[i+1:]))

    def test_preregistration_matches_frozen_three_line_policy(self):
        prereg = json.loads(study.PREREG_PATH.read_text(encoding="utf-8"))
        policy = json.loads(study.POLICY_PATH.read_text(encoding="utf-8"))
        study._verify_preregistration(prereg, policy)
        self.assertEqual(prereg["target_rounds"], "401..1250 inclusive")
        self.assertEqual(prereg["estimator"]["prior_strength"], 45)
        self.assertIs(prereg["estimator"]["parameter_search"], False)


if __name__ == "__main__":
    unittest.main()
