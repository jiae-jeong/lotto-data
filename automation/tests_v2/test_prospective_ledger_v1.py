import io
import json
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import update_prospective_ledger_v1 as ledger


class ProspectiveLedgerTests(unittest.TestCase):
    def test_next_prediction_is_cutoff_safe_and_shadow_only(self):
        draws = ledger.load_draws()
        result = ledger.make_frozen_prediction(draws, "2026-10-14T00:00:00+00:00")
        self.assertEqual(result["target_round"], 1246)
        self.assertEqual(result["training_through_round"], 1245)
        self.assertEqual(len(result["signals"]), 2)
        self.assertFalse(result["purchase_recommendation"])
        self.assertTrue(all(len(x["numbers"]) == 6 for x in result["signals"]))

    def test_official_result_parser_validates_round_and_fields(self):
        payload = {"returnValue": "success", "drwNo": 1245, "drwNoDate": "2026-10-10",
                   "drwtNo1": 1, "drwtNo2": 2, "drwtNo3": 3, "drwtNo4": 4,
                   "drwtNo5": 5, "drwtNo6": 6, "bnusNo": 7}
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *args): self.close()
        result = ledger.fetch_official(1245, opener=lambda *args, **kwargs: Response(json.dumps(payload).encode()))
        self.assertEqual(result["numbers"], (1, 2, 3, 4, 5, 6))
        self.assertEqual(result["bonus"], 7)
        self.assertEqual(result["date"], date(2026, 10, 10))
        with self.assertRaises(ValueError):
            ledger.fetch_official(1244, opener=lambda *args, **kwargs: Response(json.dumps(payload).encode()))

    def test_result_artifact_records_prediction_digest_and_cutoff_provenance(self):
        frozen = {"target_round": 1246, "training_through_round": 1245,
                  "signals": [{"signal": "X", "model_version": "v1", "numbers": [1, 2, 3, 4, 5, 6]}]}
        import tempfile
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            path = Path(temp) / "frozen.json"
            path.write_text(json.dumps(frozen), encoding="utf-8")
            actual = {"round": 1246, "date": date(2026, 10, 17), "numbers": (1, 2, 3, 4, 5, 7), "bonus": 8}
            row = ledger.result_artifact(frozen, path, actual, "2026-10-17T13:00:00+00:00")
            self.assertEqual(row["prediction_sha256"], ledger.digest(path))
            self.assertEqual(row["signals"][0]["main_hits"], 5)
            self.assertFalse(row["purchase_recommendation"])


if __name__ == "__main__":
    unittest.main()
