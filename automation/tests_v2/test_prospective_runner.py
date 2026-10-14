import io
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prospective_evidence_v1_runner as runner


class ProspectiveRunnerTests(unittest.TestCase):
    def test_official_payload_is_round_and_number_validated(self):
        payload = {"returnValue": "success", "drwNo": 1246, "drwNoDate": "2026-10-17",
                   "drwtNo1": 1, "drwtNo2": 2, "drwtNo3": 3, "drwtNo4": 4,
                   "drwtNo5": 5, "drwtNo6": 6, "bnusNo": 7}
        self.assertEqual(runner.parse_official(payload, 1246)["numbers"], [1, 2, 3, 4, 5, 6])
        with self.assertRaises(ValueError):
            runner.parse_official(payload, 1245)
        payload["bnusNo"] = 6
        with self.assertRaises(ValueError):
            runner.parse_official(payload, 1246)

    def test_secondary_payload_must_match_target_and_be_complete(self):
        payload = {"draw": {"round": 1246, "date": "2026-10-17", "numbers": [1, 2, 3, 4, 5, 6], "bonus": 7}}
        self.assertEqual(runner.parse_secondary(payload, 1246)["bonus"], 7)
        self.assertIsNone(runner.parse_secondary(payload, 1247))
        payload["draw"]["bonus"] = 6
        with self.assertRaises(ValueError):
            runner.parse_secondary(payload, 1246)

    def test_shadow_prediction_uses_only_pre_target_cutoff(self):
        draws = [{"round": i, "date": f"2026-01-{i:02d}", "numbers": [i, i+1, i+2, i+3, i+4, i+5], "bonus": 20}
                 for i in range(1, 10)]
        prediction = runner.make_next_shadow(draws, 10, "2026-10-14T00:00:00+00:00", "a" * 64)
        self.assertEqual(prediction["target_round"], 10)
        self.assertEqual(prediction["training_through_round"], 9)
        self.assertEqual(prediction["canonical_data_sha256"], "a" * 64)
        self.assertFalse(prediction["purchase_recommendation"])

    def test_existing_event_is_reused_only_for_same_outcome(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            root = Path(temp)
            path = root / "analysis/prospective_v1/outcomes/ROUND_1246.json"
            path.parent.mkdir(parents=True)
            expected = {"target_round": 1246, "draw_date": "2026-10-17",
                        "main_numbers": [1, 2, 3, 4, 5, 6], "bonus": 7}
            path.write_text(json.dumps(expected), encoding="utf-8")
            actual = {**expected, "source_evidence": []}
            self.assertEqual(runner._ensure_outcome_event(root, actual), path)
            actual["bonus"] = 8
            with self.assertRaises(ValueError):
                runner._ensure_outcome_event(root, actual)


if __name__ == "__main__":
    unittest.main()

