import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "../research/prospective_v1"))
import prospective_purchase_intake_v1 as intake
import ledger_v1


class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


def opener_for(payload):
    return lambda *args, **kwargs: Response(json.dumps(payload).encode("utf-8"))


def sample_payload(target=3, cutoff=2):
    return {"target_round": target, "purchase": True,
        "generated_at": "2026-10-11T00:00:00Z", "submitted_at": "2026-10-11T00:01:00Z",
        "training_through_round": cutoff, "source_reference": "user-confirmed purchase record",
        "lines": [
            {"numbers": list(range((i-1)*6+1,i*6+1)), "source_model": f"source-{i}", "model_version": "v1"}
            for i in range(1,6)]}


class ProspectivePurchaseIntakeTests(unittest.TestCase):
    def make_root(self, base: Path) -> Path:
        root=base
        root.joinpath("lotto_data.csv").write_text(
            "round,date,no1,no2,no3,no4,no5,no6,bonus\n"
            "1,2026.10.10,1,2,3,4,5,6,7\n"
            "2,2026.10.11,8,9,10,11,12,13,14\n",encoding="utf-8")
        path=root/intake.INTAKE_DIR/"ROUND_3.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(sample_payload()),encoding="utf-8")
        return root

    def test_pre_draw_intake_creates_immutable_sha_seal(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            root=self.make_root(Path(temp))
            now=datetime(2026,10,11,0,2,tzinfo=timezone.utc)
            result=intake.seal_intake(root,3,opener_for({"returnValue":"fail"}),now)
            self.assertEqual(result["status"],"SEALED")
            sealed=root/intake.LEDGER_DIR/"ROUND_3.json"
            bundle=ledger_v1.verify_purchase_bundle(sealed)
            self.assertTrue(bundle["purchase"])
            self.assertTrue(bundle["sealed_before_draw"])
            self.assertEqual(len(bundle["line_sha256"]),5)
            self.assertEqual(len(set(bundle["line_sha256"])),5)
            again=intake.seal_intake(root,3,opener_for({"returnValue":"success","drwNo":3}),now)
            self.assertEqual(again["status"],"ALREADY_SEALED")

    def test_post_draw_submission_is_rejected_and_not_sealed(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            root=self.make_root(Path(temp))
            actual={"returnValue":"success","drwNo":3,"drwNoDate":"2026-10-18"}
            now=datetime(2026,10,11,0,2,tzinfo=timezone.utc)
            with self.assertRaises(intake.IntakeRejected):
                intake.seal_intake(root,3,opener_for(actual),now)
            self.assertFalse((root/intake.LEDGER_DIR/"ROUND_3.json").exists())

    def test_changed_source_intake_is_rejected_after_seal(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            root=self.make_root(Path(temp))
            now=datetime(2026,10,11,0,2,tzinfo=timezone.utc)
            intake.seal_intake(root,3,opener_for({"returnValue":"fail"}),now)
            path=root/intake.INTAKE_DIR/"ROUND_3.json"
            payload=json.loads(path.read_text(encoding="utf-8"));payload["rationale"]="changed after seal"
            path.write_text(json.dumps(payload),encoding="utf-8")
            with self.assertRaisesRegex(intake.IntakeRejected,"changed after"):
                intake.seal_intake(root,3,opener_for({"returnValue":"fail"}),now)

    def test_cutoff_duplicate_and_official_lookup_fail_closed(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            root=self.make_root(Path(temp));now=datetime(2026,10,11,0,2,tzinfo=timezone.utc)
            payload=sample_payload(cutoff=3)
            path=root/intake.INTAKE_DIR/"ROUND_3.json"
            payload["training_through_round"]=3;path.write_text(json.dumps(payload),encoding="utf-8")
            with self.assertRaisesRegex(intake.IntakeRejected,"training_through_round"):
                intake.seal_intake(root,3,opener_for({"returnValue":"fail"}),now)
            payload=sample_payload();payload["lines"][4]["numbers"]=payload["lines"][0]["numbers"]
            path.write_text(json.dumps(payload),encoding="utf-8")
            with self.assertRaisesRegex(intake.IntakeRejected,"duplicate lines"):
                intake.seal_intake(root,3,opener_for({"returnValue":"fail"}),now)
            payload=sample_payload();path.write_text(json.dumps(payload),encoding="utf-8")
            with self.assertRaisesRegex(intake.IntakeRejected,"could not confirm"):
                intake.seal_intake(root,3,lambda *a,**k: (_ for _ in ()).throw(OSError("offline")),now)


if __name__ == "__main__":
    unittest.main()
