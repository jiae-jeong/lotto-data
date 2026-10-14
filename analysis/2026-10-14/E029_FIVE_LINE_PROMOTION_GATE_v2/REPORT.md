# Does the nested five-line selector meet every pre-registered promotion gate versus same-target random five-line bundles?

## MAINTENANCE/RECHECK

Canonical data and the frozen seven-component B forecast cache were read as provenance-controlled inputs. No E010-E024 study was rerun.

## NEW STUDY

The registered nested 200-target selector was compared with 100 same-target random five-line portfolios on targets 801..1245. Primary tests were paired block-bootstrap differences for any_3plus and max_hits with Holm correction across those two tests. The gate also required non-worse any_4plus, chronological block consistency, zero leakage, and positive effects after removing the best 50-target block.

## NEW FINDING

Promotion is allowed only if every check passes. A failed gate preserves five lines as the operational count and keeps this selector out of use.

## Results

```json
{
  "promotion_gate": {
    "promotion_status": "DO_NOT_PROMOTE",
    "data_cutoff": 1245,
    "operational_ticket_count": 5,
    "selector": "NESTED_DYNAMIC_5",
    "comparison": "same-target 100-random-bundle mean; targets 801..1245",
    "primary_metrics": [
      "any_3plus",
      "max_hits"
    ],
    "multiplicity_correction": "Holm step-down across the two registered primary tests",
    "checks": {
      "positive_ci_any_3plus": false,
      "positive_ci_max_hits": false,
      "holm_adjusted_primary_tests_below_0_05": false,
      "any_4plus_not_worse_point_and_ci": false,
      "block_direction_stable": false,
      "not_driven_by_best_50_round_block": false,
      "leakage_zero": true,
      "at_least_one_independent_signal_survived": true,
      "nested_targets": 445,
      "bootstrap_reps": 2000
    },
    "leave_best_50_target_block_out": {
      "any_3plus": {
        "removed_start": 1101,
        "removed_end": 1150,
        "remaining_delta": -0.058911392405063295
      },
      "max_hits": {
        "removed_start": 901,
        "removed_end": 950,
        "remaining_delta": -0.14169620253164555
      }
    },
    "future_predictions": 0,
    "recommendation_generation": false
  },
  "primary_tests": [
    {
      "strategy": "NESTED_DYNAMIC_5",
      "metric": "max_hits",
      "targets": 445,
      "model_mean": 1.6067415730337078,
      "random5_mean": 1.7284494382022473,
      "estimate": -0.12170786516853932,
      "ci95_low": -0.1939101123595507,
      "ci95_high": -0.05525842696629214,
      "p_two_sided": 0.001999000499750125,
      "p_greater": 0.9985007496251874,
      "bootstrap_reps": 2000,
      "block_length": 20,
      "comparison_family": "PRIMARY_NESTED_DYNAMIC",
      "p_raw": 0.9985007496251874,
      "p_holm": 1.0
    },
    {
      "strategy": "NESTED_DYNAMIC_5",
      "metric": "any_3plus",
      "targets": 445,
      "model_mean": 0.060674157303370786,
      "random5_mean": 0.11451685393258428,
      "estimate": -0.05384269662921348,
      "ci95_low": -0.07332584269662915,
      "ci95_high": -0.033685393258427024,
      "p_two_sided": 0.0004997501249375312,
      "p_greater": 1.0,
      "bootstrap_reps": 2000,
      "block_length": 20,
      "comparison_family": "PRIMARY_NESTED_DYNAMIC",
      "p_raw": 1.0,
      "p_holm": 1.0
    }
  ],
  "any_4plus": {
    "strategy": "NESTED_DYNAMIC_5",
    "metric": "any_4plus",
    "targets": 445,
    "model_mean": 0.0044943820224719105,
    "random5_mean": 0.006584269662921348,
    "estimate": -0.002089887640449438,
    "ci95_low": -0.006651685393258404,
    "ci95_high": 0.004471910112359562,
    "p_two_sided": 0.5087456271864068,
    "p_greater": 0.7211394302848576,
    "bootstrap_reps": 2000,
    "block_length": 20,
    "comparison_family": "EXPLORATORY",
    "p_raw": null,
    "p_holm": null
  }
}
```

## NEXT TEST

Retain this specification and require the independent promotion gate; do not use the historical result to generate a recommendation.
