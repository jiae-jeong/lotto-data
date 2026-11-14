import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "three_line_bonus_transition_e048.py"
SPEC = importlib.util.spec_from_file_location("e048_runner", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class E048FrozenSpecificationTests(unittest.TestCase):
    def test_rank_interleaving_creates_exact_union18(self):
        scores = [float(46 - n) for n in range(1, 46)]
        lines = MODULE.build_portfolio(scores)
        MODULE.validate_portfolio(lines)
        self.assertEqual(len(lines), 3)
        self.assertEqual([len(line) for line in lines], [6, 6, 6])
        self.assertEqual(len(set().union(*(set(line) for line in lines))), 18)

    def test_portfolio_builder_is_deterministic(self):
        scores = [float((n * 17) % 23) for n in range(1, 46)]
        self.assertEqual(MODULE.build_portfolio(scores), MODULE.build_portfolio(scores))

    def test_label_permutation_preserves_three_line_geometry(self):
        lines = [(1, 4, 7, 10, 13, 16), (2, 5, 8, 11, 14, 17), (3, 6, 9, 12, 15, 18)]
        randomized = MODULE.permute_portfolio_labels(lines, __import__("random").Random(2026111402))
        MODULE.validate_portfolio(randomized)
        self.assertEqual(len(set().union(*(set(line) for line in randomized))), 18)

    def test_metrics_are_computed_at_portfolio_level(self):
        lines = [(1, 2, 3, 4, 5, 6), (7, 8, 9, 10, 11, 12), (13, 14, 15, 16, 17, 18)]
        result = MODULE.portfolio_metrics(lines, {1, 2, 8, 14, 15, 20})
        self.assertEqual(result["max_hits"], 2)
        self.assertEqual(result["any2"], 1)
        self.assertEqual(result["any3"], 0)
        self.assertEqual(result["winning_union_coverage"], 5)

    def test_bonus_conditioned_score_uses_fixed_shrinkage(self):
        global_counts = [1] * 45
        conditional_counts = [[0] * 45 for _ in range(46)]
        conditional_n = [0] * 46
        conditional_n[7] = 2
        conditional_counts[8][0] = 2
        scores = MODULE.score_numbers(8, global_counts, 10, conditional_counts, conditional_n, 60.0)
        self.assertAlmostEqual(scores[0], (2 + 60 * 0.1) / 62)
        self.assertAlmostEqual(scores[1], (0 + 60 * 0.1) / 62)


if __name__ == "__main__":
    unittest.main()
