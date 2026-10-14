"""Unit and registration guards for the independent five-line research path."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daily_research_v2 as daily
import independent_signal_five_line_v1 as study


class IndependentFiveLineTests(unittest.TestCase):
    def test_registered_queue_has_new_order_without_relabeling_e019(self):
        queue = json.loads((Path(__file__).resolve().parents[1] / "research_queue_v2.json").read_text(encoding="utf-8"))
        ids = [task["id"] for task in queue["tasks"]]
        expected_prior = study.__dict__.get("TASK_IDS", [
            "E025_INDEPENDENT_SIGNAL_DISCOVERY_v1", "E026_INDEPENDENT_MODEL_WALKFORWARD_v1",
            "E027_FIVE_LINE_CANDIDATE_BANK_v1", "E028_FIVE_LINE_PORTFOLIO_SELECTOR_v2",
            "E029_FIVE_LINE_PROMOTION_GATE_v2"])
        self.assertEqual(ids[-18:-13], expected_prior)
        self.assertEqual(ids[-13:-7], [
            "E030_PROSPECTIVE_SIGNAL_FREEZE_v1",
            "E031_ORTHOGONAL_SIGNAL_DISCOVERY_v2",
            "E032_FALSE_DISCOVERY_NEGATIVE_CONTROL_v1",
            "E033_ORTHOGONAL_SIGNAL_WALKFORWARD_v1",
            "E034_SINGLE_EDGE_PROMOTION_GATE_v1",
            "E035_FIVE_LINE_REBUILD_GATE_v1",
        ])
        self.assertEqual(ids[-7:], [
            "E036_NULL_GATE_CALIBRATION_v2", "E037_PREDICTABILITY_FALSIFICATION_v1",
            "E038_ORTHOGONAL_SIGNAL_DISCOVERY_v3", "E039_ORTHOGONAL_WALKFORWARD_CONFIRMATION_v2",
            "E040_SINGLE_EDGE_PROMOTION_GATE_v2", "E041_FIVE_LINE_PORTFOLIO_REBUILD_v2",
            "E042_FIVE_LINE_PROMOTION_AND_PROSPECTIVE_FREEZE_v1",
        ])
        self.assertEqual(ids[ids.index("E019_THREE_TICKET_PORTFOLIO_COVERAGE_v1")],
                         "E019_THREE_TICKET_PORTFOLIO_COVERAGE_v1")
        for task in queue["tasks"][-18:-13]: daily._validate_task(task)
        for task in queue["tasks"][-7:]: daily._validate_task(task)

    def test_season_and_fixed_sum_regimes_are_predefined(self):
        self.assertEqual([study._season(m) for m in (1, 4, 7, 10)], ["winter", "spring", "summer", "autumn"])
        self.assertEqual([study._sum_regime(x) for x in (119, 120, 144, 145, 169, 170)], [0, 1, 1, 2, 2, 3])

    def test_lower_number_breaks_score_ties(self):
        scores = {n: 1.0 for n in range(1, 46)}
        self.assertEqual(study._top_ticket(scores), (1, 2, 3, 4, 5, 6))

    def test_fixed_portfolio_strategies_return_five_distinct_candidates(self):
        candidates = []
        for i in range(12):
            candidates.append({"candidate_id": f"C{i:02}", "numbers": tuple(range(i + 1, i + 7)),
                "source_model": f"M{i}", "source_models": f"M{i}",
                "source_family": "INDEPENDENT" if i >= 8 else "B", "candidate_score": 1 - i / 100,
                "candidate_score_rank": i + 1, "eligible_independent": i >= 8})
        for strategy in study.FIXED_STRATEGIES:
            result = study._select_portfolio(strategy, candidates)
            self.assertEqual(len(result), 5, strategy)
            self.assertEqual(len({x["candidate_id"] for x in result}), 5, strategy)

    def test_block_bootstrap_is_reproducible_and_reports_uncertainty(self):
        values = [0.1, -0.2, 0.3, 0.0] * 10
        a = study._block_bootstrap(values, 20261015, reps=120, block=4)
        b = study._block_bootstrap(values, 20261015, reps=120, block=4)
        self.assertEqual(a, b)
        self.assertLessEqual(a["ci95_low"], a["estimate"] + 1e-12)
        self.assertGreaterEqual(a["ci95_high"] + 1e-12, a["estimate"])

    def test_holm_stepdown_is_monotone(self):
        rows = [{"p_raw": p} for p in (0.01, 0.03, 0.04)]
        study._holm(rows)
        adjusted = [r["p_holm"] for r in rows]
        self.assertEqual(adjusted, sorted(adjusted))
        self.assertTrue(all(x <= 1 for x in adjusted))


if __name__ == "__main__":
    unittest.main()
