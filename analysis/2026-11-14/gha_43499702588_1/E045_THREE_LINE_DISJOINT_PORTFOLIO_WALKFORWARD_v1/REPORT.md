# E045 — Target-1251 three-line disjoint portfolio walk-forward

Execution status: **COMPLETE**
Historical strict gate: **FAIL**
Purchase readiness: **NOT_READY**

## Frozen scope

- Historical data cutoff: 1249
- Walk-forward targets: 401–1249 (849 targets)
- Training cutoff: target round minus one; the target draw is not passed to the prediction function
- Portfolio geometry: exactly three pairwise-disjoint six-number lines; union size 18
- Random comparator: 120 uniformly label-permuted geometry-matched portfolios per target
- Total random bundles: 101,880
- Family alpha: 0.05; per-metric alpha: 0.0125
- Moving-block bootstrap: 4,000 replicates, 50-target blocks, final remainder retained
- Any2 positive block share threshold: 0.65

## Historical results

| Metric | Model mean | Exact null | Difference | Adjusted CI lower | Adjusted CI upper |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.492344 | 1.514256 | -0.021912 | -0.083161 | 0.032269 |
| any2 | 0.467609 | 0.474976 | -0.007367 | -0.046237 | 0.030324 |
| any3 | 0.058893 | 0.071355 | -0.012462 | -0.036019 | 0.005206 |
| winning_union_coverage | 2.382803 | 2.400000 | -0.017197 | -0.120848 | 0.072320 |

- Any2 positive 50-target block share: 0.470588
- Fixed block lengths: [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 49]
- Historical gate result: **FAIL**
- Prospective confirmation: **required, but minimum target count and completion rule are unspecified**
- STRICT_PASS_READY: **not created**
- Final purchase lines: **not generated**
- Random fallback: **prohibited**

This is one preregistered allocator axis, not a claim of independent signal-family discovery. No model variants, parameter changes, alpha changes, block-size changes, or comparator changes were tested.
