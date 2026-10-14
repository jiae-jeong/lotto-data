import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import orthogonal_research_v2 as study


class OrthogonalResearchTests(unittest.TestCase):
    def test_preregistration_has_four_distinct_families_and_protected_scope(self):
        spec=json.loads(study.PREREG.read_text(encoding="utf-8"))
        self.assertEqual(len(spec["candidate_families"]),4)
        self.assertEqual(spec["canonical_cutoff"],1245)
        self.assertTrue(spec["no_E010_E029_reruns"])
        self.assertEqual(spec["E035_rule"].split()[0],"Run")

    def test_data_integrity_is_1_through_1245(self):
        rows=study.load_data()
        self.assertEqual(len(rows),1245)
        self.assertEqual(rows[0]["round"],1)
        self.assertEqual(rows[-1]["round"],1245)
        self.assertTrue(all(len(set(x["numbers"]))==6 for x in rows))

    def test_frozen_ticket_tie_break_prefers_lower_numbers(self):
        import numpy as np
        self.assertEqual(study._ticket(np.zeros(45)),(1,2,3,4,5,6))

    def test_residual_signal_has_pre_target_history_at_first_scored_cutoff(self):
        draws=study.load_data(); b=study.load_b()
        residuals=study._prequential_residuals(draws,b)
        self.assertEqual(min(residuals),201)
        self.assertEqual(max(residuals),1244)
        scores=study._crossfit_residual_scores(draws,b,601,residuals)
        self.assertEqual(scores.shape,(45,))

    def test_holm_adjustment_is_monotonic_and_bounded(self):
        adjusted=study._holm([.01,.04,.03])
        self.assertTrue(all(0<=x<=1 for x in adjusted))
        self.assertGreaterEqual(adjusted[0],.01)
        self.assertEqual(adjusted[1],.06)

    def test_bootstrap_repeats_exactly_with_frozen_seed(self):
        import numpy as np
        values=np.array([.1,-.2,.3,0.0]*30)
        self.assertEqual(study._bootstrap(values,44,reps=100),study._bootstrap(values,44,reps=100))

    def test_run_id_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            study.run(study.ROOT,"2026-10-14","../unsafe")


if __name__=="__main__":
    unittest.main()
