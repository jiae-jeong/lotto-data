# Daily Lotto Research — 2026-11-26

# E084 — Derived-signal redundancy ablation (3-line policy)

**Date:** 2026-11-26 KST  
**Research question:** Do the derived `balanced` and `contrarian` components add independent candidate information to the five-component mean-z consensus, or do they duplicate the base signals and overweight gap?

## What was executed

- One challenger was preregistered before evaluation; no parameter or allocator search.
- Source cutoff 1251; targets 401–1251 inclusive (851 targets); each target used only draws through t−1.
- Candidate stage: recall@10/15/20/25/30; 200 target-matched random candidate permutations per target.
- Portfolio stage: same fixed rank-partition allocator for both models (top 18 split into three disjoint six-number lines); 120 matched random portfolios per target.
- Exact geometry-matched null recomputed by combinatorial enumeration; probability mass 1.000000000000001.
- Moving-block bootstrap: 4,000 replicates, 50-target blocks; 17 complete blocks plus the final 1-target remainder retained.
- Rounds 1244–1251 are contaminated live-history diagnostics, not untouched holdout.

## Algebraic finding

The five-component score simplifies exactly:

`(recent30 + gap + momentum + balanced + contrarian)/5`  
`= (recent30 + 2×gap + momentum)/5`

The two derived components do not add a new feature dimension. Together they add one extra gap vote. The challenger removes that duplicate representation and gives recent30, gap and momentum equal weight. This is a fixed ablation, not a learned or tuned weight.

## Candidate-selection results

| K | Full five recall | Base-three recall | Matched random | Exact uniform |
|---:|---:|---:|---:|---:|
| 10 | 21.935% | 22.425% | 22.256% | 22.222% |
| 15 | 33.451% | 32.805% | 33.351% | 33.333% |
| 20 | 44.320% | 44.046% | 44.390% | 44.444% |
| 25 | 55.288% | 55.621% | 55.515% | 55.556% |
| 30 | 66.647% | 66.804% | 66.570% | 66.667% |

Primary paired ΔRecall@30 (base-three − full five): **0.157 percentage points**, 95% moving-block CI [-0.979, 1.175] pp.

Base-three Recall@30 versus exact uniform: **+0.137 pp**; 95% moving-block CI [-1.293, 1.351] pp.

## Three-line portfolio results

| Metric | Full five | Base-three | Exact null | Base-three Δ | Adjusted CI lower |
|---|---:|---:|---:|---:|---:|
| max_hit | 1.512338 | 1.493537 | 1.514256 | -0.020719 | -0.092400 |
| any2 | 0.466510 | 0.475911 | 0.474976 | +0.000934 | -0.044894 |
| any3 | 0.088132 | 0.058754 | 0.071355 | -0.012601 | -0.038452 |
| winning_union_coverage | 2.394830 | 2.363102 | 2.400000 | -0.036898 | -0.146181 |

Any2-positive full-block share: **9/17 (52.94%)**, required ≥65%. Final remainder: 1 target, reported separately.

Matched-random portfolio means: max_hit=1.518096; any2=0.475999; any3=0.073042; any4=0.004358; any5=0.000098; any6=0.000000; winning_union_coverage=2.403653.

## Interpretation

- Candidate-stage ablation is evaluated separately from the fixed allocator.
- The portfolio stage uses the same three-line geometry for both rankers and the correct exact null.
- Historical strict gate: **FAIL**.
- No model or allocator promotion. Historical data cannot satisfy prospective confirmation.
- No candidate numbers, TOP30, core/tail lists or purchase lines were written to user-facing output. No delivery event was appended.

## Data and provenance

- Data SHA-256: `2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9`
- Data Git blob SHA: `be2fa07921a92f335aeb6e715b4f40098e297834`
- Runner Git blob SHA: `b7049773330c72a7909a45b56e9d2c288ac47257`
- Preregistration Git blob SHA: `4b2a3e566754f76407cf4dd5877cc8d5f7e2b7c0`
- 1251 original delivery artifact was checked against DELIVERY_LOG; per-line hits 1/1/0, max-hit 1, union coverage 2/6. Purchase remains unconfirmed.
- Direct official API retrieval remains unavailable; 1251 result was cross-checked against operator-attributed reporting and independent result sources.

## Next tests

1. Do not create another variant from this same historical target range.
2. Preserve the fixed three-line gate and the unspecified prospective minimum-count rule; do not invent a threshold.
3. Move to independent external/nested validation or a genuinely new, preregistered research gap.


## Historical delivery and error-note reconciliation

- Original target-1251 artifact and DELIVERY_LOG event were re-fetched; artifact blob SHA `9da6f5760367758896f20f8643c771452e7948cd`, ledger blob SHA `24f66f12e71f7976db9d25d5bee32c12a02218b6`.
- The preserved 1251 lines score [1, 1, 0] against the recorded draw; max-hit 1, any2+ false, union coverage 2/6. Artifact lines match the ledger: true. No source lines were reconstructed or rewritten.
- Purchase-confirmation registry contains 0 confirmed purchases; no purchase is inferred from display.
- 1249 is a displayed intermediate candidate with no purchase confirmation; 1250 display evidence was corrected to unverified; 1247/1248 have conflicting preserved line sets and no purchase receipts. No aggregate actual-purchase score was updated.

## 1252 readiness

STRICT FAIL / NOT READY. No candidate list, TOP30, core/tail, or purchase lines were generated or displayed. No freeze/seal and no DELIVERY_LOG event were created. The prospective minimum target count and completion rule remain unspecified in policy and were not invented.
