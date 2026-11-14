import csv
import hashlib
import io
import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

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


    def _write_repository_snapshot(self, root: Path):
        target_numbers = [16, 22, 23, 24, 27, 28]
        lines = ["round,date,no1,no2,no3,no4,no5,no6,bonus"]
        for round_no in range(1, 1247):
            if round_no == 1246:
                draw_date, numbers, bonus = "2026.10.17", target_numbers, 6
            else:
                draw_date, numbers, bonus = "2026.10.10", [1, 2, 3, 4, 5, 6], 7
            lines.append(",".join(map(str, [round_no, draw_date, *numbers, bonus])))
        raw = ("\n".join(lines) + "\n").encode()
        data_path = root / "lotto_data.csv"
        data_path.write_bytes(raw)
        prefix_lines = raw.splitlines(keepends=True)
        prefix = []
        for line in prefix_lines:
            prefix.append(line)
            if line.startswith(b"1246,"):
                break
        prefix_sha = hashlib.sha256(b"".join(prefix)).hexdigest()
        crosscheck = {
            "evidence_id": "E030_OUTCOME_SOURCE_CROSSCHECK_1246_v1",
            "target_round": 1246,
            "draw_date": "2026-10-17",
            "main_numbers": target_numbers,
            "bonus": 6,
            "repository_snapshot": {
                "path": "lotto_data.csv",
                "data_cutoff": 1246,
                "prefix_through_target_sha256": prefix_sha,
            },
            "fallback_sources": [
                {"domain": "source-a.example", "url": "https://source-a.example/1246",
                 "round": 1246, "draw_date": "2026-10-17", "main_numbers": target_numbers, "bonus": 6},
                {"domain": "source-b.example", "url": "https://source-b.example/1246",
                 "round": 1246, "draw_date": "2026-10-17", "main_numbers": target_numbers, "bonus": 6},
            ],
        }
        crosscheck_path = root / "research/prospective_v1/source_crosschecks/ROUND_1246.json"
        crosscheck_path.parent.mkdir(parents=True, exist_ok=True)
        crosscheck_path.write_text(json.dumps(crosscheck, indent=2) + "\n", encoding="utf-8")
        return data_path

    def _write_base_snapshot(self, path: Path):
        lines = ["round,date,no1,no2,no3,no4,no5,no6,bonus"]
        for round_no in range(1, 1246):
            lines.append(",".join(map(str, [round_no, "2026.10.10", 1, 2, 3, 4, 5, 6, 7])))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_frozen_1246(self, root: Path):
        frozen = {
            "status": "FROZEN_PROSPECTIVE_SHADOW_ONLY",
            "target_round": 1246,
            "training_through_round": 1245,
            "signals": [
                {"signal": "CALENDAR_SEASON_CONDITIONAL_v1", "model_version": "E025_FROZEN_v1", "numbers": [4, 12, 14, 19, 21, 45]},
                {"signal": "PREVIOUS_SUM_REGIME_CONDITIONAL_v1", "model_version": "E025_FROZEN_v1", "numbers": [18, 21, 31, 33, 40, 44]},
            ],
            "purchase_recommendation": False,
        }
        path = root / "analysis/seed/E030/FROZEN_SIGNALS_1246.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
        return path

    def test_repository_fallback_requires_prefix_hash_and_two_matching_domains(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_repository_snapshot(root)
            actual = ledger.fetch_repository_verified(1246, root)
            self.assertEqual(actual["numbers"], (16, 22, 23, 24, 27, 28))
            self.assertEqual(actual["bonus"], 6)
            self.assertEqual(actual["source_type"], "REPOSITORY_SNAPSHOT_CROSSCHECKED_BY_TWO_SECONDARY_SOURCES")
            crosscheck = root / "research/prospective_v1/source_crosschecks/ROUND_1246.json"
            record = json.loads(crosscheck.read_text(encoding="utf-8"))
            record["fallback_sources"][1]["bonus"] = 5
            crosscheck.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaises(ValueError):
                ledger.fetch_repository_verified(1246, root)

    def test_run_records_1246_but_never_backfills_a_late_1247_prediction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_repository_snapshot(root)
            base = root / "snapshot_1_1245.csv"
            self._write_base_snapshot(base)
            frozen_path = self._write_frozen_1246(root)
            original_frozen = frozen_path.read_bytes()
            now = datetime(2026, 11, 15, 0, 0, tzinfo=timezone.utc)
            with patch.object(ledger, "DATA", base), patch.object(ledger, "fetch_official", return_value=None):
                result = ledger.run(root=root, now=now)
            tracker = root / "analysis/prospective/E030"
            outcome = json.loads((tracker / "RESULT_1246.json").read_text(encoding="utf-8"))
            status = json.loads((tracker / "UPDATE_STATUS_1246.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "OUTCOME_RECORDED")
            self.assertEqual(outcome["source_type"], "REPOSITORY_SNAPSHOT_CROSSCHECKED_BY_TWO_SECONDARY_SOURCES")
            self.assertFalse(result["next_prediction_created"])
            self.assertFalse((tracker / "FROZEN_SIGNALS_1247.json").exists())
            self.assertEqual(status["historical_targets_without_pre_draw_freeze"], [])
            self.assertEqual(frozen_path.read_bytes(), original_frozen)
            self.assertFalse(outcome["purchase_recommendation"])

    def test_run_freezes_next_target_when_its_draw_is_still_in_the_future(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_repository_snapshot(root)
            base = root / "snapshot_1_1245.csv"
            self._write_base_snapshot(base)
            self._write_frozen_1246(root)
            now = datetime(2026, 10, 17, 14, 0, tzinfo=timezone.utc)
            with patch.object(ledger, "DATA", base), patch.object(ledger, "fetch_official", return_value=None):
                result = ledger.run(root=root, now=now)
            next_path = root / "analysis/prospective/E030/FROZEN_SIGNALS_1247.json"
            next_prediction = json.loads(next_path.read_text(encoding="utf-8"))
            self.assertTrue(result["next_prediction_created"])
            self.assertEqual(next_prediction["target_round"], 1247)
            self.assertEqual(next_prediction["training_through_round"], 1246)
            self.assertEqual(next_prediction["target_draw_date_assumption"], "2026-10-24")


if __name__ == "__main__":
    unittest.main()
