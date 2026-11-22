# E079 independent re-execution audit (2026-11-22)

Evidence class: historical rolling walk-forward diagnostic only. Targets 1244-1249 are contaminated live-history diagnostics; this is not a clean holdout or prospective confirmation.

## Integrity and reproducibility
- Canonical source: lotto_data.csv, 1,250 contiguous draws through cutoff 1250; SHA-256 7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2; Git blob 66431d711919f179e4cb1349e2f7295c68a8735e.
- The frozen prefix through 1249 hashes to a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7. One internal blank physical line is present after round 1245; the frozen parser filters blank lines, so the logical 1..1250 sequence remains contiguous.
- E079 V2 runner blob: feb66711209043a5ae14a2a926501570b6915534.
- Per-target ledger: 849 rows, targets 401..1249, all training cutoffs equal t-1, independent re-execution metric/line-hit mismatches 0, geometry violations 0.
- The exact geometry-matched null was recomputed combinatorially and matches the registered constants to numerical tolerance.
- The preregistered bootstrap seed is 20261122080; the V2 runner uses seed bases 20261122100 / 20261122200 / 20261122300. This schedule is not stated in the preregistration. The CIs below are therefore diagnostic re-computations, not a conforming preregistered inference record.

## Candidate selection
| K | Mean winning numbers in TOP-K | candidate_recall@K | Uniform expected hits | Delta hits |
|---:|---:|---:|---:|---:|
| 10 | 1.299176 | 21.653% | 1.333333 | -0.034158 |
| 15 | 1.954064 | 32.568% | 2.000000 | -0.045936 |
| 20 | 2.584217 | 43.070% | 2.666667 | -0.082450 |
| 25 | 3.294464 | 54.908% | 3.333333 | -0.038869 |
| 30 | 3.962309 | 66.038% | 4.000000 | -0.037691 |
All five candidate-recall point estimates are below the uniform-random expectation. No candidate-stage promotion is supported.

## Three-line allocator comparison
The same E054 candidate scores and sequential top-16 pool rule were fixed. Arm A used the sorted-ticket E045 structural objective; arm B used score-only top-six selection. Both produced three disjoint six-number lines with union18 at every target.

| Metric | Exact null | A mean | A delta | B mean | B delta |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.514256 | 1.491166 | -0.023090 | 1.497055 | -0.017201 |
| any2 | 0.474976 | 0.472320 | -0.002656 | 0.452297 | -0.022679 |
| any3 | 0.071355 | 0.061249 | -0.010106 | 0.078916 | 0.007561 |
| any4 | 0.004180 | 0.000000 | -0.004180 | 0.001178 | -0.003003 |
| any5 | 0.000087 | 0.000000 | -0.000087 | 0.000000 | -0.000087 |
| any6 | 0.000000 | 0.000000 | -0.000000 | 0.000000 | -0.000000 |
| winning_union_coverage | 2.400000 | 2.361602 | -0.038398 | 2.335689 | -0.064311 |

A max-hit distribution (0..6): 36, 412, 349, 52, 0, 0, 0. B max-hit distribution (0..6): 30, 435, 317, 66, 1, 0, 0.
A all-line hit counts (0..6, 2,547 tickets): 1038, 1065, 392, 52, 0, 0, 0. B: 1052, 1075, 353, 66, 1, 0, 0.
A any2-positive blocks: 7/17 (41.18%). B: 4/17 (23.53%). The minimum is 65%; both fail.

## Matched random and paired comparison
Matched label-permutation simulation: 120 portfolios per target per arm, 101,880 per arm. A simulated random means: {"max_hits":1.5150667451904212,"any2":0.47555948174322693,"any3":0.07137809187279173,"any4":0.004093050647820956,"any5":0.00004907734589713388,"any6":0,"winning_union_coverage":2.3990282685512367}. B simulated random means: {"max_hits":1.511827640361211,"any2":0.47311542991755057,"any3":0.07054377699254048,"any4":0.004446407538280318,"any5":0.0001177856301531213,"any6":0,"winning_union_coverage":2.3959658421672567}. These are close to the exact null.

Paired B-minus-A deltas: {"max_hits":{"delta_mean":0.005889281507656066,"adjusted_ci":[-0.04946996466431095,0.05653710247349823]},"any2":{"delta_mean":-0.020023557126030624,"adjusted_ci":[-0.06595995288574794,0.020023557126030624]},"any3":{"delta_mean":0.0176678445229682,"adjusted_ci":[-0.004711425206124852,0.038869257950530034]},"winning_union_coverage":{"delta_mean":-0.02591283863368669,"adjusted_ci":[-0.07420494699646643,0.020023557126030624]}}. All four paired adjusted intervals include zero. A has higher any2 and union point estimates; B has a higher any3 point estimate. This is a trade-off, not a robust simultaneous gain.

## Strict gate
Both arms FAIL: every diagnostic adjusted CI lower bound is below zero; any2-positive block share is below 0.65; the prospective confirmation minimum and completion rule remain unspecified; and the bootstrap seed schedule does not match the preregistered seed declaration. No model is promoted. No candidates or purchase lines are generated.

## Next work
1. Correct and pre-register the bootstrap seed schedule before any further E079 inference; do not rewrite this run.
2. Continue only the separately registered candidate-recall axis or a new independent allocator hypothesis; do not tune to 1244-1249.
3. Obtain an explicit prospective confirmation minimum and completion rule before any STRICT_PASS_READY claim.
