# Daily Lotto Research Report — 2026-11-23

## NEW STUDY — E080 Borda rank aggregation

Registered one fixed rank-aggregation ablation before evaluation. The five existing cutoff-safe candidate signals were unchanged; only the aggregation changed from mean standardized scores to equal-weight sum of component rank positions. The allocator remained fixed at top-18 split into three disjoint six-number lines.

- Canonical source: 1,250 contiguous rows through cutoff 1250; SHA-256 7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2; Git blob 66431d711919f179e4cb1349e2f7295c68a8735e.
- Code: automation/e080_borda_rank_aggregation_v3.js; blob 313be168074e1f038822b9042f0b0b6653a015c5; SHA-256 c5433bae84b8b5e5c8e08008d7af21eb708235387cc694fef752bbf3ff8bd3be.
- Targets 401–1250 (850), cutoff t-1; rounds 1244–1249 remain contaminated live-history diagnostics.
- Candidate stage: recall@10/15/20/25/30, 200 matched random candidate sets per target, 10 Bonferroni-controlled candidate comparisons.
- Portfolio stage: max-hit, any2/any3/any4/any5/any6, union coverage and line-hit distributions; 120 geometry-matched random portfolios per target; 4,000 moving-block bootstrap replicates; 50-target blocks.

### Candidate stage results

| K | Borda recall | Exact random | Delta | Adjusted CI |
|---:|---:|---:|---:|---:|
| 10 | 22.510% | 22.222% | 0.288 pp | [-1.340, 1.602] pp |
| 15 | 32.804% | 33.333% | -0.529 pp | [-2.118, 1.118] pp |
| 20 | 44.059% | 44.444% | -0.386 pp | [-2.092, 1.379] pp |
| 25 | 55.255% | 55.556% | -0.301 pp | [-1.752, 1.190] pp |
| 30 | 65.961% | 66.667% | -0.706 pp | [-2.098, 0.549] pp |

All five adjusted intervals include zero; candidate stage is not promoted.

### Portfolio stage results

| Metric | Borda delta vs exact null | Adjusted CI |
|---|---:|---:|
| max_hits | -0.018962 | [-0.069558, 0.036332] |
| any2 | -0.013800 | [-0.052623, 0.026200] |
| any3 | -0.005473 | [-0.026649, 0.016888] |
| winning_union_coverage | -0.002353 | [-0.100007, 0.096471] |

Any2-positive blocks: 8/17 (47.06%), below the 65% threshold. Historical strict gate: **FAIL**. Prospective confirmation is not met or defined; strict readiness remains false.

## MAINTENANCE / RECHECK — prior delivered recommendation

Re-read the preserved target-1251 pre-draw delivery artifact and append-only post-draw error note. The original three-line artifact matches its stored source exactly; no line reconstruction occurred. Recorded outcome remains line-hit distribution 1/1/0, max-hit 1, any2+/any3+ false, union coverage 2/6. Candidate-stage trace attributes two winners to the selected union, two to later sequential pools not allocated, and two outside the three-stage pool reach. This is one-target diagnosis only; purchase remains unconfirmed.

## Decision and next work

- E080 candidate ranking and fixed allocator are not promoted.
- No strict PASS, prospective confirmation, purchase lines, or fallback numbers.
- Next tests: (1) verify whether the Borda miss-rank trace adds any stable, pre-target information beyond the existing consensus ranks; (2) continue only a separately preregistered candidate-stage hypothesis; (3) keep prospective policy minimum/completion rule unresolved until explicitly defined by the policy owner.
