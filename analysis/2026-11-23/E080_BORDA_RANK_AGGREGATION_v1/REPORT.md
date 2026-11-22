# E080 — Borda rank aggregation candidate-recall study

**Classification:** historical cutoff-safe diagnostic only; not a clean holdout, not prospective confirmation, and not purchase readiness.

## Question and frozen design

One fixed candidate-model ablation was registered before evaluation. It uses the same five signals as the existing consensus model and changes only the aggregation rule: arithmetic mean of standardized scores versus equal-weight sum of component rank positions (Borda). The allocator is fixed at top-18 candidates split into three disjoint six-number lines.

- Source: `lotto_data.csv`, 1,250 contiguous rounds; cutoff 1250; SHA-256 `7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2`; Git blob `66431d711919f179e4cb1349e2f7295c68a8735e`.
- Runner: `automation/e080_borda_rank_aggregation_v3.js`; blob `313be168074e1f038822b9042f0b0b6653a015c5`; source SHA-256 `c5433bae84b8b5e5c8e08008d7af21eb708235387cc694fef752bbf3ff8bd3be`.
- Evaluation targets: 401–1250 (850); every target uses only rounds through t-1.
- Rounds 1244–1249 are contaminated live-history diagnostics; no clean-holdout or prospective claim is made.
- Candidate random control: 200 matched random K-subsets per target (170,000 total). Portfolio random control: 120 geometry-preserving bundles per target (102,000 total).
- Inference: 4,000 moving-block bootstrap replicates, 50-target blocks; candidate family alpha 0.05 / 10 comparisons, portfolio family alpha 0.05 / 4 strict metrics.

## Candidate-selection stage

| K | Borda recall@K | Exact random | Borda delta | Adjusted CI vs random | Consensus recall@K | Borda minus consensus |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 22.510% | 22.222% | 0.288 pp | [-1.340, 1.602] pp | 21.941% | 0.569 pp |
| 15 | 32.804% | 33.333% | -0.529 pp | [-2.118, 1.118] pp | 33.451% | -0.647 pp |
| 20 | 44.059% | 44.444% | -0.386 pp | [-2.092, 1.379] pp | 44.314% | -0.255 pp |
| 25 | 55.255% | 55.556% | -0.301 pp | [-1.752, 1.190] pp | 55.294% | -0.039 pp |
| 30 | 65.961% | 66.667% | -0.706 pp | [-2.098, 0.549] pp | 66.647% | -0.686 pp |

All five Borda adjusted intervals include zero. The point estimate is slightly above random only at K=10; K=15/20/25/30 are below the exact expectation. None supports candidate-stage promotion. Borda-minus-consensus differences are descriptive only and were not separately tested.

## Three-line portfolio stage

| Metric | Exact geometry null | Borda observed | Delta | Adjusted moving-block CI | Consensus observed | Matched-random mean |
|---|---:|---:|---:|---:|---:|---:|
| max_hits | 1.514256 | 1.495294 | -0.018962 | [-0.069558, 0.036332] | 1.512941 | 1.511775 |
| any2 | 0.474976 | 0.461176 | -0.013800 | [-0.052623, 0.026200] | 0.467059 | 0.474500 |
| any3 | 0.071355 | 0.065882 | -0.005473 | [-0.026649, 0.016888] | 0.088235 | 0.070029 |
| winning_union_coverage | 2.400000 | 2.397647 | -0.002353 | [-0.100007, 0.096471] | 2.395294 | 2.395127 |

- Borda any2-positive non-overlapping 50-target blocks: 8/17 (47.06%); unchanged minimum 65%.
- Borda max-hit distribution (0–6): 32, 426, 336, 52, 3, 1, 0.
- Borda all-line hit distribution (0–6; 2550 lines): 1009, 1105, 380, 52, 3, 1, 0.
- Borda winning-union coverage distribution (0–6): 32, 155, 278, 240, 120, 23, 2.

All four strict portfolio CI lower bounds and the any2 block-share condition must pass simultaneously. The strict historical gate is **FAIL**. Prospective confirmation remains false and its minimum count/completion rule remains unspecified, so `STRICT_PASS_READY` is false regardless.

## Candidate miss trace

The internal trace stores 5100 winning-number instances with Borda rank, consensus rank, and all five component ranks. Borda rank bands (counts of winner instances): 1-10: 1148; 11-15: 525; 16-20: 574; 21-25: 571; 26-30: 546; 31-45: 1736. The trace is retained internally; no candidate list or top-30 is released.

## Decision

- Candidate model promotion: **NO**.
- Allocator promotion: **NO**; the allocator was held fixed.
- Strict purchase readiness: **NO**.
- No purchase lines, candidate numbers, top-30, or fallback numbers were generated for user display.
- This is historical evidence only. The next independent confirmation can begin only prospectively after a pre-draw policy freeze; historical results cannot substitute for it.
