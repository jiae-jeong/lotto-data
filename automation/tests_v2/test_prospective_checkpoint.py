import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prospective_checkpoint_v1 as checkpoint


class ProspectiveCheckpointTests(unittest.TestCase):
    def test_200_target_interim_miss_is_insufficient_not_rejected(self):
        self.assertEqual(checkpoint.checkpoint_status(199,False),"PROSPECTIVE_PENDING")
        self.assertEqual(checkpoint.checkpoint_status(200,False),"PROSPECTIVE_INSUFFICIENT_EVIDENCE")
        self.assertEqual(checkpoint.checkpoint_status(200,False,False,True),"PROSPECTIVE_INSUFFICIENT_EVIDENCE")

    def test_promotion_requires_complete_registered_gates(self):
        values=[0.01]*200
        passed=checkpoint.promotion_gates(values,values,[0.0]*200,values,50.0,50.0,shadow_e_value=100.0)
        self.assertTrue(passed["pass"])
        harmed=checkpoint.promotion_gates(values,values,[-0.01]*200,values,50.0,50.0,shadow_e_value=100.0)
        self.assertFalse(harmed["pass"])
        self.assertFalse(checkpoint.promotion_gates(values[:199],values[:199],values[:199],values[:199],50.0,50.0,shadow_e_value=100.0)["pass"])

    def test_rejected_requires_separately_registered_futility_rule(self):
        self.assertEqual(checkpoint.checkpoint_status(200,False,False,True),"PROSPECTIVE_INSUFFICIENT_EVIDENCE")
        self.assertEqual(checkpoint.checkpoint_status(200,False,True,True),"REJECTED")
        self.assertEqual(checkpoint.checkpoint_status(200,True),"PROSPECTIVE_VALIDATED_EDGE")

    def test_workflow_output_commits_do_not_retrigger_the_same_workflow(self):
        workflow=(Path(__file__).resolve().parents[2]/".github/workflows/prospective-ledger-update.yml").read_text(encoding="utf-8")
        self.assertIn("analysis/prospective_v1/purchases/intake/**",workflow)
        self.assertNotIn("analysis/prospective_v1/**",workflow)
        self.assertNotIn("analysis/prospective_v1/purchases/ROUND_",workflow)


if __name__=="__main__":
    unittest.main()

