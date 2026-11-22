# E030 prospective shadow review — target 1251

Evidence class: first resumed pre-draw-frozen shadow observation; one target only; not a confirmation horizon and not three-line portfolio evidence.

## What was frozen before the draw

- Target 1251, training cutoff 1250.
- Frozen at 2026-11-14 19:18:47 UTC (2026-11-15 04:18:47 KST), before the 2026-11-21 draw.
- Frozen artifact SHA-256: e809288c6f6a2d891fb48e88810369e03ff64cea48333b5fca383d6621b316c6.
- Canonical 1–1250 data SHA-256: 7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2.
- The 1247–1250 pre-draw gap remains; this is the first resumed observation, not a continuous prospective series.

## Candidate-stage results

| Frozen signal | Top-6 hits | Winner ranks | Recall@10 | @15 | @20 | @25 | @30 |
|---|---:|---|---:|---:|---:|---:|---:|
| CALENDAR_SEASON_CONDITIONAL_v1 | 3/6 | 1, 3, 5, 8, 20, 41 | 4/6 | 4/6 | 5/6 | 5/6 | 5/6 |
| PREVIOUS_SUM_REGIME_CONDITIONAL_v1 | 0/6 | 10, 13, 17, 19, 20, 43 | 1/6 | 2/6 | 5/6 | 5/6 | 5/6 |

Uniform-random expected candidate hits are 1.333, 2.000, 2.667, 3.333, and 4.000 for K=10/15/20/25/30 respectively. These are single-target descriptive comparisons only. No p-value, confidence interval, significance claim, or signal promotion is made.

The two frozen rankings had top-K overlap counts 0/6, 2/10, 7/15, and 23/30. This indicates substantial ranking disagreement at small K; it does not establish which signal is generally better.

## Separate 1251 delivered three-line review

The original E054/E045 artifact was not reconstructed. Recalculation from the preserved artifact gives line hits [1,1,0], max-hit 1, no any2+/any3+, and union coverage 2/6. The error note matches exactly. The candidate-stage top30 had 5/6 winners, while only 2 were in the delivered union; the recorded decomposition attributes 2 further winners to later sequential candidate pools not allocated and 2 outside three-stage pool reach. This is a one-draw diagnosis only, not a tuning rule. Purchase remains unconfirmed.

## Historical delivery provenance

- Target 1249: five-line intermediate candidate was visibly displayed; recalculation gives [2,1,0,0,1], max-hit 2, any2+, union coverage 4/6. It was not a final strict-pass artifact and purchase is unconfirmed.
- Target 1250: display evidence was corrected as unverified; exclude it from delivered-set performance.
- Targets 1247–1248: purchase is unconfirmed and multiple line sets exist; do not select one as the actual purchased set.

## Conclusion

This review adds one genuinely pre-draw-frozen shadow observation and verifies source integrity. It does not qualify the three-line policy, does not satisfy prospective confirmation, and does not change the STRICT_FAIL status. No candidate numbers, TOP30, core/tail list, or purchase lines are included.
