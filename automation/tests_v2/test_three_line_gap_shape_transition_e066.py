import importlib.util
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "automation" / "three_line_gap_shape_transition_e066.py"
SPEC = importlib.util.spec_from_file_location("e066_runner_test", RUNNER)
E066 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E066)
BASE = E066.load_base()


def fake_draw(round_no, nums):
    return {"round": round_no, "nums": tuple(sorted(nums))}


class GapShapeTransitionE066Tests(unittest.TestCase):
    def test_gap_shape_state_uses_five_frozen_components(self):
        previous = (1, 2, 4, 9, 17, 30)
        self.assertEqual(E066.gap_shape_state(previous), (0, 2, 1, 2, 2))

    def test_gap_shape_state_rejects_invalid_draw(self):
        with self.assertRaises(ValueError):
            E066.gap_shape_state((1, 2, 3, 4, 5, 5))
        with self.assertRaises(ValueError):
            E066.gap_shape_state((0, 2, 3, 4, 5, 6))

    def test_hamming_distance_is_fixed_to_five_components(self):
        self.assertEqual(E066.hamming_distance((0, 1, 2, 0, 1), (0, 2, 2, 1, 1)), 2)
        with self.assertRaises(ValueError):
            E066.hamming_distance((0, 1), (0, 1))

    def test_transition_updates_45_exposures_and_six_successes(self):
        previous = (1, 2, 4, 9, 17, 30)
        outcome = (3, 8, 14, 22, 35, 44)
        exposures, successes = {}, {}
        E066.update_transition(previous, outcome, exposures, successes)
        self.assertEqual(sum(sum(row) for row in exposures.values()), 45)
        self.assertEqual(sum(sum(row) for row in successes.values()), 6)

    def test_training_counts_exclude_target_outcome(self):
        draws = [
            fake_draw(1, (1, 2, 3, 4, 5, 6)),
            fake_draw(2, (7, 8, 9, 10, 11, 12)),
            fake_draw(3, (13, 14, 15, 16, 17, 18)),
            fake_draw(4, (19, 20, 21, 22, 23, 24)),
            fake_draw(5, (25, 26, 27, 28, 29, 30)),
        ]
        exp_a, hit_a = E066.build_training_counts(draws, 5)
        mutated = list(draws)
        mutated[4] = fake_draw(5, (1, 3, 5, 7, 9, 11))
        exp_b, hit_b = E066.build_training_counts(mutated, 5)
        self.assertEqual(exp_a, exp_b)
        self.assertEqual(hit_a, hit_b)

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
        scores_before, lines_before = E066.score_target(draws, 5, BASE)
        mutated = list(draws)
        mutated[4] = fake_draw(5, (1, 3, 5, 7, 9, 11))
        mutated[5] = fake_draw(6, (2, 4, 6, 8, 10, 12))
        mutated[6] = fake_draw(7, (13, 15, 17, 19, 21, 23))
        scores_after, lines_after = E066.score_target(mutated, 5, BASE)
        self.assertEqual(scores_before, scores_after)
        self.assertEqual(lines_before, lines_after)

    def test_three_line_portfolio_is_deterministic_and_union18(self):
        scores = {n: 1.0 / (n + 1) for n in range(1, 46)}
        first = E066.make_three_line_portfolio(scores, BASE)
        second = E066.make_three_line_portfolio(scores, BASE)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertEqual(len(set().union(*(set(x) for x in first))), 18)
        self.assertTrue(all(len(line) == 6 for line in first))
        self.assertTrue(all(not (set(a) & set(b)) for i, a in enumerate(first) for b in first[i + 1:]))

    def test_random_label_permutation_preserves_geometry(self):
        lines = E066.make_three_line_portfolio({n: 1.0 / (n + 1) for n in range(1, 46)}, BASE)
        permuted = BASE.permute_portfolio_labels(lines, random.Random(20261117066))
        self.assertEqual(len(set().union(*(set(x) for x in permuted))), 18)
        self.assertTrue(all(not (set(a) & set(b)) for i, a in enumerate(permuted) for b in permuted[i + 1:]))


if __name__ == "__main__":
    unittest.main()
