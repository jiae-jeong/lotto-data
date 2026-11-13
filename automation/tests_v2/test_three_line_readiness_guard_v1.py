import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "three_line_readiness_guard_v1.py"
SPEC = importlib.util.spec_from_file_location("three_line_readiness_guard_v1", MODULE_PATH)
GUARD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GUARD)


class ThreeLineReadinessGuardTests(unittest.TestCase):
    def make_root(self, cutoff=1250):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        data = root / "lotto_data.csv"
        fields = ["round", "date", "no1", "no2", "no3", "no4", "no5", "no6", "bonus"]
        with data.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for r in range(1, cutoff + 1):
                writer.writerow({
                    "round": r, "date": "2026-11-14",
                    "no1": 1, "no2": 2, "no3": 3,
                    "no4": 4, "no5": 5, "no6": 6, "bonus": 7,
                })
        policy_dir = root / "research" / "weekly_purchase" / "1251"
        policy_dir.mkdir(parents=True)
        (policy_dir / "THREE_LINE_POLICY_1251_PLUS.json").write_text(
            json.dumps({
                "effective_from_target": 1251,
                "purchase_lines": 3,
                "numbers_per_line": 6,
            }),
            encoding="utf-8",
        )
        self.addCleanup(temp.cleanup)
        return root

    def ready_payload(self, root, date="2026-11-15", lines=None):
        cutoff, data_sha, _ = GUARD.read_source(root)
        if lines is None:
            lines = [
                [1, 2, 3, 4, 5, 6],
                [7, 8, 9, 10, 11, 12],
                [13, 14, 15, 16, 17, 18],
            ]
        return {
            "status": "STRICT_PASS_READY",
            "target_round": int(cutoff) + 1,
            "date_kst": date,
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
            "final_lines": lines,
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
                "completion_rule": "50 consecutive untouched target rounds with all preregistered checks",
                "complete": True,
            },
        }

    def write_ready(self, root, payload):
        target = payload["target_round"]
        outdir = root / "research" / "weekly_purchase" / str(target)
        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / f"STRICT_PASS_READY_{target}_{payload['date_kst'].replace('-', '')}_test.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_target_1251_without_candidate_stays_not_ready_and_suppresses_lines(self):
        root = self.make_root(1250)
        result = GUARD.build_status(root, "2026-11-15")
        self.assertEqual(result["target_round"], 1251)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertFalse(result["strict_portfolio_pass"])
        self.assertFalse(result["strict_pass_ready"])
        self.assertFalse(result["random_fallback_allowed"])
        self.assertEqual(result["line_level_output_status"], "SUPPRESSED_NOT_READY")
        self.assertNotIn("final_lines", result)

    def test_three_line_guard_does_not_apply_to_target_1250(self):
        root = self.make_root(1249)
        with self.assertRaisesRegex(ValueError, "only active from target 1251"):
            GUARD.build_status(root, "2026-11-14")

    def test_five_line_ready_artifact_is_rejected(self):
        root = self.make_root(1250)
        payload = self.ready_payload(root, lines=[
            [1, 2, 3, 4, 5, 6],
            [7, 8, 9, 10, 11, 12],
            [13, 14, 15, 16, 17, 18],
            [19, 20, 21, 22, 23, 24],
            [25, 26, 27, 28, 29, 30],
        ])
        self.write_ready(root, payload)
        with self.assertRaisesRegex(ValueError, "exactly three lines"):
            GUARD.build_status(root, payload["date_kst"])

    def test_valid_disjoint_three_line_ready_artifact_is_accepted(self):
        root = self.make_root(1250)
        payload = self.ready_payload(root)
        self.write_ready(root, payload)
        result = GUARD.build_status(root, payload["date_kst"])
        self.assertEqual(result["status"], "STRICT_PASS_READY")
        self.assertTrue(result["strict_portfolio_pass"])
        self.assertTrue(result["strict_pass_ready"])
        self.assertTrue(result["ready_file_exists"])
        self.assertNotIn("final_lines", result)

    def test_stale_data_hash_is_rejected(self):
        root = self.make_root(1250)
        payload = self.ready_payload(root)
        payload["data_sha256"] = hashlib.sha256(b"stale").hexdigest()
        self.write_ready(root, payload)
        with self.assertRaisesRegex(ValueError, "cutoff/hash mismatch"):
            GUARD.build_status(root, payload["date_kst"])


if __name__ == "__main__":
    unittest.main()
