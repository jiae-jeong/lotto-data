import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import three_line_pair_context_transition_1251_v1 as study


class PairContextTransitionTests(unittest.TestCase):
    def _draws(self):
        return [
            {"round": 1, "nums": (1, 2, 3, 4, 5, 6)},
            {"round": 2, "nums": (1, 2, 7, 8, 9, 10)},
            {"round": 3, "nums": (1, 2, 11, 12, 13, 14)},
            {"round": 4, "nums": (3, 4, 15, 16, 17, 18)},
            {"round": 5, "nums": (5, 6, 19, 20, 21, 22)},
        ]

    def test_unseen_pair_contexts_shrink_to_uniform_inclusion_prior(self):
        previous = (1, 2, 3, 4, 5, 6)
        scores = study.pair_context_scores(previous, Counter(), Counter())
        for value in scores.values():
            self.assertAlmostEqual(value, 6.0 / 45.0, places=14)

    def test_pair_context_counts_stop_at_registered_training_cutoff(self):
        draws = self._draws()
        exposures, successes = study.build_pair_context_counts(draws, through_round=3)
        pair = (1, 2)
        self.assertEqual(exposures[pair], 2)
        self.assertEqual(successes[(pair, 1)], 2)
        self.assertEqual(successes[(pair, 2)], 2)
        self.assertEqual(successes[(pair, 11)], 1)
        self.assertEqual(successes[(pair, 15)], 0)

    def test_future_draw_cannot_change_scores_for_the_same_target(self):
        draws = self._draws()
        exposures, successes = study.build_pair_context_counts(draws, through_round=3)
        previous = draws[2]["nums"]
        before = study.pair_context_scores(previous, exposures, successes)
        changed_future = [dict(item) for item in draws]
        changed_future[3]["nums"] = (20, 21, 22, 23, 24, 25)
        changed_future[4]["nums"] = (30, 31, 32, 33, 34, 35)
        after = study.pair_context_scores(changed_future[2]["nums"], exposures, successes)
        self.assertEqual(before, after)

    def test_three_line_selector_is_deterministic_and_union18(self):
        base = study.load_base()
        scores = {n: float((n * 17) % 47) for n in range(1, 46)}
        first = study.make_three_line_portfolio(scores, base)
        second = study.make_three_line_portfolio(scores, base)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        union = set().union(*(set(line) for line in first))
        self.assertEqual(len(union), 18)
        self.assertTrue(all(len(line) == 6 for line in first))
        self.assertTrue(all(not (set(a) & set(b)) for i, a in enumerate(first) for b in first[i+1:]))


if __name__ == "__main__":
    unittest.main()
