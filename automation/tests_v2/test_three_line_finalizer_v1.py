import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "finalize_three_line_from_strict_ready_v1.py"
SPEC = importlib.util.spec_from_file_location("finalize_three_line_from_strict_ready_v1", MODULE_PATH)
FINALIZER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FINALIZER)


class ThreeLineFinalizerTests(unittest.TestCase):
    def make_root(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        data = root / "lotto_data.csv"
        fields = ["round", "date", "no1", "no2", "no3", "no4", "no5", "no6", "bonus"]
        with data.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for r in range(1, 1251):
                writer.writerow({
                    "round": r, "date": "2026-11-14",
                    "no1": 1, "no2": 2, "no3": 3,
                    "no4": 4, "no5": 5, "no6": 6, "bonus": 7,
                })
        policy_dir = root / "research" / "weekly_purchase" / "1251"
        policy_dir.mkdir(parents=True)
        (policy_dir / "THREE_LINE_POLICY_1251_PLUS.json").write_text(
            json.dumps({
                "policy_id": "WEEKLY_THREE_LINE_POLICY_1251_PLUS",
                "effective_from_target": 1251,
                "purchase_lines": 3,
                "numbers_per_line": 6,
            }),
            encoding="utf-8",
        )
        self.addCleanup(temp.cleanup)
        return root

    def write_ready(self, root, date_kst="2026-11-19"):
        cutoff, data_sha, _ = FINALIZER.read_source(root)
        target = int(cutoff) + 1
        outdir = root / "research" / "weekly_purchase" / str(target)
        outdir.mkdir(parents=True, exist_ok=True)
        payload = {
            "status": "STRICT_PASS_READY",
            "target_round": target,
            "date_kst": date_kst,
            "data_cutoff": int(cutoff),
            "data_sha256": data_sha,
            "strict_model_validation_pass": True,
            "validated_models": ["three-line-model-v1"],
            "strict_portfolio_pass": True,
            "strict_pass_ready": True,
            "historical_strict_gate_pass": True,
            "strict_gate_version": "FROZEN_THREE_LINE_STRICT_GATE_V1",
            "no_future_leakage": True,
            "final_selection_randomness": False,
            "random_fallback_allowed": False,
            "final_lines": [
                [1, 2, 3, 4, 5, 6],
                [7, 8, 9, 10, 11, 12],
                [13, 14, 15, 16, 17, 18],
            ],
            "inference": {
                "max_hits": {"adjusted_ci_lower": 0.01},
                "any2": {"adjusted_ci_lower": 0.02},
                "any3": {"adjusted_ci_lower": 0.01},
                "winning_union_coverage": {"adjusted_ci_lower": 0.03},
                "any2_positive_50_target_block_share": 0.70,
            },
            "prospective_confirmation": {
                "required": True,
                "minimum_target_count": 50,
                "observed_target_count": 50,
                "completion_rule": "50 untouched target rounds under frozen rules",
                "complete": True,
            },
        }
        ready = outdir / f"STRICT_PASS_READY_{target}_{date_kst.replace('-', '')}_test.json"
        ready.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return ready

    def test_thursday_freeze_and_friday_verify_same_three_lines(self):
        root = self.make_root()
        self.write_ready(root)
        frozen = FINALIZER.freeze(root, "2026-11-19")
        self.assertEqual(frozen["status"], "THURSDAY_VERIFIED_3_LINE_READY")
        self.assertEqual(frozen["target_round"], 1251)
        verified = FINALIZER.verify(root, "2026-11-20")
        self.assertEqual(verified["status"], "THURSDAY_SEAL_REVALIDATED")
        self.assertEqual(verified["line_count"], 3)
        self.assertEqual(verified["union_size"], 18)
        self.assertEqual(verified["line_level_output_status"], "UNCHANGED_THURSDAY_SEAL")

    def test_friday_cannot_create_a_new_seal(self):
        root = self.make_root()
        self.write_ready(root)
        with self.assertRaisesRegex(ValueError, "only on Thursday"):
            FINALIZER.freeze(root, "2026-11-20")

    def test_missing_ready_artifact_blocks_freeze(self):
        root = self.make_root()
        with self.assertRaisesRegex(ValueError, "no current three-line STRICT_PASS_READY"):
            FINALIZER.freeze(root, "2026-11-19")

    def test_changed_source_after_thursday_blocks_friday_verification(self):
        root = self.make_root()
        self.write_ready(root)
        FINALIZER.freeze(root, "2026-11-19")
        data = root / "lotto_data.csv"
        with data.open("a", encoding="utf-8") as stream:
            stream.write("1251,2026-11-21,1,2,3,4,5,6,7\n")
        with self.assertRaises(FileNotFoundError):
            FINALIZER.verify(root, "2026-11-20")

    def test_policy_id_mismatch_blocks_friday_verification(self):
        root = self.make_root()
        self.write_ready(root)
        FINALIZER.freeze(root, "2026-11-19")
        seal = root / "research" / "weekly_purchase" / "1251" / "FINAL_THREE_LINES_1251_20261119.json"
        payload = json.loads(seal.read_text(encoding="utf-8"))
        payload["policy_id"] = "WRONG_POLICY"
        payload["freeze_payload_sha256"] = FINALIZER.canonical_sha(payload)
        seal.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "policy id mismatch"):
            FINALIZER.verify(root, "2026-11-20")


if __name__ == "__main__":
    unittest.main()
