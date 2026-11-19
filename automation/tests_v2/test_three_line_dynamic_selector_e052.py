import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import three_line_dynamic_selector_e052_v1 as study


class ThreeLineDynamicSelectorE052Tests(unittest.TestCase):
    def test_fixed_tie_break_uses_preregistered_model_order(self):
        rates = {model: 0.5 for model in study.MODEL_ORDER}
        self.assertEqual(study.select_model(rates), study.MODEL_ORDER[0])

    def test_selector_uses_only_the_preceding_100_targets(self):
        self.assertEqual(study.training_window(501, 100), list(range(401, 501)))
        self.assertEqual(study.training_window(700, 100), list(range(600, 700)))
        self.assertNotIn(501, study.training_window(501, 100))

    def test_selector_chooses_highest_trailing_any2_rate(self):
        rates = {model: 0.1 for model in study.MODEL_ORDER}
        rates[study.MODEL_ORDER[3]] = 0.7
        rates[study.MODEL_ORDER[4]] = 0.6
        self.assertEqual(study.select_model(rates), study.MODEL_ORDER[3])

    def test_selector_rejects_unregistered_candidate_sets(self):
        with self.assertRaisesRegex(ValueError, "exactly the five"):
            study.select_model({study.MODEL_ORDER[0]: 0.5})

    def test_preregistration_identity_and_window_are_frozen(self):
        prereg_path = Path(__file__).resolve().parents[2] / "research/weekly_purchase/1251/E052_THREE_LINE_TRAILING_PERFORMANCE_SELECTOR_PREREG_20261115.json"
        policy_path = Path(__file__).resolve().parents[2] / "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
        prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        study._verify_preregistration(prereg, policy)
        self.assertEqual(prereg["selection"]["lookback_targets"], 100)
        self.assertEqual(prereg["evaluation_target_range"], [501, 1249])
        self.assertIs(prereg["selection"]["parameter_search"], False)


if __name__ == "__main__":
    unittest.main()
