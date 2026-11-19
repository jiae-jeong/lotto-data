# Does vote depth across seven frozen B component tickets associate with OOS winning-number membership under round-clustered uncertainty?

## MAINTENANCE/RECHECK

Existing B component forecasts are reused only as the frozen, cutoff-safe input panel; this is not a new B reproduction.

## NEW STUDY

Vote depths are computed from seven frozen B component tickets before each target; outcomes are evaluated as round-clustered 45-number vectors. Uniform random reference uses repeated seven-ticket random ensembles per target.

## NEW FINDING

Depth calibration is descriptive and retrospective. Cluster bootstrap preserves within-round dependence; no naive binomial test treats 45 numbers as independent.

## Results

```json
[
  {
    "vote_depth": 0,
    "number_round_cells": 11435,
    "winning_memberships": 1582,
    "empirical_hit_probability": 0.13834717971141233,
    "unique_target_rounds": 645,
    "uniform_number_probability": 0.13333333333333333,
    "random_ensemble_cells": 1064493,
    "random_winning_memberships": 142616,
    "random_empirical_hit_probability": 0.13397551698320234,
    "cluster_bootstrap_ci95_low": 0.13356643356643358,
    "cluster_bootstrap_ci95_high": 0.14343116701607267,
    "bootstrap_replicates": 2000
  },
  {
    "vote_depth": 1,
    "number_round_cells": 10657,
    "winning_memberships": 1403,
    "empirical_hit_probability": 0.1316505583184761,
    "unique_target_rounds": 645,
    "uniform_number_probability": 0.13333333333333333,
    "random_ensemble_cells": 1150031,
    "random_winning_memberships": 152841,
    "random_empirical_hit_probability": 0.132901634825496,
    "cluster_bootstrap_ci95_low": 0.1265550463006267,
    "cluster_bootstrap_ci95_high": 0.13699400299850076,
    "bootstrap_replicates": 2000
  },
  {
    "vote_depth": 2,
    "number_round_cells": 4910,
    "winning_memberships": 635,
    "empirical_hit_probability": 0.12932790224032586,
    "unique_target_rounds": 645,
    "uniform_number_probability": 0.13333333333333333,
    "random_ensemble_cells": 529757,
    "random_winning_memberships": 70469,
    "random_empirical_hit_probability": 0.13302136640006645,
    "cluster_bootstrap_ci95_low": 0.12054399340614053,
    "cluster_bootstrap_ci95_high": 0.1383699445699035,
    "bootstrap_replicates": 2000
  },
  {
    "vote_depth": 3,
    "number_round_cells": 1558,
    "winning_memberships": 191,
    "empirical_hit_probability": 0.12259306803594351,
    "unique_target_rounds": 603,
    "uniform_number_probability": 0.13333333333333333,
    "random_ensemble_cells": 135575,
    "random_winning_memberships": 17954,
    "random_empirical_hit_probability": 0.1324285450857459,
    "cluster_bootstrap_ci95_low": 0.10646387832699619,
    "cluster_bootstrap_ci95_high": 0.13862024500322373,
    "bootstrap_replicates": 2000
  },
  {
    "vote_depth": 4,
    "number_round_cells": 389,
    "winning_memberships": 52,
    "empirical_hit_probability": 0.13367609254498714,
    "unique_target_rounds": 289,
    "uniform_number_probability": 0.13333333333333333,
    "random_ensemble_cells": 20579,
    "random_winning_memberships": 2857,
    "random_empirical_hit_probability": 0.138830846979931,
    "cluster_bootstrap_ci95_low": 0.10187667560321716,
    "cluster_bootstrap_ci95_high": 0.16793893129770993,
    "bootstrap_replicates": 2000
  },
  {
    "vote_depth": 5,
    "number_round_cells": 73,
    "winning_memberships": 7,
    "empirical_hit_probability": 0.0958904109589041,
    "unique_target_rounds": 70,
    "uniform_number_probability": 0.13333333333333333,
    "random_ensemble_cells": 1976,
    "random_winning_memberships": 251,
    "random_empirical_hit_probability": 0.1270242914979757,
    "cluster_bootstrap_ci95_low": 0.03488372093023256,
    "cluster_bootstrap_ci95_high": 0.16901408450704225,
    "bootstrap_replicates": 2000
  },
  {
    "vote_depth": 6,
    "number_round_cells": 3,
    "winning_memberships": 0,
    "empirical_hit_probability": 0.0,
    "unique_target_rounds": 3,
    "uniform_number_probability": 0.13333333333333333,
    "random_ensemble_cells": 89,
    "random_winning_memberships": 12,
    "random_empirical_hit_probability": 0.1348314606741573,
    "cluster_bootstrap_ci95_low": 0.0,
    "cluster_bootstrap_ci95_high": 0.0,
    "bootstrap_replicates": 2000
  },
  {
    "vote_depth": 7,
    "number_round_cells": 0,
    "winning_memberships": 0,
    "empirical_hit_probability": null,
    "unique_target_rounds": 0,
    "uniform_number_probability": 0.13333333333333333,
    "random_ensemble_cells": 0,
    "random_winning_memberships": 0,
    "random_empirical_hit_probability": null,
    "cluster_bootstrap_ci95_low": null,
    "cluster_bootstrap_ci95_high": null,
    "bootstrap_replicates": 2000
  }
]
```

## Verification

```json
{
  "status": "PASS",
  "targets": 645,
  "cluster_rows": 29025,
  "random_ensembles_per_target": 100,
  "bootstrap_unit": "target round; all 45 number outcomes retained within cluster",
  "bootstrap_replicates": 2000,
  "naive_number_independence_test": "NOT USED",
  "future_predictions": 0
}
```

## NEXT TEST

Retain the frozen experiment and seek independent prospective evidence. Do not tune this result into a future recommendation.
