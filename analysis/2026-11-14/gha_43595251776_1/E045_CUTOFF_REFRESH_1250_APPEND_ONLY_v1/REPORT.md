# E045 cutoff refresh — target-1251 three-line disjoint portfolio walk-forward (append-only; not independent)

Execution status: **COMPLETE**
Historical strict gate: **FAIL**
Purchase readiness: **NOT_READY**

## Frozen scope

- Historical data cutoff: 1250
- Walk-forward targets: 401–1250 (850 targets)
- Training cutoff: target round minus one; the target draw is not passed to the prediction function
- Portfolio geometry: exactly three pairwise-disjoint six-number lines; union size 18
- Random comparator: 120 uniformly label-permuted geometry-matched portfolios per target
- Total random bundles: 102,000
- Family alpha: 0.05; per-metric alpha: 0.0125
- Moving-block bootstrap: 4,000 replicates, 50-target blocks, final remainder retained
- Any2 positive block share threshold: 0.65

## Historical results

| Metric | Model mean | Exact null | Difference | Adjusted CI lower | Adjusted CI upper |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.491765 | 1.514256 | -0.022492 | -0.083668 | 0.032803 |
| any2 | 0.467059 | 0.474976 | -0.007917 | -0.045564 | 0.028553 |
| any3 | 0.058824 | 0.071355 | -0.012531 | -0.036061 | 0.006292 |
| winning_union_coverage | 2.383529 | 2.400000 | -0.016471 | -0.123529 | 0.069412 |

- Any2 positive 50-target block share: 0.470588
- Fixed block lengths: [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
- Historical gate result: **FAIL**
- Prospective confirmation: **required, but minimum target count and completion rule are unspecified**
- STRICT_PASS_READY: **not created**
- Final purchase lines: **not generated**
- Random fallback: **prohibited**

This is one preregistered allocator axis, not a claim of independent signal-family discovery. No model variants, parameter changes, alpha changes, block-size changes, or comparator changes were tested.
