""""Unit and registration guards for the independent five-line research path."""
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
        expected_e030_e035 = [
            "E030_PROSPECTIVE_SIGNAL_FREEZE_v1",
            "E031_ORTHOGONAL_SIGNAL_DISCOVERY_v2",
            "E032_FALSE_DISCOVERY_NEGATIVE_CONTROL_v1",
            "E033_ORTHOGONAL_SIGNAL_WALKFORWARD_v1",
            "E034_SINGLE_EDGE_PROMOTION_GATE_v1",
            "E035_FIVE_LINE_REBUILD_GATE_v1",
        ]
        expected_e036_e042 = [
            "E036_NULL_GATE_CALIBRATION_v2", "E037_PREDICTABILITY_FALSIFICATION_v1",
            "E038_ORTHOGONAL_SIGNAL_DISCOVERY_v3", "E039_ORTHOGONAL_WALKFORWARD_CONFIRMATION_v2",
            "E040_SINGLE_EDGE_PROMOTION_GATE_v2", "E041_FIVE_LINE_PORTFOLIO_REBUILD_v2",
            "E042_FIVE_LINE_PROMOTION_AND_PROSPECTIVE_FREEZE_v1",
        ]
        prior_start = ids.index(expected_prior[0])
        e030_start = ids.index(expected_e030_e035[0])
        e036_start = ids.index(expected_e036_e042[0])
        self.assertEqual(ids[prior_start:prior_start + len(expected_prior)], expected_prior)
        self.assertEqual(ids[e030_start:e030_start + len(expected_e030_e035)], expected_e030_e035)
        self.assertEqual(ids[e036_start:e036_start + len(expected_e036_e042)], expected_e036_e042)
        self.assertLess(prior_start, e030_start)
        self.assertLess(e030_start, e036_start)
        expected_e043_e050 = [
            "E043_H1250_A_FIXED_BANK_ALLOCATOR_v1",
            "E044_H1250_B_DYNAMIC_CANDIDATE_RANKING_v1",
            "E044_H1250_B_DYNAMIC_CANDIDATE_RANKING_v2",
            "E045_THREE_LINE_DISJOINT_PORTFOLIO_WALKFORWARD_v1",
            "E046_THREE_LINE_PROSPECTIVE_POWER_PLANNING_v1",
            "E048_THREE_LINE_BONUS_TO_MAIN_TRANSITION_v1",
            "E049_THREE_LINE_DRAW_STATE_TRANSITION_v1",
            "E050_THREE_LINE_PREVIOUS_MAIN_NEIGHBOR_TRANSITION_v1",
        ]
        self.assertEqual(ids[-len(expected_e043_e050):], expected_e043_e050)
        e046 = next(task for task in queue["tasks"] if task["id"] == "E046_THREE_LINE_PROSPECTIVE_POWER_PLANNING_v1")
        self.assertEqual(e046["execution_status"], "EXECUTED_DESIGN_PLANNING_COMPLETE")
        daily._validate_task(e046)
        e048 = next(task for task in queue["tasks"] if task["id"] == "E048_THREE_LINE_BONUS_TO_MAIN_TRANSITION_v1")
        self.assertIn("bonus number", e048["question"].lower())
        self.assertEqual(ids.count("E048_THREE_LINE_BONUS_TO_MAIN_TRANSITION_v1"), 1)
        e049 = next(task for task in queue["tasks"] if task["id"] == "E049_THREE_LINE_DRAW_STATE_TRANSITION_v1")
        self.assertEqual(e049["kind"], "three_line_draw_state_transition")
        self.assertEqual(e049["execution_entrypoint"], "automation/three_line_draw_state_transition_e049.py")
        self.assertEqual(e049["workflow_entrypoint"], ".github/workflows/target-1251-e049-three-line-draw-state-transition.yml")
        self.assertEqual(e049["preregistration"], "research/weekly_purchase/1251/E049_THREE_LINE_DRAW_STATE_TRANSITION_PREREG_20261114.json")
        self.assertIn(e049["execution_status"], (
            "PREREGISTERED_PENDING_DEDICATED_WORKFLOW",
            "EXECUTED_HISTORICAL_STRICT_FAIL_OUTPUTS_PRESERVED",
            "EXECUTED_HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING",
        ))
        if e049["execution_status"] != "PREREGISTERED_PENDING_DEDICATED_WORKFLOW":
            self.assertEqual(e049["execution_result"]["verification_status"], "PASS")
            self.assertFalse(e049["execution_result"]["strict_pass_ready"])
        e050 = next(task for task in queue["tasks"] if task["id"] == "E050_THREE_LINE_PREVIOUS_MAIN_NEIGHBOR_TRANSITION_v1")
        self.assertEqual(e050["kind"], "three_line_neighbor_transition")
        self.assertEqual(e050["execution_entrypoint"], "automation/three_line_neighbor_transition_e050.py")
        self.assertEqual(e050["workflow_entrypoint"], ".github/workflows/target-1251-e050-three-line-neighbor-transition.yml")
        self.assertEqual(e050["preregistration"], "research/weekly_purchase/1251/E050_THREE_LINE_NEIGHBOR_TRANSITION_PREREG_20261114.json")
        self.assertIn(e050["execution_status"], (
            "PREREGISTERED_PENDING_DEDICATED_WORKFLOW",
            "EXECUTED_HISTORICAL_STRICT_FAIL_OUTPUTS_PRESERVED",
            "EXECUTED_HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING",
        ))
        if e050["execution_status"] != "PREREGISTERED_PENDING_DEDICATED_WORKFLOW":
            self.assertEqual(e050["execution_result"]["verification_status"], "PASS")
            self.assertFalse(e050["execution_result"]["strict_pass_ready"])
        self.assertEqual(ids[ids.index("E019_THREE_TICKET_PORTFOLIO_COVERAGE_v1")],
                         "E019_THREE_TICKET_PORTFOLIO_COVERAGE_v1")
        for task in queue["tasks"][prior_start:prior_start + len(expected_prior)]: daily._validate_task(task)
        for task in queue["tasks"][e036_start:e036_start + len(expected_e036_e042)]: daily._validate_task(task)

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
                "source_model": f"M{i}", "source_models": f"M{i}", "source_family": "INDEPENDENT" if i >= 8 else "B",
                "candidate_score": 1 - i / 100, "candidate_score_rank": i + 1, "eligible_independent": i >= 8})
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
