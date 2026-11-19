import itertools
import random
import unittest

from automation import three_line_research_1251_e075_corrected_v1 as e075


class E075SelectorOrderAuditTests(unittest.TestCase):
    def test_consecutive_pairs_are_permutation_invariant(self):
        ticket = (14, 25, 26, 27, 28, 40)
        expected = 3
        for permutation in itertools.permutations(ticket):
            self.assertEqual(e075.consecutive_pairs(permutation), expected)

    def test_legacy_score_order_can_miss_sorted_consecutive_pairs(self):
        score_order = (25, 40, 28, 26, 27, 14)
        legacy_count = sum(b - a == 1 for a, b in zip(score_order, score_order[1:]))
        sorted_count = e075.consecutive_pairs(score_order)
        self.assertEqual(legacy_count, 1)
        self.assertEqual(sorted_count, 3)

    def test_candidate_pool_is_unchanged_by_correction(self):
        role = {n: ((n * 17) % 101) / 101 for n in range(1, 46)}
        global_score = {n: ((n * 29) % 103) / 103 for n in range(1, 46)}
        used = {2, 11, 19, 35, 44}
        _, _, legacy_pool = e075.choose_disjoint_ticket_legacy(role, global_score, used)
        _, corrected_pool = e075.choose_disjoint_ticket(role, global_score, used)
        self.assertEqual(legacy_pool, corrected_pool)

    def test_sorted_ticket_tie_break_is_reproducible(self):
        role = {n: 1.0 for n in range(1, 46)}
        rng = random.Random(99)
        global_score = {n: rng.random() for n in range(1, 46)}
        legacy_ticket, _, legacy_pool = e075.choose_disjoint_ticket_legacy(role, global_score, set())
        corrected_ticket, corrected_pool = e075.choose_disjoint_ticket(role, global_score, set())
        self.assertEqual(legacy_pool, corrected_pool)
        self.assertEqual(legacy_ticket, (8, 10, 15, 25, 34, 41))
        self.assertEqual(corrected_ticket, (5, 8, 15, 23, 34, 44))
        self.assertEqual(corrected_ticket, tuple(sorted(corrected_ticket)))

    def test_label_permutation_preserves_union18_geometry(self):
        lines = [(1, 2, 3, 4, 5, 6), (7, 8, 9, 10, 11, 12), (13, 14, 15, 16, 17, 18)]
        mapping = e075.random_label_mapping(random.Random(20261119))
        transformed = e075.apply_label_mapping(lines, mapping)
        self.assertEqual(len(set().union(*(set(x) for x in transformed))), 18)
        self.assertTrue(all(len(x) == 6 for x in transformed))
        self.assertTrue(all(not (set(transformed[i]) & set(transformed[j]))
                            for i in range(3) for j in range(i + 1, 3)))


if __name__ == "__main__":
    unittest.main()
