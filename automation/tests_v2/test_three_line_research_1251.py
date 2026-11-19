import importlib.util
import random
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "three_line_research_1251_v1.py"
SPEC = importlib.util.spec_from_file_location("three_line_research_1251_v1", MODULE_PATH)
STUDY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(STUDY)


class ThreeLineResearch1251Tests(unittest.TestCase):
    def make_scores(self):
        role = {n: float(46 - n) for n in range(1, 46)}
        global_score = {n: float((n * 7) % 19) for n in range(1, 46)}
        return role, global_score

    def make_lines(self):
        role, global_score = self.make_scores()
        used = set()
        lines = []
        for _ in range(3):
            line = STUDY.choose_disjoint_ticket(role, global_score, used)
            lines.append(line)
            used.update(line)
        return lines

    def test_three_lines_are_pairwise_disjoint_union18(self):
        lines = self.make_lines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(len(line) == 6 and len(set(line)) == 6 for line in lines))
        self.assertEqual(len(set().union(*(set(line) for line in lines))), 18)
        for i in range(3):
            for j in range(i + 1, 3):
                self.assertFalse(set(lines[i]) & set(lines[j]))

    def test_ticket_selection_is_deterministic(self):
        role, global_score = self.make_scores()
        first = STUDY.choose_disjoint_ticket(role, global_score, set())
        second = STUDY.choose_disjoint_ticket(role, global_score, set())
        self.assertEqual(first, second)

    def test_random_label_permutation_preserves_geometry(self):
        lines = self.make_lines()
        permuted = STUDY.permute_portfolio_labels(lines, random.Random(20261114))
        self.assertEqual(len(set().union(*(set(line) for line in permuted))), 18)
        for i in range(3):
            for j in range(i + 1, 3):
                self.assertFalse(set(permuted[i]) & set(permuted[j]))

    def test_metrics_use_max_hit_and_union_coverage(self):
        lines = [
            (1, 2, 3, 4, 5, 6),
            (7, 8, 9, 10, 11, 12),
            (13, 14, 15, 16, 17, 18),
        ]
        result = STUDY.portfolio_metrics(lines, {1, 7, 13, 19, 20, 21})
        self.assertEqual(result["max_hits"], 1)
        self.assertEqual(result["any2"], 0)
        self.assertEqual(result["any3"], 0)
        self.assertEqual(result["winning_union_coverage"], 3)
        self.assertEqual(result["union_size"], 18)

    def test_block_stability_keeps_final_remainder(self):
        blocks = STUDY.block_slices([float(i) for i in range(849)], 50)
        self.assertEqual(len(blocks), 17)
        self.assertEqual([len(x) for x in blocks[:16]], [50] * 16)
        self.assertEqual(len(blocks[-1]), 49)

    def test_moving_block_ci_is_reproducible(self):
        values = [((i * 13) % 17) / 10 for i in range(149)]
        first = STUDY.moving_block_ci(values, 0.0125, 20261114, 250, 50)
        second = STUDY.moving_block_ci(values, 0.0125, 20261114, 250, 50)
        self.assertEqual(first, second)
        self.assertLessEqual(first[0], first[1])

    def test_missing_prospective_rule_never_creates_readiness(self):
        self.assertFalse(STUDY.strict_portfolio_ready(True, None, None))
        self.assertFalse(STUDY.strict_portfolio_ready(True, 1, None))
        self.assertFalse(STUDY.strict_portfolio_ready(False, 1, "one target"))
        self.assertTrue(STUDY.strict_portfolio_ready(True, 1, "one target"))


if __name__ == "__main__":
    unittest.main()
