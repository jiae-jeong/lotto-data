import unittest
from automation.three_line_calendar_month_frequency_e074 import calendar_month_scores, make_portfolio, month_from_date

class CalendarMonthFrequencyE074Tests(unittest.TestCase):
    def test_month_parser(self):
        self.assertEqual(month_from_date("2026.11.14"),11)
        self.assertEqual(month_from_date("2026-02-07"),2)

    def test_only_prior_draws_in_target_month_contribute(self):
        prior=[
            {"round":1,"month":1,"nums":(1,2,3,4,5,6)},
            {"round":2,"month":2,"nums":(1,7,8,9,10,11)},
            {"round":3,"month":1,"nums":(2,3,4,5,6,7)},
        ]
        scores,exposure=calendar_month_scores(prior,1)
        self.assertEqual(exposure,2)
        self.assertAlmostEqual(scores[1],7/47)
        self.assertAlmostEqual(scores[2],8/47)
        self.assertAlmostEqual(scores[7],7/47)
        self.assertAlmostEqual(scores[8],6/47)

    def test_empty_history_uses_fixed_uniform_beta_prior(self):
        scores,exposure=calendar_month_scores([],11)
        self.assertEqual(exposure,0)
        self.assertTrue(all(abs(x-6/45)<1e-15 for x in scores.values()))

    def test_ties_are_ascending_number(self):
        scores,_=calendar_month_scores([],7)
        self.assertEqual(make_portfolio(scores),[
            (1,2,3,4,5,6),(7,8,9,10,11,12),(13,14,15,16,17,18)
        ])

    def test_three_disjoint_lines_union18(self):
        scores={n:float(46-n) for n in range(1,46)}
        lines=make_portfolio(scores)
        self.assertEqual(len(set().union(*(set(x) for x in lines))),18)
        self.assertTrue(all(len(x)==6 for x in lines))
        self.assertTrue(all(not(set(lines[i])&set(lines[j])) for i in range(3) for j in range(i+1,3)))

    def test_future_mutation_outside_prior_prefix_cannot_change_scores(self):
        prior=[{"round":1,"month":11,"nums":(1,2,3,4,5,6)},
               {"round":2,"month":10,"nums":(7,8,9,10,11,12)},
               {"round":3,"month":11,"nums":(2,3,4,5,6,7)}]
        before=calendar_month_scores(prior,11)
        later=prior+[{"round":4,"month":11,"nums":(40,41,42,43,44,45)}]
        after=calendar_month_scores(later[:3],11)
        self.assertEqual(before,after)

if __name__=="__main__": unittest.main()
