# E078 — Empirical multivariate block-resampling power stress test

**Classification: DESIGN-ONLY / HISTORICAL-INPUT STRESS TEST. Not model evidence, not a strict PASS, and not prospective confirmation.**

## Question and frozen design
Does preserving the empirical joint distribution of the four strict-gate endpoint block means change the prospective confirmation power picture relative to E046's normal-theory independence approximation?

- Source cutoff: 1249; targets 401–1249 (849), already inspected/live-history material.
- Four endpoints: max-hit, any2, any3, winning-union coverage, each differenced from the exact disjoint-union18 null.
- 16 complete 50-target source blocks plus the final 49-target remainder; the remainder is retained.
- Empirical multivariate block vectors are resampled jointly, preserving observed cross-endpoint dependence. The final prospective remainder is sampled from all contiguous source windows of the same length.
- Hypothetical effect sizes: 0.25/0.50/0.75/1.00 historical block SD per endpoint. No model or gate is changed.
- 10000 Monte Carlo trajectories per grid cell; family alpha 0.05, per-endpoint alpha 0.0125, critical z 2.4977054744123737.

## Source and integrity
- Canonical current data: 1–1250, SHA256 7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2, Git blob 66431d711919f179e4cb1349e2f7295c68a8735e. Round 1251 is not present.
- E045 prediction source: SHA256 63741597dced378876c7ac1d7a15fb5864e03f3a2b765a42e9452591867d3500, Git blob e55b8f5997dde36ff55b93b4bb53d20b8ad2ba69. 849/849 targets; cutoff violations 0; all three-line union18 geometries and stored hits recomputed.
- E045 exact comparator source: SHA256 19566decad6fac44651341046d10a6241ba40abc7575771736fd53ef8d035a25, Git blob fa0fe8e2317f22b01dbd3b3aa15f4df68d8680c3. 849/849 targets; geometry violations 0.
- Historical block SDs reproduce E046 exactly: 0.105617200, 0.061432171, 0.042608134, 0.168539557.
- 1244–1249 are contaminated live-history diagnostics, not clean holdout or prospective evidence.

## Joint gate probability (empirical block resampling)

| Targets | d | Full blocks + remainder | Joint gate probability | Wilson 95% interval | E046 independence approx. |
|---:|---:|---:|---:|---:|---:|
| 100 | 0.25 | 2 | 0.00% | 0.00–0.04% | 0.00% |
| 100 | 0.50 | 2 | 0.00% | 0.00–0.04% | 0.00% |
| 100 | 0.75 | 2 | 0.32% | 0.23–0.45% | 0.00% |
| 100 | 1.00 | 2 | 0.45% | 0.34–0.60% | 0.03% |
| 200 | 0.25 | 4 | 0.00% | 0.00–0.04% | 0.00% |
| 200 | 0.50 | 4 | 0.09% | 0.05–0.17% | 0.00% |
| 200 | 0.75 | 4 | 0.46% | 0.35–0.61% | 0.05% |
| 200 | 1.00 | 4 | 2.32% | 2.04–2.63% | 0.80% |
| 300 | 0.25 | 6 | 0.00% | 0.00–0.04% | 0.00% |
| 300 | 0.50 | 6 | 0.05% | 0.02–0.12% | 0.01% |
| 300 | 0.75 | 6 | 0.96% | 0.79–1.17% | 0.36% |
| 300 | 1.00 | 6 | 5.09% | 4.68–5.54% | 5.05% |
| 400 | 0.25 | 8 | 0.00% | 0.00–0.04% | 0.00% |
| 400 | 0.50 | 8 | 0.08% | 0.04–0.16% | 0.02% |
| 400 | 0.75 | 8 | 1.25% | 1.05–1.49% | 1.15% |
| 400 | 1.00 | 8 | 8.33% | 7.80–8.89% | 13.82% |
| 500 | 0.25 | 10 | 0.01% | 0.00–0.06% | 0.00% |
| 500 | 0.50 | 10 | 0.10% | 0.05–0.18% | 0.07% |
| 500 | 0.75 | 10 | 1.71% | 1.47–1.98% | 3.39% |
| 500 | 1.00 | 10 | 11.07% | 10.47–11.70% | 29.25% |
| 600 | 0.25 | 12 | 0.00% | 0.00–0.04% | 0.00% |
| 600 | 0.50 | 12 | 0.11% | 0.06–0.20% | 0.17% |
| 600 | 0.75 | 12 | 2.10% | 1.84–2.40% | 7.54% |
| 600 | 1.00 | 12 | 19.99% | 19.22–20.79% | 46.72% |
| 800 | 0.25 | 16 | 0.01% | 0.00–0.06% | 0.00% |
| 800 | 0.50 | 16 | 0.03% | 0.01–0.09% | 0.58% |
| 800 | 0.75 | 16 | 4.58% | 4.19–5.01% | 19.91% |
| 800 | 1.00 | 16 | 32.03% | 31.12–32.95% | 73.63% |
| 849 | 0.25 | 16 + 49 | 0.00% | 0.00–0.04% | — |
| 849 | 0.50 | 16 + 49 | 0.15% | 0.09–0.25% | — |
| 849 | 0.75 | 16 + 49 | 4.58% | 4.19–5.01% | — |
| 849 | 1.00 | 16 + 49 | 35.56% | 34.63–36.50% | — |
| 1000 | 0.25 | 20 | 0.00% | 0.00–0.04% | 0.00% |
| 1000 | 0.50 | 20 | 0.18% | 0.11–0.28% | 1.85% |
| 1000 | 0.75 | 20 | 5.72% | 5.28–6.19% | 39.19% |
| 1000 | 1.00 | 20 | 46.42% | 45.44–47.40% | 89.92% |

## Interpretation
This is a planning stress test only. The source contains just 16 complete non-overlapping 50-target blocks plus one 49-target remainder, so empirical block resampling has limited support and cannot establish future power or model edge. The E046 independence approximation is not treated as ground truth; the empirical joint estimate retains endpoint correlation but remains conditional on historical block behavior. Neither method replaces the operational moving-block bootstrap on future, pre-registered prospective outcomes.

The prospective minimum target count and completion rule remain unspecified. This study does not choose or adopt either, does not relax the strict gate, and cannot create STRICT_PASS_READY or purchase lines.

## Recommendation delivery audit
- Target 1249: the DELIVERY_LOG records an intermediate candidate display, strict FAIL, and no purchase confirmation. Its post-draw line/union metrics are stored in DELIVERY_REVIEW_1249_1250_1251.json; the original log is unchanged.
- Target 1250: preserved lines are evaluated only as an unverified saved-candidate diagnostic because the append-only evidence correction says the user-visible display is not independently verified. Excluded from actual-purchase learning.
- Target 1251: the 2026-11-20 research-selected artifact is pre-draw; outcome comparison is deferred until the official 2026-11-21 result. Purchase is not confirmed.
- Confirmed purchases in the registry: 0. No purchase-learning aggregate is updated.

## Decision
E078 computation completed as a design-only uncertainty stress test. No predictive model is promoted; no candidate numbers or purchase lines are generated or displayed; no freeze/seal is created.
