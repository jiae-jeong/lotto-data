"""Contract tests for E054 rolling concentration regime."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import three_line_rolling_concentration_regime_e054_v1 as study

def synthetic_draws(count=500):
    return [{"nums":tuple(((r*6+i)%45)+1 for i in range(6))} for r in range(count)]

class E054Tests(unittest.TestCase):
    def test_hhi_series_contains_only_full_windows(self):
        h=study.build_hhi_series(synthetic_draws(250))
        self.assertEqual((min(h),max(h)),(100,250))
        self.assertTrue(all(1/45 <= x <= 1 for x in h.values()))

    def test_target_401_uses_200_prior_nonoverlapping_windows(self):
        d=study.regime_details(401,study.build_hhi_series(synthetic_draws()))
        self.assertEqual(d["current_window_end_round"],400)
        self.assertEqual(d["reference_start_end_round"],101)
        self.assertEqual(d["reference_end_end_round"],300)
        self.assertEqual(d["reference_count"],200)

    def test_future_draw_mutations_do_not_change_target_401_regime(self):
        a=synthetic_draws(); b=synthetic_draws()
        for i in range(400,500): b[i]={"nums":tuple(range(40,46))}
        self.assertEqual(study.regime_details(401,study.build_hhi_series(a)),
                         study.regime_details(401,study.build_hhi_series(b)))

    def test_earliest_historical_regime_has_only_prior_inputs(self):
        d=study.regime_details(301,study.build_hhi_series(synthetic_draws()))
        self.assertEqual(d["current_window_end_round"],300)
        self.assertEqual(d["reference_count"],101)
        self.assertEqual(d["reference_end_end_round"],200)

    def test_beta_smoothing_and_exposure_updates(self):
        e=[[0]*46 for _ in range(2)]; s=[[0]*46 for _ in range(2)]
        initial=study.regime_scores(0,e,s)
        self.assertTrue(all(abs(x-6/45)<1e-12 for x in initial.values()))
        study.update_counts(1,(1,2,3,4,5,6),e,s)
        self.assertTrue(all(e[1][n]==1 for n in range(1,46)))
        self.assertEqual(sum(s[1]),6)
        self.assertGreater(study.regime_scores(1,e,s)[1],6/45)

    def test_portfolio_is_three_disjoint_lines(self):
        base=study.load_base(); scores={n:1.0 for n in range(1,46)}
        lines=study.make_portfolio(scores,base)
        self.assertEqual(len(lines),3)
        self.assertEqual(len(set().union(*(set(x) for x in lines))),18)
        self.assertTrue(all(len(x)==6 for x in lines))

if __name__=="__main__": unittest.main()
