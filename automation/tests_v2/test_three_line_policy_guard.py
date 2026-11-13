import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "finalize_from_strict_ready_v1.py"
SPEC = importlib.util.spec_from_file_location("strict_ready_finalizer", MODULE_PATH)
FINALIZER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FINALIZER)


class ThreeLinePolicyGuardTests(unittest.TestCase):
    def make_root(self, cutoff):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        data_path = root / "lotto_data.csv"
        fields = ["round", "date", "no1", "no2", "no3", "no4", "no5", "no6", "bonus"]
        with data_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for round_no in range(1, cutoff + 1):
                writer.writerow({
                    "round": round_no,
                    "date": "2026-11-07",
                    "no1": 1, "no2": 2, "no3": 3,
                    "no4": 4, "no5": 5, "no6": 6, "bonus": 7,
                })
        policy_dir = root / "research" / "weekly_purchase" / "1251"
        policy_dir.mkdir(parents=True)
        (policy_dir / "THREE_LINE_POLICY_1251_PLUS.json").write_text(
            json.dumps({"effective_from_target": 1251, "purchase_lines": 3}),
            encoding="utf-8",
        )
        return temp, root

    def test_target_1251_blocks_legacy_five_line_freeze(self):
        temp, root = self.make_root(1250)
        self.addCleanup(temp.cleanup)
        with self.assertRaisesRegex(ValueError, "requires 3 lines"):
            FINALIZER.build_freeze(root, "2026-11-15")

    def test_target_1250_keeps_historical_five_line_path(self):
        temp, root = self.make_root(1249)
        self.addCleanup(temp.cleanup)
        with self.assertRaises(FileNotFoundError):
            FINALIZER.build_freeze(root, "2026-11-13")


if __name__ == "__main__":
    unittest.main()
