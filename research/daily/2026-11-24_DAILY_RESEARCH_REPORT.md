# Daily Lotto Research Report — 2026-11-24

## NEW STUDY — E082 rank-dependence and candidate-set overlap

**Question:** Do the existing mean-z consensus, E080 Borda, and E081 MIN_RANK aggregators create meaningfully distinct candidate rankings, or mostly reshuffle the same information?

This is a candidate-stage diagnostic only. No feature, weight, cutoff, allocator, threshold, or model was changed. The study was preregistered before evaluation; the first preregistration contained a truncated Git blob SHA, and an append-only correction was committed before any evaluation. The original file remains unchanged.

### Execution and source integrity

- Source: `data/snapshots/lotto_data_through_1251_20261122.csv`
- Cutoff: 1251; 1,251 contiguous rows, rounds 1–1,251.
- SHA-256: `2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9`
- Git blob SHA-1: `be2fa07921a92f335aeb6e715b4f40098e297834`
- Header, sequence, six unique main numbers in 1–45, and bonus validity: PASS.
- Hash implementation self-tests: SHA-256 `abc` vector PASS; Git blob SHA-1 `blob 3\\0abc` vector PASS.
- Targets 401–1251 inclusive: 851. Every target used only rounds through t−1; cutoff violations: 0.
- Computed 2,553 full model rankings and 2,553 pairwise rank-correlation observations, top-K overlaps for K=10/15/20/25/30, and winner-rescue counts.
- Stability partition: 17 non-overlapping 50-target blocks plus the final one-target remainder, retained separately.
- Rounds 1244–1251 are contaminated live-history diagnostics, not a clean holdout or prospective confirmation.

### Rank dependence

| Model pair | Mean Spearman rank correlation | Mean top-30 intersection | Top-30 Jaccard |
|---|---:|---:|---:|
| Consensus vs Borda | 0.8660 | 27.28 / 30 | 0.8363 |
| Consensus vs MIN_RANK | 0.7220 | 24.57 / 30 | 0.6962 |
| Borda vs MIN_RANK | 0.5870 | 24.02 / 30 | 0.6698 |

For reference, two independent uniform top-30 sets have expected intersection 20.0. The observed sets are therefore substantially overlapping; Borda is especially close to consensus. MIN_RANK is more distinct, particularly from Borda, but still shares about 24 of 30 candidates on average. This measures rank dependence, not predictive value.

### Candidate recall versus exact uniform expectation

All figures below are descriptive point differences in percentage points; no confidence interval or significance claim was calculated in E082.

| Ranker | @10 | @15 | @20 | @25 | @30 |
|---|---:|---:|---:|---:|---:|
| Consensus | −0.287 | +0.118 | −0.124 | −0.268 | −0.020 |
| Borda | +0.261 | −0.529 | −0.379 | −0.307 | −0.705 |
| MIN_RANK | +1.045 | +0.392 | −0.535 | +0.261 | +0.274 |

MIN_RANK's positive point deltas at four of five K values do not establish a repeatable edge: its K=20 delta is negative, and the prior E081 Bonferroni-adjusted candidate intervals all included zero. Borda is below the exact uniform expectation at K=15/20/25/30. Consensus is close to the exact expectation throughout.

At K=30, MIN_RANK captured 728 winner instances that Borda did not, while Borda captured 678 that MIN_RANK did not, across the 851 historical targets. This is a descriptive rescue count, not an independent test. In the 17 full blocks, MIN_RANK had more unique winner captures than Borda in 11 blocks; Borda led in 5; one block was tied. This direction is not sufficient for promotion and does not replace candidate-recall uncertainty control.

### Interpretation and decision

1. **Borda is largely redundant with consensus.** Their mean full-rank Spearman correlation is 0.866 and their top-30 intersection averages 27.28.
2. **MIN_RANK changes the ordering more materially.** Its correlations are lower (0.722 vs consensus; 0.587 vs Borda), but the top-30 still overlaps by about 24–25 numbers on average.
3. **Distinct rankings are not the same as useful rankings.** Candidate-recall point differences are small and mixed; existing E081 adjusted intervals include zero. E082 is descriptive only and has no inferential promotion test.
4. **No allocator conclusion follows.** E082 held candidate ranking comparisons separate from the three-line allocator. It did not calculate a new portfolio policy or strict-gate result.
5. No model or allocator is promoted; strict thresholds are unchanged.

## MAINTENANCE / RECHECK — actual delivered recommendation and post-draw note

The original target-1251 artifact was fetched and matched to its existing error note; no line was reconstructed or rewritten. The pre-draw artifact is `research/weekly_purchase/1251/RESEARCH_SELECTED_LINES_1251_20261120.json` (Git blob `9da6f5760367758896f20f8643c771452e7948cd`), using E054 with the unchanged E045 allocator, cutoff 1250, and the canonical 1,250-row source SHA `7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2`.

- Officially reported 1251 result: 14, 18, 19, 29, 40, 45; bonus 1.
- Recomputed from the preserved artifact: line-hit distribution 1/1/0; max-hit 1; any2+ false; any3+ false; union coverage 2/6; bonus match false.
- The delivery was research-selected, not strict-pass. Purchase confirmation remains NOT_CONFIRMED.
- `research/PURCHASE_CONFIRMATION_REGISTRY.json` still contains zero confirmed purchases.
- Target 1249 has a recorded intermediate five-line display, but no purchase confirmation. Target 1250's user-visible delivery evidence was corrected to unverified. Targets 1247/1248 retain conflicting preserved line sets and no purchase proof; they are excluded from confirmed-purchase learning.

The 1251 result is corroborated by the operator-attributed Yonhap report and independent result listings; direct Donghaeng API retrieval was not obtained. Source links: [Yonhap, 2026-11-21](https://www.yna.co.kr/view/AKR20261121050800002), [Newsis via FN News](https://www.fnnews.com/news/202611212058363456), [LottoLottery result listing](https://www.lottolottery.co.kr/results/1251).

## Current target-1252 readiness

- Latest data integrity: PASS after the 2026-11-23 SHA correction. The initial mismatch was caused by an audit helper omitting SHA-256 constant `0xefbe4786`; the snapshot itself was not changed.
- Latest strict status remains FAIL / NOT READY. E081's adjusted CI lower bounds were max-hit −0.093575, any2 −0.061345, any3 −0.026702, and winning-union coverage −0.132080. Any2-positive 50-target blocks were 8/17 (47.06%), below the unchanged 65% threshold.
- Prospective confirmation remains unevaluated because its minimum target count and completion rule are unspecified. Do not import the separate prospective_v4 200-target rule.
- The H1250-A/B external nested workflow execution was not found; its five-line research design cannot qualify the three-line policy.
- No qualified champion, no strict PASS, no target-1252 purchase lines, no random fallback, and no freeze/seal.

## Next work

1. Keep E080/E081 and E082 immutable; do not tune the same historical targets or create more aggregation variants from the observed deltas.
2. Resolve the prospective minimum-count and completion-rule gap through a versioned policy decision; do not invent the value or borrow a different protocol's endpoint.
3. Only after that, preregister one independent three-line axis and run the required external nested/rolling evaluation against the target-specific exact geometry null and matched random baseline. Keep candidate recall and allocator performance separate.

**Classification:** E082 is a completed new historical rank-dependence diagnostic, not a clean holdout, not prospective confirmation, and not purchase readiness. No candidate numbers, TOP30, core/tail lists, or purchase lines are included in this report.
