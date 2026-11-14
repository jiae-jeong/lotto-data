import importlib.util, json, random, unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"three_line_draw_state_transition_e049.py"
SPEC=importlib.util.spec_from_file_location("e049_runner",SCRIPT)
MODULE=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)

class E049FrozenSpecificationTests(unittest.TestCase):
    def test_state_and_hamming(self):
        self.assertEqual(MODULE.draw_state((1,2,3,4,5,6)),(0,1,2,2))
        self.assertEqual(MODULE.draw_state((10,12,14,16,24,26)),(0,0,1,0))
        self.assertEqual(MODULE.hamming_distance((0,1,2,2),(0,0,1,0)),3)
    def test_invalid_state_rejected(self):
        with self.assertRaises(ValueError): MODULE.draw_state((1,1,2,3,4,5))
        with self.assertRaises(ValueError): MODULE.draw_state((0,2,3,4,5,6))
    def test_fixed_kernel_and_shrinkage(self):
        scores,total=MODULE.score_numbers((0,0,0,0),[(0,0,0,0),(1,0,0,0)],[(1,2,3,4,5,6),(2,3,4,5,6,7)],[1]*45,10,60.0)
        self.assertAlmostEqual(total,1.5); self.assertAlmostEqual(scores[0],7/61.5)
        self.assertAlmostEqual(scores[1],7.5/61.5); self.assertAlmostEqual(scores[6],6.5/61.5)
        self.assertAlmostEqual(scores[7],6/61.5)
    def test_rank_interleaving_union18(self):
        lines=MODULE.shared.build_portfolio([float(46-n) for n in range(1,46)])
        self.assertEqual(lines,[(1,4,7,10,13,16),(2,5,8,11,14,17),(3,6,9,12,15,18)])
        MODULE.shared.validate_portfolio(lines)
    def test_random_label_permutation_geometry(self):
        lines=[(1,4,7,10,13,16),(2,5,8,11,14,17),(3,6,9,12,15,18)]
        x=MODULE.shared.permute_portfolio_labels(lines,random.Random(2026111404))
        MODULE.shared.validate_portfolio(x); self.assertEqual(len(set().union(*(set(z) for z in x))),18)
    def test_frozen_prereg_and_data_prefix(self):
        p=json.loads(MODULE.PREREG_PATH.read_text()); policy=json.loads(MODULE.POLICY_PATH.read_text())
        MODULE.validate_preregistration(p,policy)
        draws,prefix,full,total=MODULE.shared.read_frozen_prefix(1249,p["source_data_prefix_sha256"],p["source_data_full_file_sha256"])
        self.assertEqual(len(draws),1249); self.assertEqual(total,1249)
        self.assertEqual(prefix,p["source_data_prefix_sha256"]); self.assertEqual(full,p["source_data_full_file_sha256"])
    def test_shared_helper_is_pinned(self):
        self.assertEqual(MODULE.verify_shared_helper(),MODULE.SHARED_HELPER_GIT_BLOB_SHA)
    def test_bootstrap_deterministic(self):
        x=[float((i%7)-3) for i in range(123)]
        a=MODULE.shared.moving_block_ci(x,.0125,2026111404,400,50)
        b=MODULE.shared.moving_block_ci(x,.0125,2026111404,400,50)
        self.assertEqual(a,b); self.assertLessEqual(a[0],a[1])

if __name__=="__main__": unittest.main()
