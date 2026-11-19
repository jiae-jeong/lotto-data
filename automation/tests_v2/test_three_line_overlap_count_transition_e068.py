import importlib.util
import json
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "automation" / "three_line_overlap_count_transition_e068.py"
SPEC = importlib.util.spec_from_file_location("e068_runner_test", RUNNER)
E068 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E068)
BASE = E068.load_base()


def fake_draw(round_no, nums):
    return {"round": round_no, "nums": tuple(sorted(nums))}


class OverlapCountTransitionE068Tests(unittest.TestCase):
    def test_overlap_count_state_uses_three_frozen_bins(self):
        two_back = (1, 2, 3, 4, 5, 6)
        self.assertEqual(E068.overlap_count_state(two_back, (7, 8, 9, 10, 11, 12)), 0)
        self.assertEqual(E068.overlap_count_state(two_back, (1, 7, 8, 9, 10, 11)), 1)
        self.assertEqual(E068.overlap_count_state(two_back, (1, 2, 8, 9, 10, 11)), 2)
        self.assertEqual(E068.overlap_count_state(two_back, (1, 2, 3, 4, 5, 6)), 2)

    def test_overlap_count_state_rejects_invalid_draws(self):
        with self.assertRaises(ValueError):
            E068.overlap_count_state((1, 2, 3, 4, 5, 5), (1, 7, 8, 9, 10, 11))
        with self.assertRaises(ValueError):
            E068.overlap_count_state((0, 2, 3, 4, 5, 6), (1, 7, 8, 9, 10, 11))

    def test_hamming_distance_is_fixed_to_one_component(self):
        self.assertEqual(E068.hamming_distance(0, 2), 1)
        self.assertEqual(E068.hamming_distance(1, 1), 0)
        with self.assertRaises(ValueError):
            E068.hamming_distance(0, 3)

    def test_frozen_blob_hashes_match_preregistration(self):
        prereg = json.loads((ROOT / E068.PREREG_REL).read_text(encoding="utf-8"))
        self.assertEqual(E068.verify_frozen_blobs(prereg), prereg["frozen_blobs"])

    def test_transition_updates_45_exposures_and_six_successes(self):
        two_back = (1, 2, 4, 9, 17, 30)
        previous = (2, 4, 8, 12, 16, 20)
        outcome = (3, 8, 14, 22, 35, 44)
        exposures, successes = {}, {}
        E068.update_transition(two_back, previous, outcome, exposures, successes)
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
        exp_a, hit_a = E068.build_training_counts(draws, 5)
        mutated = list(draws)
        mutated[4] = fake_draw(5, (1, 3, 5, 7, 9, 11))
        exp_b, hit_b = E068.build_training_counts(mutated, 5)
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
        scores_before, lines_before = E068.score_target(draws, 5, BASE)
        mutated = list(draws)
        mutated[4] = fake_draw(5, (1, 3, 5, 7, 9, 11))
        mutated[5] = fake_draw(6, (2, 4, 6, 8, 10, 12))
        mutated[6] = fake_draw(7, (13, 15, 17, 19, 21, 23))
        scores_after, lines_after = E068.score_target(mutated, 5, BASE)
        self.assertEqual(scores_before, scores_after)
        self.assertEqual(lines_before, lines_after)

    def test_three_line_portfolio_is_deterministic_and_union18(self):
        scores = {n: 1.0 / (n + 1) for n in range(1, 46)}
        first = E068.make_three_line_portfolio(scores, BASE)
        second = E068.make_three_line_portfolio(scores, BASE)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertEqual(len(set().union(*(set(x) for x in first))), 18)
        self.assertTrue(all(len(line) == 6 for line in first))
        self.assertTrue(all(not (set(a) & set(b)) for i, a in enumerate(first) for b in first[i + 1:]))

    def test_random_label_permutation_preserves_geometry(self):
        lines = E068.make_three_line_portfolio({n: 1.0 / (n + 1) for n in range(1, 46)}, BASE)
        permuted = BASE.permute_portfolio_labels(lines, random.Random(20261117068))
        self.assertEqual(len(set().union(*(set(x) for x in permuted))), 18)
        self.assertTrue(all(not (set(a) & set(b)) for i, a in enumerate(permuted) for b in permuted[i + 1:]))


if __name__ == "__main__":
    unittest.main()
