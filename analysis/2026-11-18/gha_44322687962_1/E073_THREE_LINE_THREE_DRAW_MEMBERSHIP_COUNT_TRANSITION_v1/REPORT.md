# E073 — Three-draw membership-count conditional inclusion model

- Study status: **STRICT_FAIL**
- Data cutoff: **1250**; source rows: **1250**
- Walk-forward targets: **850** (401..1250)
- Random bundles: **102,000** (120 per target)
- Feature: candidate membership count across the three immediately preceding main draws; bonus excluded
- Estimator: one fixed Beta-smoothed inclusion probability with prior mean 6/45 and prior strength 45
- Portfolio: three pairwise-disjoint six-number lines, union18, using the unchanged E045 selector
- Randomness is used only for the geometry-matched null, never for selection

| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.508235 | 1.514256 | -0.006021 | -0.073080 | +0.063391 |
| any2 | 0.472941 | 0.474976 | -0.002035 | -0.049094 | +0.049730 |
| any3 | 0.071765 | 0.071355 | +0.000410 | -0.020767 | +0.019233 |
| winning_union_coverage | 2.410588 | 2.400000 | +0.010588 | -0.081176 | +0.116471 |

- any2-positive 50-target block share: **58.82%** (10/17 blocks)
- Historical strict gate: **FAIL**
- STRICT_PASS_READY: **not created**
- Prospective minimum/completion rule: **unspecified and not adopted**
- No final purchase lines, recommendation, or freeze/seal were generated.

Each target is scored before its outcome enters the lag-three membership transition counts. One frozen signal family, one estimator, no variants or tuning.
