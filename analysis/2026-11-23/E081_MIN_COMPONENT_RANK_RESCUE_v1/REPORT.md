# E081 — Minimum-component-rank rescue diagnostic (2026-11-23)

**Classification:** historical cutoff-safe exploratory diagnostic only; not a clean holdout, not prospective confirmation, and not purchase readiness.

## Frozen question and execution

A single minimum-component-rank aggregation was registered before evaluation. For each number, rank by the best (lowest) position among five existing signals; ties are broken by the sum of the five component ranks, then by number. The allocator is fixed at three disjoint six-number lines formed from ranks 1–6, 7–12 and 13–18. No parameter or allocator search was performed.

- Data: 1,251 contiguous rounds through cutoff 1251; corrected SHA-256 `2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9`; Git blob `be2fa07921a92f335aeb6e715b4f40098e297834`.
- Runner: `automation/e081_min_component_rank_rescue_v2.js`; blob `568269e7d89cc9dc08bef6f128d2fd3b91d9be0a`.
- Targets: 401–1251 inclusive (851); every target uses only rounds through t-1.
- Rounds 1244–1251 are contaminated live-history material, not clean holdout or prospective evidence.
- Candidate random: 200 target-matched subsets per target (170200 total); portfolio random: 120 geometry-preserving bundles per target (102120 total).
- Bootstrap: 4,000 moving-block replicates, 50-target blocks; 17 full blocks plus the final 1-target remainder retained.

## Candidate-selection stage

| K | Min-rank recall | Exact random | Delta | Bonferroni-adjusted CI |
|---:|---:|---:|---:|---:|
| 10 | 23.267% | 22.222% | 1.045 pp | [-0.718, 2.102] pp |
| 15 | 33.725% | 33.333% | 0.392 pp | [-1.802, 1.704] pp |
| 20 | 43.909% | 44.444% | -0.535 pp | [-3.042, 0.992] pp |
| 25 | 55.817% | 55.556% | 0.261 pp | [-1.795, 1.260] pp |
| 30 | 66.941% | 66.667% | 0.274 pp | [-1.312, 1.312] pp |

Top-30 miss trace: 1688 of 5106 winner instances (33.06%) were outside the selected candidate set. Among those misses, the best-ranked component attribution counts were: recent30 595, gap 218, momentum 394, balanced 47, contrarian 434. These are rank-position diagnostics, not a basis for post-result signal weighting.

## Three-line portfolio stage

| Metric | Observed | Exact geometry null | Delta | Adjusted CI |
|---|---:|---:|---:|---:|
| max_hits | 1.502938 | 1.514256 | -0.011319 | [-0.093575, 0.042743] |
| any2 | 0.468860 | 0.474976 | -0.006116 | [-0.061345, 0.027961] |
| any3 | 0.070505 | 0.071355 | -0.000850 | [-0.026702, 0.019134] |
| winning_union_coverage | 2.397180 | 2.400000 | -0.002820 | [-0.132080, 0.077086] |

- Any2-positive full 50-target blocks: 8/17 (47.06%); minimum 65%.
- Final remainder: 1 target, retained in bootstrap and separately reported.
- Hit distributions (0–6): max-hit 32, 420, 339, 59, 1, 0, 0; all-line 1011, 1105, 377, 59, 1, 0, 0; union coverage 32, 141, 300, 233, 126, 18, 1.
- Exact-null probability sum: 1.000000000000; registered exact-null values independently reproduced.

## Stable baseline comparison

On the same targets, candidate recall at K=30 was MIN_RANK 66.941%, Borda 65.962%, consensus 66.647%, against exact random 66.667%. At K=10 the corresponding recalls were 23.267%, 22.483%, 21.935%. Baseline comparisons are descriptive; only MIN_RANK versus exact random received the preregistered candidate CIs.

Portfolio any3+ point rates were MIN_RANK 7.051%, Borda 6.580%, consensus 8.813%, exact geometry null 7.135%. These comparator point estimates are descriptive only; they do not qualify a strict gate.

## Decision

- Historical strict portfolio gate: STRICT_FAIL.
- All four adjusted CI lower bounds positive: false. Any2 positive block share: 47.06% versus 65% minimum.
- Prospective confirmation: NOT MET; the policy minimum target count and completion rule remain unspecified.
- Candidate model promotion: NO. Allocator promotion: NO. Strict pass ready: NO.
- No candidate list, TOP30, core/tail, or purchase lines were generated for user display. No random fallback or purchase confirmation.
