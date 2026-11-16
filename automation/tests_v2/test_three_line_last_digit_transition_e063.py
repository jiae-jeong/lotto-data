import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "automation" / "three_line_last_digit_transition_e063.py"
SPEC = importlib.util.spec_from_file_location("e063_runner_test", RUNNER)
E063 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E063)
BASE = E063.load_base()


def fake_draw(round_no, nums):
    return {"round": round_no, "nums": tuple(sorted(nums))}


class LastDigitTransitionE063Tests(unittest.TestCase):
    def test_last_digit_occupancy_is_candidate_specific(self):
        previous = (1, 10, 21, 32, 43, 45)
        self.assertEqual(E063.last_digit_occupancy(previous, 1), 2)
        self.assertEqual(E063.last_digit_occupancy(previous, 11), 2)
        self.assertEqual(E063.last_digit_occupancy(previous, 20), 1)
        self.assertEqual(E063.last_digit_occupancy(previous, 45), 1)

    def test_transition_updates_one_state_per_candidate_and_six_successes(self):
        previous = (1, 10, 21, 32, 43, 45)
        outcome = (2, 11, 19, 28, 34, 40)
        exposures = [[0] * 46 for _ in range(7)]
        successes = [[0] * 46 for _ in range(7)]
        E063.update_transition(previous, outcome, exposures, successes)
        self.assertEqual(sum(sum(row) for row in exposures), 45)
        self.assertEqual(sum(sum(row) for row in successes), 6)

    def test_target_score_is_invariant_to_target_and_future_outcome_mutations(self):
        draws = [
            fake_draw(1, (1, 2, 3, 4, 5, 6)),
            fake_draw(2, (7, 8, 9, 10, 11, 12)),
            fake_draw(3, (13, 14, 15, 16, 17, 18)),
            fake_draw(4, (19, 20, 21, 22, 23, 24)),
            fake_draw(5, (25, 26, 27, 28, 29, 30)),
            fake_draw(6, (31, 32, 33, 34, 35, 36)),
            fake_draw(7, (37, 38, 39, 40, 41, 42)),
        ]
        scores_before, lines_before = E063.score_target(draws, 5, BASE)
        mutated = list(draws)
        mutated[4] = fake_draw(5, (1, 3, 5, 7, 9, 11))
        mutated[5] = fake_draw(6, (2, 4, 6, 8, 10, 12))
        mutated[6] = fake_draw(7, (13, 15, 17, 19, 21, 23))
        scores_after, lines_after = E063.score_target(mutated, 5, BASE)
        self.assertEqual(scores_before, scores_after)
        self.assertEqual(lines_before, lines_after)

    def test_three_line_portfolio_is_deterministic_and_union18(self):
        scores = {n: 1.0 / (n + 1) for n in range(1, 46)}
        first = E063.make_three_line_portfolio(scores, BASE)
        second = E063.make_three_line_portfolio(scores, BASE)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertEqual(len(set().union(*(set(x) for x in first))), 18)
        self.assertTrue(all(len(line) == 6 for line in first))
        self.assertTrue(all(not (set(a) & set(b)) for i, a in enumerate(first) for b in first[i + 1:]))

    def test_random_label_permutation_preserves_three_line_geometry(self):
        import random
        lines = E063.make_three_line_portfolio({n: 1.0 / (n + 1) for n in range(1, 46)}, BASE)
        permuted = BASE.permute_portfolio_labels(lines, random.Random(20261116063))
        self.assertEqual(len(set().union(*(set(x) for x in permuted))), 18)
        self.assertTrue(all(not (set(a) & set(b)) for i, a in enumerate(permuted) for b in permuted[i + 1:]))

    def test_training_counts_exclude_target_outcome(self):
        draws = [
            fake_draw(1, (1, 2, 3, 4, 5, 6)),
            fake_draw(2, (7, 8, 9, 10, 11, 12)),
            fake_draw(3, (13, 14, 15, 16, 17, 18)),
            fake_draw(4, (19, 20, 21, 22, 23, 24)),
            fake_draw(5, (25, 26, 27, 28, 29, 30)),
        ]
        exp_a, hit_a = E063.build_training_counts(draws, 5)
        mutated = list(draws)
        mutated[4] = fake_draw(5, (1, 3, 5, 7, 9, 11))
        exp_b, hit_b = E063.build_training_counts(mutated, 5)
        self.assertEqual(exp_a, exp_b)
        self.assertEqual(hit_a, hit_b)


if __name__ == "__main__":
    unittest.main()
