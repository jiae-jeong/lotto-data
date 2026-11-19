import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import automation.protocol_recovery_v1 as recovery


def five_lines(offset=0):
    return [
        [offset + 1, offset + 2, offset + 3, offset + 4, offset + 5, offset + 6],
        [offset + 7, offset + 8, offset + 9, offset + 10, offset + 11, offset + 12],
        [offset + 13, offset + 14, offset + 15, offset + 16, offset + 17, offset + 18],
        [offset + 19, offset + 20, offset + 21, offset + 22, offset + 23, offset + 24],
        [offset + 25, offset + 26, offset + 27, offset + 28, offset + 29, offset + 30],
    ]


class PurchaseConfirmationProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_root = recovery.ROOT
        recovery.ROOT = self.root

        target_dir = self.root / "research" / "weekly_purchase" / "2"
        target_dir.mkdir(parents=True)
        self.purchase_path = target_dir / "ACTUAL_PURCHASE_FIVE_LINES_2.json"
        self.final_path = target_dir / "FINAL_FIVE_LINES_2.json"
        self.purchase_path.write_text(json.dumps({
            "target_round": 2,
            "data_cutoff": 1,
            "final_lines": five_lines(0),
        }), encoding="utf-8")
        self.final_path.write_text(json.dumps({
            "target_round": 2,
            "data_cutoff": 1,
            "final_lines": five_lines(1),
        }), encoding="utf-8")

        self.registry_path = self.root / "research" / "PURCHASE_CONFIRMATION_REGISTRY.json"
        self.registry_path.write_text(json.dumps({
            "schema_version": 1,
            "policy": "Test fixture only.",
            "confirmed_purchases": [],
        }), encoding="utf-8")
        self.rows = [
            {"round": 1, "nums": [1, 2, 3, 4, 5, 6], "bonus": 7},
            {"round": 2, "nums": [2, 3, 4, 5, 6, 7], "bonus": 8},
        ]
        self.dated = self.root / "analysis" / "2026-11-14"
        self.dated.mkdir(parents=True)

    def tearDown(self):
        recovery.ROOT = self.old_root
        self.tmp.cleanup()

    def test_filename_and_preserved_final_do_not_prove_purchase(self):
        result = recovery.build_historical_closed_loop(self.rows, self.dated)
        self.assertEqual(result["verified_round_count"], 0)
        self.assertEqual(result["verified_purchase_lines"], 0)
        self.assertEqual(result["reviews"], [])
        self.assertEqual(result["purchase_confirmation_status"], "NO_CONFIRMED_PURCHASES")
        self.assertEqual(result["unconfirmed_purchase_target_count"], 1)
        self.assertEqual(result["unresolved_source_conflicts"][0]["target_round"], 2)
        self.assertFalse(result["closed_loop_complete"])

    def test_explicit_confirmation_requires_exact_source_hash(self):
        source_sha = hashlib.sha256(self.purchase_path.read_bytes()).hexdigest()
        self.registry_path.write_text(json.dumps({
            "schema_version": 1,
            "confirmed_purchases": [{
                "target_round": 2,
                "source_path": "research/weekly_purchase/2/ACTUAL_PURCHASE_FIVE_LINES_2.json",
                "source_sha256": source_sha,
                "confirmation_status": "CONFIRMED",
                "evidence_type": "EXPLICIT_USER_CONFIRMATION",
                "confirmed_by_user": True,
                "evidence_reference": "synthetic-test-fixture",
            }],
        }), encoding="utf-8")
        result = recovery.build_historical_closed_loop(self.rows, self.dated)
        self.assertEqual(result["verified_round_count"], 1)
        self.assertEqual(result["reviews"][0]["source_role"], "ACTUAL_PURCHASE_CONFIRMED")
        self.assertEqual(result["reviews"][0]["source_sha256"], source_sha)
        self.assertEqual(result["unconfirmed_purchase_target_count"], 0)
        self.assertTrue(result["closed_loop_complete"])

    def test_hash_mismatch_is_not_accepted_as_purchase_confirmation(self):
        self.registry_path.write_text(json.dumps({
            "schema_version": 1,
            "confirmed_purchases": [{
                "target_round": 2,
                "source_path": "research/weekly_purchase/2/ACTUAL_PURCHASE_FIVE_LINES_2.json",
                "source_sha256": "0" * 64,
                "confirmation_status": "CONFIRMED",
                "evidence_type": "EXPLICIT_USER_CONFIRMATION",
                "confirmed_by_user": True,
                "evidence_reference": "synthetic-test-fixture",
            }],
        }), encoding="utf-8")
        result = recovery.build_historical_closed_loop(self.rows, self.dated)
        self.assertEqual(result["verified_round_count"], 0)
        self.assertTrue(any("sha256_mismatch" in item["reason"] for item in result["invalid_or_unreviewable_preserved_records"]))


if __name__ == "__main__":
    unittest.main()
