import gzip
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import prepare_prospective_v1 as prep
import ledger_v1 as ledger


class ProspectiveFreezeTests(unittest.TestCase):
    def test_exact_random5_metrics_and_power_are_finite(self):
        metrics = prep.random5_exact_metrics()
        self.assertGreater(metrics["five_line_any_kplus_probability"]["2"], metrics["five_line_any_kplus_probability"]["3"])
        self.assertAlmostEqual(metrics["single_ticket_mean_hits"], 0.8)
        result = prep.power_horizon(metrics)
        self.assertGreater(result["five_line_any3plus"]["0.01"]["0.8"], 0)

    def test_e_process_is_one_and_grows_for_positive_evidence(self):
        neutral = ledger.mixture_e_value([0.0] * 20, -1, 1, [0.01, 0.02])
        positive = ledger.mixture_e_value([0.5] * 20, -1, 1, [0.01, 0.02])
        self.assertLessEqual(neutral, 1.0)
        self.assertGreater(positive, neutral)

    def test_pool_generation_is_deterministic_and_each_portfolio_valid(self):
        first = prep.random_pool_bytes()
        second = prep.random_pool_bytes()
        self.assertEqual(first, second)
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            path = Path(temp) / "pool.jsonl.gz"
            path.write_bytes(first)
            self.assertEqual(len(ledger.read_random5_pool(path, prep.sha_file(path))), 10_000)
        singles = prep.random_single_pool_bytes()
        self.assertEqual(singles, prep.random_single_pool_bytes())
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            path = Path(temp) / "single.jsonl.gz"
            path.write_bytes(singles)
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                self.assertEqual(sum(1 for _ in stream), 10_000)

    def test_purchase_seal_requires_verified_source_and_is_write_once(self):
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            root = Path(temp)
            metadata = {"purchase": True, "sealed_before_draw": True, "source_evidence": [{"type": "receipt"}]}
            path = ledger.seal_purchase(root, 1246, [[1,2,3,4,5,6],[7,8,9,10,11,12],[13,14,15,16,17,18],[19,20,21,22,23,24],[25,26,27,28,29,30]], metadata, "2099-01-01T00:00:00+00:00")
            with self.assertRaises(FileExistsError):
                ledger.seal_purchase(root, 1246, [[1,2,3,4,5,6],[7,8,9,10,11,12],[13,14,15,16,17,18],[19,20,21,22,23,24],[25,26,27,28,29,30]], metadata, "2099-01-01T00:00:00+00:00")
            self.assertTrue(path.exists())

    def test_outcome_event_requires_two_source_types(self):
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            actual = {"target_round": 1246, "draw_date": "2099-01-01", "main_numbers": [1,2,3,4,5,6], "bonus": 7,
                      "source_evidence": [{"source_type": "official"}]}
            with self.assertRaises(ValueError):
                ledger.write_outcome_event(Path(temp), actual)


if __name__ == "__main__":
    unittest.main()
