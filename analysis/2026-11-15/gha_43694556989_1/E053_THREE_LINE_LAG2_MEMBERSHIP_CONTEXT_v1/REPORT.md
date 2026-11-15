# E053 — Two-draw membership-state conditional inclusion model

- Study status: **STRICT_FAIL**
- Data cutoff: **1250**; source rows: **1250**
- Walk-forward targets: **850** (401..1250)
- Random bundles: **102,000** (120 per target)
- Feature: candidate membership pattern across the two immediately preceding main draws; bonus excluded
- Estimator: one fixed Beta-smoothed inclusion probability with prior mean 6/45 and prior strength 45
- Portfolio: three pairwise-disjoint six-number lines, union18, using the unchanged E045 selector
- Randomness is used only for the geometry-matched null, never for selection

| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.482353 | 1.514256 | -0.031903 | -0.095433 | +0.036332 |
| any2 | 0.461176 | 0.474976 | -0.013800 | -0.051447 | +0.042671 |
| any3 | 0.062353 | 0.071355 | -0.009002 | -0.030178 | +0.010998 |
| winning_union_coverage | 2.385882 | 2.400000 | -0.014118 | -0.101176 | +0.067059 |

- any2-positive 50-target block share: **47.06%** (8/17 blocks)
- Historical strict gate: **FAIL**
- STRICT_PASS_READY: **not created**
- Prospective minimum/completion rule: **unspecified and not adopted**
- No final purchase lines, recommendation, or freeze/seal were generated.

Each target is scored before its outcome enters the lag-two membership transition counts. One frozen signal family, one estimator, no variants or tuning.
