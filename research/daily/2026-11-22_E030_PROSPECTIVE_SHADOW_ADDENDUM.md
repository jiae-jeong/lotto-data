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

## Daily run integrity and execution notes

- Latest main at run start: cbe9c3c10f536c3e39a1eefee43b7d4271a8ba5d.
- LOTTO_PROJECT_PROTOCOL.md and AGENTS.md were read before research; the 1250 remediation plan and current 1251 strict policy were read.
- The 1251 snapshot SHA-256 was independently recomputed as 2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9; it matches the append-only correction artifact. Canonical 1250-row source hash also matched.
- E079 remains historical STRICT_FAIL. Its runner bootstrap seed bases are not specified by its preregistration; no post-hoc seed schedule was invented and its intervals remain diagnostic only.
- E079 candidate recall@10/15/20/25/30 was 21.65%, 32.57%, 43.07%, 54.91%, 66.04%, each below its uniform expectation. Structural E079-A deltas were negative for max-hit (-0.02309), any2 (-0.00266), any3 (-0.01011), and union coverage (-0.03840); score-only E079-B had any3 +0.00756 but max-hit/any2/union deltas -0.01720/-0.02268/-0.06431. Any2-positive 50-target block shares were 7/17 and 4/17, both below 0.65. No promotion.
- Target-1251 delivered E054/E045 three-line artifact was independently recomputed and exactly matched the preserved error note. Target-1249 visible intermediate set was also recomputed; 1250 and 1247–1248 remain excluded from actual-purchase aggregates due missing display/purchase confirmation.
- No candidate numbers were displayed; DELIVERY_LOG was not changed because no number-delivery event occurred.

## Next work

1. Keep the E079 bootstrap seed-schedule conformance issue unresolved; do not retrofit a seed schedule after observing the historical results.
2. Continue the prospective shadow ledger only from genuinely pre-draw frozen artifacts, preserving all missing-target gaps and without counting a single target as confirmation.
3. Select and preregister a genuinely independent candidate-stage hypothesis only after reviewing the latest failure registry; do not recycle E043/E044 five-line work or relax the three-line strict gate.
