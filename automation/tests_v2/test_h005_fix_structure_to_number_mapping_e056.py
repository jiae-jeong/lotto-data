"""Contract tests for the isolated H005_FIX structure-to-number mapping."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import h005_fix_structure_to_number_mapping_e056_v1 as study

class H005FixTests(unittest.TestCase):
    def test_corrected_structure_vector_is_number_specific(self):
        v=study.corrected_structure_vector((1,7,13,19,25,45))
        self.assertEqual(len(v),45)
        self.assertEqual(sum(x==45 for x in v),6)
        self.assertEqual(sum(x==0 for x in v),39)
        self.assertEqual(v[0],45)
        self.assertEqual(v[1],0)
        self.assertEqual(v[44],45)

    def test_legacy_mapping_constant_is_not_number_specific(self):
        self.assertEqual(270.0/51.0,270.0/51.0)
        v=study.corrected_structure_vector((1,7,13,19,25,45))
        self.assertEqual(len(set(v)),2)
        self.assertNotEqual(len(set([270.0/51.0]*45)),2)

    def test_invalid_structure_ticket_rejected(self):
        with self.assertRaises(ValueError):
            study.corrected_structure_vector((1,1,2,3,4,5))
        with self.assertRaises(ValueError):
            study.corrected_structure_vector((0,1,2,3,4,5))

if __name__=="__main__": unittest.main()
