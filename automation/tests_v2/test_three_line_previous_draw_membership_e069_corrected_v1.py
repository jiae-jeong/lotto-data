import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "automation" / "three_line_previous_draw_membership_e069_corrected_v1.py"
SPEC = importlib.util.spec_from_file_location("e069_corrected_runner_test", RUNNER)
CORRECTED = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CORRECTED)
ORIGINAL = CORRECTED.load_module(CORRECTED.ORIGINAL_RUNNER_REL, "e069_original_for_corrected_test")
BASE = ORIGINAL.load_base()


def fake_draw(round_no, nums):
    return {"round": round_no, "nums": tuple(sorted(nums))}


class E069CorrectiveFixedPriorTests(unittest.TestCase):
    def test_score_uses_exact_fixed_six_over_45_prior(self):
        previous = (1, 2, 3, 4, 5, 6)
        exposures = [[0] * 46 for _ in range(2)]
        successes = [[0] * 46 for _ in range(2)]
        exposures[1][1], successes[1][1] = 10, 3
        exposures[0][7], successes[0][7] = 20, 4
        scores = CORRECTED.score_numbers(previous, exposures, successes)
        self.assertAlmostEqual(scores[1], (3 + 6) / (10 + 45))
        self.assertAlmostEqual(scores[7], (4 + 6) / (20 + 45))
        self.assertAlmostEqual(scores[8], 6 / 45)

    def test_candidate_membership_selects_the_correct_transition_state(self):
        previous = (1, 10, 21, 32, 43, 45)
        exposures = [[0] * 46 for _ in range(2)]
        successes = [[0] * 46 for _ in range(2)]
        exposures[1][1], successes[1][1] = 9, 2
        exposures[0][11], successes[0][11] = 18, 5
        scores = CORRECTED.score_numbers(previous, exposures, successes)
        self.assertAlmostEqual(scores[1], (2 + 6) / (9 + 45))
        self.assertAlmostEqual(scores[11], (5 + 6) / (18 + 45))

    def test_target_and_future_outcome_mutations_do_not_change_target_scores(self):
        draws = [
            fake_draw(1, (1, 2, 3, 4, 5, 6)),
            fake_draw(2, (7, 8, 9, 10, 11, 12)),
            fake_draw(3, (13, 14, 15, 16, 17, 18)),
            fake_draw(4, (19, 20, 21, 22, 23, 24)),
            fake_draw(5, (25, 26, 27, 28, 29, 30)),
            fake_draw(6, (31, 32, 33, 34, 35, 36)),
            fake_draw(7, (37, 38, 39, 40, 41, 42)),
        ]
        scores_before, lines_before = CORRECTED.score_target(draws, 5, ORIGINAL, BASE)
        mutated = list(draws)
        mutated[4] = fake_draw(5, (1, 3, 5, 7, 9, 11))
        mutated[5] = fake_draw(6, (2, 4, 6, 8, 10, 12))
        mutated[6] = fake_draw(7, (13, 15, 17, 19, 21, 23))
        scores_after, lines_after = CORRECTED.score_target(mutated, 5, ORIGINAL, BASE)
        self.assertEqual(scores_before, scores_after)
        self.assertEqual(lines_before, lines_after)

    def test_corrected_three_line_portfolio_is_deterministic_union18(self):
        exposures = [[0] * 46 for _ in range(2)]
        successes = [[0] * 46 for _ in range(2)]
        scores = CORRECTED.score_numbers((1, 2, 3, 4, 5, 6), exposures, successes)
        first = ORIGINAL.make_three_line_portfolio(scores, BASE)
        second = ORIGINAL.make_three_line_portfolio(scores, BASE)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertEqual(len(set().union(*(set(line) for line in first))), 18)
        self.assertTrue(all(len(line) == 6 for line in first))
        self.assertTrue(all(
            not (set(a) & set(b))
            for i, a in enumerate(first)
            for b in first[i + 1:]
        ))


if __name__ == "__main__":
    unittest.main()
