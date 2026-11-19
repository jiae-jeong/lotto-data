import csv
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
QUEUE=ROOT/"automation/research_queue_v2.json"
PREREG=ROOT/"research/weekly_purchase/1251/E076_HISTORICAL_RECOMMENDATION_CANDIDATE_VS_ALLOCATOR_DECOMPOSITION_PREREG_20261119.json"
DATA=ROOT/"lotto_data.csv"
OUT=ROOT/"analysis/2026-11-19/E076_HISTORICAL_RECOMMENDATION_CANDIDATE_VS_ALLOCATOR_DECOMPOSITION_v1"


def git_blob(path):
    return subprocess.check_output(["git","rev-parse","HEAD:"+path.relative_to(ROOT).as_posix()],cwd=ROOT,text=True).strip()


class E076QueueContractTests(unittest.TestCase):
    def test_preregistered_diagnostic_manifest_and_sources_are_verified_without_promotion(self):
        queue=json.loads(QUEUE.read_text(encoding="utf-8"))
        task=next(x for x in queue["tasks"] if x.get("id")=="E076_HISTORICAL_RECOMMENDATION_CANDIDATE_VS_ALLOCATOR_DECOMPOSITION_v1")
        prereg=json.loads(PREREG.read_text(encoding="utf-8"))
        results=json.loads((OUT/"RESULTS.json").read_text(encoding="utf-8"))
        manifest=json.loads((OUT/"SHA256_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(task["execution_status"],"EXECUTED_HISTORICAL_DIAGNOSTIC_ONLY")
        self.assertEqual(task["execution_mode"],"connector_reproducible_compute")
        self.assertEqual(task["preregistration_blob_sha"],git_blob(PREREG))
        self.assertEqual(task["preregistration_blob_sha"],"4d4f73e1e8006c2eb1c6f908bfe018d6e1ac6564")
        self.assertEqual(prereg["preregistration_status"],"FROZEN_BEFORE_EXECUTION")
        self.assertEqual(prereg["source_data"]["blob_sha"],git_blob(DATA))
        self.assertEqual(prereg["source_data"]["sha256"],hashlib.sha256(DATA.read_bytes()).hexdigest())
        self.assertEqual(results["preregistration_blob_sha"],git_blob(PREREG))
        self.assertEqual(results["data_integrity"]["row_count"],1250)
        self.assertEqual(results["data_integrity"]["round_range"],[1,1250])
        self.assertTrue(results["data_integrity"]["contiguous"])
        self.assertEqual(results["purchase_confirmation"]["confirmed_purchases"],0)
        self.assertEqual(results["artifact_count"],6)
        self.assertFalse(results["promotion"]["strict_pass_ready"])
        self.assertFalse(results["promotion"]["prospective_confirmation"])
        self.assertEqual(manifest["hash_algorithm"],"SHA-256 over UTF-8 bytes; manifest excludes itself")
        self.assertEqual(set(manifest["files"]),{"RESULTS.json","LINE_HIT_DECOMPOSITION.csv","REPORT.md"})
        for name,record in manifest["files"].items():
            payload=(OUT/name).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(),record["sha256"],name)
            self.assertEqual(len(payload),record["bytes"],name)
        self.assertEqual(git_blob(DATA),"66431d711919f179e4cb1349e2f7295c68a8735e")
        for source in prereg["recommendation_artifacts"]:
            source_path=ROOT/source["path"]
            self.assertEqual(git_blob(source_path),source["blob_sha"],source["id"])
            result=next(x for x in results["results"] if x["artifact_id"]==source["id"])
            self.assertEqual(result["source_blob_sha"],source["blob_sha"])
            self.assertEqual(source["cutoff"],source["round"]-1)
        self.assertEqual(results["candidate_stage"]["artifacts_with_at_least_2_winners_in_union"],5)
        self.assertEqual(results["allocator_stage"]["artifacts_realizing_any2"],2)
        self.assertEqual(results["candidate_stage"]["artifacts_with_at_least_3_winners_in_union"],4)
        self.assertEqual(results["allocator_stage"]["artifacts_realizing_any3"],2)
        self.assertEqual(results["candidate_stage"]["artifacts_with_at_least_4_winners_in_union"],3)
        self.assertEqual(results["allocator_stage"]["artifacts_realizing_any4"],0)
        with (OUT/"LINE_HIT_DECOMPOSITION.csv").open(encoding="utf-8",newline="") as stream:
            self.assertEqual(len(list(csv.DictReader(stream))),28)
        self.assertFalse(task["independent_research_axis"])
        self.assertFalse(task["independent_sample"])
        self.assertFalse(task["target_1251_three_line_readiness_eligible"])
        self.assertFalse(task["spec"]["strict_pass_ready"])
        self.assertEqual(task["execution_result"]["verification"],"PASS")
        self.assertEqual(task["execution_result"]["artifacts"],6)
        self.assertIn("no model/allocator promotion",task["promotion_rule"].lower())
        self.assertFalse(any("p_value" in key.lower() or "confidence_interval" in key.lower() for key in results.keys()))


if __name__=="__main__":
    unittest.main()
