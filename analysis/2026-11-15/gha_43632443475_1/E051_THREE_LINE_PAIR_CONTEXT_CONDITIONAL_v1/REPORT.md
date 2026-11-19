# E051 — Pair-context conditional number-inclusion model

- Study status: **STRICT_FAIL**
- Data cutoff: **1250**; source rows: **1250**
- Walk-forward targets: **850** (401..1250)
- Random bundles: **102,000** (120 per target)
- Feature: 15 unordered pairs in the immediately preceding main draw; bonus excluded
- Estimator: Beta-smoothed candidate inclusion probability with prior mean 6/45 and fixed strength 50
- Portfolio: three pairwise-disjoint six-number lines, union18
- Randomness is used only for the geometry-matched null, never for selection

| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.498824 | 1.514256 | -0.015433 | -0.076609 | +0.056332 |
| any2 | 0.465882 | 0.474976 | -0.009094 | -0.043212 | +0.035612 |
| any3 | 0.069412 | 0.071355 | -0.001943 | -0.020767 | +0.015704 |
| winning_union_coverage | 2.381176 | 2.400000 | -0.018824 | -0.136471 | +0.109412 |

- any2-positive 50-target block share: **41.18%** (7/17 blocks)
- Historical strict gate: **FAIL**
- STRICT_PASS_READY: **not created**
- Prospective minimum/completion rule: **unspecified and not adopted**
- No final purchase lines, recommendation, or freeze/seal were generated.

Each target is scored before its outcome enters pair-context exposure/success counts. One frozen specification, one estimator, no variants or tuning.
