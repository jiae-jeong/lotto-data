# Can any frozen five-line construction strategy repeatedly outperform same-target random five-line bundles?

## MAINTENANCE/RECHECK

Canonical data and the frozen seven-component B forecast cache were read as provenance-controlled inputs. No E010-E024 study was rerun.

## NEW STUDY

Every target receives seven fixed candidate-bank strategies, a same-target RANDOM_5_LINES baseline from 100 random bundles, and the nested selector for targets 801..1245. The selector uses only the preceding 200 target outcomes to choose among the seven frozen construction strategies; all candidate lines and overlaps are created before the target outcome is scored.

## NEW FINDING

Five-line outcomes are compared against five random lines on identical target rounds. This historical replay is exploratory and does not change the current five-line operational rule.

## Results

```json
{
  "summary": [
    {
      "strategy": "TOP_5",
      "target_count": 645,
      "max_hits": 1.572093023255814,
      "any_2plus": 0.5224806201550387,
      "any_3plus": 0.07751937984496124,
      "any_4plus": 0.009302325581395349,
      "any_5plus": 0,
      "any_6": 0,
      "winning_union_coverage": 0.3891472868217054,
      "unique_number_coverage": 17.829457364341085,
      "mean_pairwise_overlap": 1.83984496124031,
      "line_hit_variance": 0.3801550387596899
    },
    {
      "strategy": "MIN_OVERLAP_5",
      "target_count": 645,
      "max_hits": 1.710077519379845,
      "any_2plus": 0.6356589147286822,
      "any_3plus": 0.08062015503875969,
      "any_4plus": 0.004651162790697674,
      "any_5plus": 0,
      "any_6": 0,
      "winning_union_coverage": 0.5335917312661499,
      "unique_number_coverage": 24.928682170542636,
      "mean_pairwise_overlap": 0.5344186046511628,
      "line_hit_variance": 0.487937984496124
    },
    {
      "strategy": "MID_OVERLAP_5",
      "target_count": 645,
      "max_hits": 1.6651162790697673,
      "any_2plus": 0.5813953488372093,
      "any_3plus": 0.08527131782945736,
      "any_4plus": 0.009302325581395349,
      "any_5plus": 0,
      "any_6": 0,
      "winning_union_coverage": 0.45529715762273903,
      "unique_number_coverage": 20.685271317829457,
      "mean_pairwise_overlap": 1.1531782945736435,
      "line_hit_variance": 0.45097674418604655
    },
    {
      "strategy": "HIGH_OVERLAP_5",
      "target_count": 645,
      "max_hits": 1.5410852713178294,
      "any_2plus": 0.5054263565891473,
      "any_3plus": 0.07751937984496124,
      "any_4plus": 0.007751937984496124,
      "any_5plus": 0,
      "any_6": 0,
      "winning_union_coverage": 0.37002583979328163,
      "unique_number_coverage": 17.148837209302325,
      "mean_pairwise_overlap": 2.014108527131783,
      "line_hit_variance": 0.3715968992248062
    },
    {
      "strategy": "SOURCE_DIVERSITY_5",
      "target_count": 645,
      "max_hits": 1.572093023255814,
      "any_2plus": 0.5224806201550387,
      "any_3plus": 0.07751937984496124,
      "any_4plus": 0.009302325581395349,
      "any_5plus": 0,
      "any_6": 0,
      "winning_union_coverage": 0.3891472868217054,
      "unique_number_coverage": 17.829457364341085,
      "mean_pairwise_overlap": 1.83984496124031,
      "line_hit_variance": 0.3801550387596899
    },
    {
      "strategy": "INDEPENDENT_SIGNAL_CENTRED_5",
      "target_count": 645,
      "max_hits": 1.572093023255814,
      "any_2plus": 0.5224806201550387,
      "any_3plus": 0.07751937984496124,
      "any_4plus": 0.009302325581395349,
      "any_5plus": 0,
      "any_6": 0,
      "winning_union_coverage": 0.3891472868217054,
      "unique_number_coverage": 17.829457364341085,
      "mean_pairwise_overlap": 1.83984496124031,
      "line_hit_variance": 0.3801550387596899
    },
    {
      "strategy": "B_PLUS_INDEPENDENT_MIX_5",
      "target_count": 645,
      "max_hits": 1.572093023255814,
      "any_2plus": 0.5224806201550387,
      "any_3plus": 0.07751937984496124,
      "any_4plus": 0.009302325581395349,
      "any_5plus": 0,
      "any_6": 0,
      "winning_union_coverage": 0.3891472868217054,
      "unique_number_coverage": 17.829457364341085,
      "mean_pairwise_overlap": 1.83984496124031,
      "line_hit_variance": 0.3801550387596899
    },
    {
      "strategy": "RANDOM_5_LINES",
      "target_count": 645,
      "max_hits": 1.7286046511627906,
      "any_2plus": 0.6170542635658914,
      "any_3plus": 0.11438759689922481,
      "any_4plus": 0.006837209302325582,
      "any_5plus": 0.00010852713178294573,
      "any_6": 0.0,
      "winning_union_coverage": 0.5113410852713178,
      "unique_number_coverage": 23.000883720930233,
      "mean_pairwise_overlap": 0.7995457364341085,
      "line_hit_variance": 0.49077457364341087
    },
    {
      "strategy": "NESTED_DYNAMIC_5",
      "target_count": 445,
      "max_hits": 1.6067415730337078,
      "any_2plus": 0.5640449438202247,
      "any_3plus": 0.060674157303370786,
      "any_4plus": 0.0044943820224719105,
      "any_5plus": 0,
      "any_6": 0,
      "winning_union_coverage": 0.45205992509363296,
      "unique_number_coverage": 20.669662921348316,
      "mean_pairwise_overlap": 1.243820224719101,
      "line_hit_variance": 0.41186516853932587
    }
  ],
  "verification": {
    "status": "PASS",
    "target_count": 645,
    "random_portfolios": 64500,
    "random_portfolios_per_target": 100,
    "fixed_strategies": [
      "TOP_5",
      "MIN_OVERLAP_5",
      "MID_OVERLAP_5",
      "HIGH_OVERLAP_5",
      "SOURCE_DIVERSITY_5",
      "INDEPENDENT_SIGNAL_CENTRED_5",
      "B_PLUS_INDEPENDENT_MIX_5"
    ],
    "nested_dynamic_targets": 445,
    "nested_history_targets": 200,
    "portfolio_line_rows": 24800,
    "cutoff_violations": 0,
    "future_outcomes_used_in_candidate_bank": false,
    "future_outcomes_used_in_dynamic_choice": false,
    "future_predictions": 0
  }
}
```

## NEXT TEST

Retain this specification and require the independent promotion gate; do not use the historical result to generate a recommendation.
