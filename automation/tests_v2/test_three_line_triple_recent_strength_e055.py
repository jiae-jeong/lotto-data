"""Contract tests for E055 triple recent-strength falsification."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import three_line_triple_recent_strength_e055_v1 as study

class E055Tests(unittest.TestCase):
    def test_fifteen_nonoverlapping_forward_blocks_and_prior_windows(self):
        specs=study.block_specs()
        self.assertEqual(len(specs),15)
        self.assertEqual(specs[0]["trailing_start_target"],401)
        self.assertEqual(specs[0]["trailing_end_target"],500)
        self.assertEqual(specs[0]["forward_start_target"],501)
        self.assertEqual(specs[-1]["trailing_start_target"],1101)
        self.assertEqual(specs[-1]["trailing_end_target"],1200)
        self.assertEqual(specs[-1]["forward_start_target"],1201)
        self.assertEqual(specs[-1]["forward_end_target"],1250)

    def test_pearson_perfect_positive_and_negative(self):
        self.assertAlmostEqual(study.pearson([1,2,3,4],[2,4,6,8]),1.0)
        self.assertAlmostEqual(study.pearson([1,2,3,4],[8,6,4,2]),-1.0)

    def test_zero_variance_is_conservatively_zero(self):
        self.assertEqual(study.pearson([1,1,1,1],[2,3,4,5]),0.0)

    def test_trailing_rate_uses_only_pre_block_values(self):
        original=[0,1]*50+[1]*50
        changed=original[:]
        changed[100:]=[0]*100
        self.assertEqual(study.trailing_rate(original,100),study.trailing_rate(changed,100))
        self.assertEqual(study.trailing_rate(original,100),0.5)

    def test_moving_block_correlation_interval_is_reproducible(self):
        pairs=[(i/20,(i%4)/4) for i in range(15)]
        a=study.moving_block_corr_ci(pairs,replicates=300,seed=123)
        b=study.moving_block_corr_ci(pairs,replicates=300,seed=123)
        self.assertEqual(a,b)
        self.assertEqual(len(a),2)
        self.assertLessEqual(a[0],a[1])

if __name__=="__main__": unittest.main()
