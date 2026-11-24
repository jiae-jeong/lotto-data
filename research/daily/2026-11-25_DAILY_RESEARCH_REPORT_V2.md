# Daily Lotto Research — 2026-11-25 (corrected final record)

This version supersedes the candidate-stage summary in `2026-11-25_DAILY_RESEARCH_REPORT.md`. The earlier file and all earlier E083 outputs remain preserved; the corrected run adds the omitted static recall@10/15/20/25 columns without changing the preregistered selector, allocator, source, target range, seeds, or inference design.

## New study: E083 prequential dynamic ranker selection

One dynamic selector was frozen before evaluation. At each target it selected among the existing CONSENSUS, BORDA, and MIN_RANK rankers using only each ranker's candidate_recall@30 over the preceding 50 target rounds. The target outcome was excluded from its own selection. The selected ranking's top 18 were passed to one unchanged allocator: three consecutive disjoint six-number lines.

- Warm-up: 401–450; rolling-origin targets: 451–1251 (801).
- Candidate stage: recall@10/15/20/25/30; primary metric recall@30.
- Portfolio stage: max-hit, any2/3/4/5/6, winning-union coverage, and line-hit distributions.
- Matched random: 200 candidate sets and 120 geometry-preserving three-line portfolios per target.
- Moving-block bootstrap: 4,000 replicates, block length 50, final one-target remainder retained; Bonferroni alpha 0.0125.
- Source integrity: 1,251 contiguous rows; recomputed SHA-256 and Git blob SHA-1 matched. Cutoff violations 0; invalid three-line geometries 0.
- Rounds 1244–1251 remain contaminated live-history diagnostics, not clean holdout or prospective evidence.

## Candidate-selection results

| Ranker | Recall@10 | Recall@15 | Recall@20 | Recall@25 | Recall@30 |
|---|---:|---:|---:|---:|---:|
| CONSENSUS | 21.827% | 33.417% | 44.299% | 55.431% | 66.750% |
| BORDA | 22.347% | 32.813% | 44.132% | 55.347% | 65.980% |
| MIN_RANK | 23.075% | 33.521% | 43.654% | 55.493% | 66.750% |
| DYNAMIC | 22.493% | 33.000% | 43.675% | 55.035% | 66.271% |

Dynamic recall@30 versus exact uniform: −0.395 percentage points; Bonferroni-adjusted moving-block CI [−1.873, +1.020] pp. Versus CONSENSUS: −0.479 pp [−1.332, +0.458]; versus BORDA: +0.291 pp [−0.916, +1.581]; versus MIN_RANK: −0.479 pp [−1.540, +0.708]. All intervals include zero, so no reliable candidate-recall gain was demonstrated.

Selector counts: CONSENSUS 363, BORDA 149, MIN_RANK 289; 71 switches. Top-30 misses: 1,621/4,806 winning instances (33.73%). Best-component rank attribution among misses: recent30 568, momentum 495, contrarian 420, gap 117, balanced 21. This attribution is not causal proof.

## Three-line portfolio results

| Metric | Observed | Exact geometry null | Delta | Bonferroni-adjusted CI |
|---|---:|---:|---:|---:|
| max-hit | 1.489388 | 1.514256 | −0.024868 | [−0.089795, +0.045045] |
| any2+ | 0.455680 | 0.474976 | −0.019296 | [−0.066737, +0.025656] |
| any3+ | 0.074906 | 0.071355 | +0.003551 | [−0.015175, +0.026023] |
| winning union coverage | 2.367041 | 2.400000 | −0.032959 | [−0.136579, +0.059426] |

Matched-random means: max-hit 1.510456, any2+ 0.473231, any3+ 0.069268, union coverage 2.396660. The dynamic portfolio was below matched random on max-hit, any2+, and union coverage; the small positive any3+ point difference has a CI spanning zero. Any4+/5+/6 were not improved. Any2-positive 50-target blocks: 6/16 (37.50%), below the unchanged 65% requirement. The final one-target remainder was retained separately.

## Gate and decision

Historical four-metric gate: **FAIL**. All four adjusted CI lower bounds were non-positive; any2-positive block share was 37.50% versus the required 65%. Prospective confirmation is absent and its minimum count/completion rule remains unspecified. This was not an external nested execution. No model/allocator promotion, no strict PASS, no freeze/seal, no random fallback, and no candidate/TOP30/core-tail/purchase lines were generated.

## Implementation audit

- E083 v1 miss-attribution draft was rejected before evaluation because it mapped aggregate ranks into component-rank fields; it was not executed.
- E083 v2 produced the portfolio and recall@30 calculations but omitted static recall@10/15/20/25 output columns, which serialized as null.
- E083 v3 corrected the output schema and reran the preregistered calculation. No selector, allocator, source, target-range, seed, threshold, or inference rule changed. Earlier v1/v2 artifacts remain preserved; the v3 output folder is canonical.

## Historical delivery and error-note review

The original target-1251 pre-draw artifact and error note were re-read unchanged. The error note records line-hit distribution 1/1/0, max-hit 1, no any2+/any3+, and union coverage 2/6; purchase confirmation remains NOT_CONFIRMED. Target 1249 remains an intermediate display without purchase confirmation. Target 1250's user-visible delivery assertion remains unverified. Targets 1247/1248 retain conflicting saved sets without purchase proof. No set was reconstructed or promoted into the confirmed-purchase aggregate.

The 1251 result is cross-checked against Yonhap and independent result listings; the direct official API endpoint was not retrieved, so that provenance limitation remains.

## Next actions

1. Resolve the prospective minimum-target and completion-rule policy gap through a separately versioned decision; do not silently borrow the unrelated 200-target protocol.
2. Only after policy resolution, run a genuinely independent nested/rolling validation before any prospective claim.
3. Keep the 1252 three-line strict gate unchanged. No freeze or number release while strict status is FAIL.
