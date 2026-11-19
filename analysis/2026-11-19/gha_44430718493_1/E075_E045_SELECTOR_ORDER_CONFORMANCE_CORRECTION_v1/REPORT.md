# E075 — E045 selector-order implementation-conformance correction

Execution status: **COMPLETE**
Historical E045 legacy gate: **FAIL**
Corrected historical gate: **FAIL**
Purchase readiness: **NOT_READY**

## Frozen scope

- Historical data cutoff: 1250; targets 401–1250 (850)
- Training cutoff: target round minus one; both selectors receive the same pre-target predictions and scores
- Candidate-pool ranking rule: identical top-16 ordering formula; first-role pool mismatches: 0; downstream pool-content differences after earlier line selections: 7/2100 (two later-role comparisons per 1,050 warmup-plus-scored targets)
- Correction: compute consecutive pairs and lexicographic tie-break on sorted ticket values, as the E045 preregistration specifies
- Unchanged: model predictions, role order, role/global scores, top-16 candidate-pool ranking rule, objective weights, line order, disjoint union18 geometry, exact null, random seed, alpha, block length, bootstrap count, strict thresholds
- Random comparator: 120 shared label-permutation maps per target and per version (102,000 per version)
- Moving-block bootstrap: 4,000 replicates; 50-target blocks; final remainder retained
- Any2 positive block threshold: 0.65

## Implementation audit

- Legacy selected-ticket adjacency-order mismatches: 1229/3150 selector decisions
- Targets with one or more changed lines: 5/1050 (warmup-plus-scored selector targets; outcome metrics use 850 targets)
- Changed line assignments: 10/3150 selector decisions
- Candidate-pool ranking rule changed: **NO**; first-role candidate pool mismatches: 0. Later available pools can differ because each portfolio has its own prior selected lines.

## Historical metrics

| Metric | Legacy delta vs exact null | Corrected delta vs exact null | Corrected minus legacy | Paired CI |
|---|---:|---:|---:|---:|
| max_hits | -0.022492 | -0.022492 | 0.000000 | [0.000000, 0.000000] |
| any2 | -0.007917 | -0.007917 | 0.000000 | [0.000000, 0.000000] |
| any3 | -0.012531 | -0.012531 | 0.000000 | [0.000000, 0.000000] |
| winning_union_coverage | -0.016471 | -0.016471 | 0.000000 | [0.000000, 0.000000] |

- Legacy any2-positive block share: 0.470588
- Corrected any2-positive block share: 0.470588
- Legacy historical gate: **FAIL**
- Corrected historical gate: **FAIL**
- Prospective confirmation: **required; minimum target count and completion rule remain unspecified**
- STRICT_PASS_READY: **not created**
- Final purchase lines: **not generated**
- Random fallback: **prohibited**

This is an implementation-conformance correction, not an independent signal-family discovery or prospective confirmation. The original E045 runner and outputs remain unchanged. No model, weight, threshold, or parameter search was performed.
