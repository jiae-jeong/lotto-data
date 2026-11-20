# Daily Lotto Research Report — 2026-11-21

## 1. New study: E078 empirical multivariate block-resampling power stress

**Classification:** DESIGN ONLY; historical planning stress test, not model evidence, not prospective confirmation, not a strict PASS.

Question: does a joint empirical resampling design for the four three-line strict-gate endpoints materially change the planning power estimate relative to E046's normal-theory independence approximation?

### Frozen inputs and execution
- Source cutoff 1249; walk-forward targets 401–1249 (849). Rounds 1244–1249 are explicitly contaminated live-history diagnostics, not clean holdout.
- E045 predictions SHA-256 `63741597dced378876c7ac1d7a15fb5864e03f3a2b765a42e9452591867d3500`; Git blob `e55b8f5997dde36ff55b93b4bb53d20b8ad2ba69`.
- E045 exact geometry-matched random comparator SHA-256 `19566decad6fac44651341046d10a6241ba40abc7575771736fd53ef8d035a25`; Git blob `fa0fe8e2317f22b01dbd3b3aa15f4df68d8680c3`.
- Recomputed all 849 target cutoffs (t-1), stored line hits, max-hit, any2/any3, union coverage, three-line disjoint union18 geometry, and exact-null constants. Cutoff violations 0; geometry violations 0; stored-hit mismatches 0.
- 16 complete 50-target blocks plus final 49-target remainder retained. 36 design cells × 10,000 Monte Carlo trajectories.
- Effect grid: 0.25, 0.50, 0.75, 1.00 historical block SD. Four endpoints and strict alpha unchanged.

### Results
The historical four-endpoint block correlations are positive:
- max-hit / any2: 0.857
- max-hit / any3: 0.823
- max-hit / union coverage: 0.777
- any2 / any3: 0.511
- any3 / union coverage: 0.625

Empirical joint probability of passing all four planning lower-bound checks and the 0.65 positive-any2-block-share condition, under a hypothetical +1.0 block-SD shift per metric:

| Prospective targets | Empirical joint probability | E046 independence approximation |
|---:|---:|---:|
| 400 | 8.33% | 13.82% |
| 600 | 19.99% | 46.72% |
| 800 | 32.03% | 73.63% |
| 1,000 | 46.42% | 89.92% |

At 1,000 targets and a +0.75 SD hypothetical shift, the empirical joint estimate was 5.72% versus E046's 39.19%. At 1,000 targets and +1.0 SD, the any3 lower-bound positivity probability was only 49.82%, while the any2 block-share gate passed in 99.83% of simulated paths. This makes the any3 tail endpoint a material bottleneck under this historical resampling stress.

**Interpretation:** E046's independence/normal approximation can be materially optimistic relative to this empirical block-resampling stress. This is not a proof that E046 is wrong or that the empirical estimate is the true future power: only 16 full historical blocks plus one 49-target remainder are available, and the empirical resampling assumptions are limited. The operational moving-block bootstrap on future preregistered prospective observations remains mandatory. No prospective target count or completion rule was adopted.

## 2. Current target-1251 strict status

The latest cutoff-matched three-line gate remains **STRICT_FAIL** at cutoff 1250.

| Metric | Delta vs exact geometry-matched null | Adjusted CI |
|---|---:|---:|
| max-hit | -0.022492 | [-0.083668, +0.032803] |
| any2 | -0.007917 | [-0.045564, +0.028553] |
| any3 | -0.012531 | [-0.036061, +0.006292] |
| winning-union coverage | -0.016471 | [-0.123529, +0.069412] |

Any2-positive 50-target block share: 8/17 = 47.06%, below 65%. Prospective confirmation is unevaluated because the minimum target count and completion rule remain unspecified. No validated model, STRICT_PASS_READY, freeze, or seal exists.

## 3. Candidate stage vs allocator stage

The latest candidate-recall scorecard is still the cutoff-1250, 1,050-target historical diagnostic; no new target result exists before the 1251 draw. Its small positive point deltas versus matched random are not confidence-bound evidence and do not qualify a candidate model. E059's E054 candidate-recall audit remained below random point estimates at TOP10/15/20/25/30 with adjusted intervals including zero.

The new dated review of preserved delivery records found:
- Target 1249 displayed five-line intermediate candidate: line hits [2,1,0,0,1], union coverage 4/6, max-hit 2, any2 yes, any3 no. Three-plus was possible within the displayed portfolio union but not realized on one line. The original TOP-K candidate bank and a presealed source artifact were not found, so candidate-recall failure cannot be assigned.
- Target 1250: the five-line saved candidate was scored as a diagnostic only. Display evidence was explicitly corrected as unverified. Line hits [1,0,0,1,1], union coverage 2/6, max-hit 1; a 2+ line was possible within the saved union but not realized. This is not a verified delivery or purchase.
- Target 1251: the 2026-11-20 research-selected three-line artifact is pre-draw for the 2026-11-21 draw. Its outcome comparison is deferred until the official result. Purchase remains unconfirmed.

Confirmed purchase registry count remains 0. Recommendation-review evidence is kept separate from actual-purchase learning. No source lines were reconstructed and DELIVERY_LOG was not changed in this run.

## 4. Existing validation and failure inventory reviewed

- 1250 remediation plan: V54/V83/V84/V85/V86 each failed at least one strict gate; the common final-48-target any2 loss remains a diagnostic, not a tuning target.
- E075: V54–V86 failure audit preserved; no promotion.
- E076: six preserved artifacts over four historical rounds; 2+/3+ candidate opportunity and realized line outcomes remain post-hoc diagnostics, not actual purchase evidence.
- E077 trailing-100 selector: cutoff-safe historical selector, but mean hits 0.778824 vs exact 0.8; any2 15.88% vs 17.53%; positive any2 block share 41.18%; all adjusted intervals include zero. No promotion.
- E045 three-line allocator, E054 rolling-concentration model, and E060 snake partition all remain historical STRICT_FAIL.
- The older 2026-10-12 nested regime/dynamic-selector study independently verified 10,140 inner replays and 1,935 nested outer replays, but was explicitly POST_HOC_EXPLORATORY, single-ticket/model-selection research, and not evidence for the current three-line portfolio. It does not resolve the target-1251 prospective requirement.
- E011 nested 3+/4+ single-ticket tail study also remained exploratory with no Holm-significant positive comparisons.

## 5. Policy and data integrity

- Canonical `lotto_data.csv`: rounds 1–1250, 1,250 contiguous rows; SHA-256 `7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2`; Git blob `66431d711919f179e4cb1349e2f7295c68a8735e`. Round 1251 is not yet present at the 08:03 KST audit.
- The 1250 official API endpoint was not directly retrieved; two independent published reports agree on the 1250 result. No direct API retrieval is claimed.
- Appended 2026-11-21 policy amendment to AGENTS.md and LOTTO_PROJECT_PROTOCOL.md: it supersedes the 2026-11-20 exception that allowed research-selected lines during strict FAIL. From now on, no candidate numbers, TOP30, core/tail lists, or purchase lines may be displayed before a verified strict PASS. No random/fallback numbers. Existing strict thresholds and three-line policy are unchanged.
- The 2026-11-20 target-1251 display event remains in DELIVERY_LOG as historical evidence; it is not repeated here and purchase is not confirmed.

## 6. Next tests
1. After the 1251 draw, append a separate post-draw review against the already stored pre-draw artifact; never alter its bytes.
2. Keep the three-line prospective minimum target count and completion rule unresolved until an explicit policy decision; do not import the older single-ticket 200-target horizon.
3. Continue only preregistered, independent research. Do not tune to 1244–1249 or use those rounds as clean holdout.

## Output and provenance
- E078 report/results: `analysis/2026-11-21/E078_THREE_LINE_EMPIRICAL_BLOCK_POWER_STRESS_v2/`
- E078 preregistration: `research/weekly_purchase/1251/E078_THREE_LINE_EMPIRICAL_BLOCK_POWER_STRESS_PREREG_20261121.json`
- E078 implementation repair addenda: `research/weekly_purchase/1251/E078_IMPLEMENTATION_REPAIR_ADDENDUM_20261121_V1.json`, `E078_POSTRUN_REVIEW_PARSER_CORRECTION_ADDENDUM_20261121_V1.json`, `E078_WORKFLOW_OUTPUT_PATH_CORRECTION_ADDENDUM_20261121_V1.json`
- Historical closed-loop status: `analysis/2026-11-21/HISTORICAL_CLOSED_LOOP_STATUS.json`
- Recommendation error note: `research/weekly_purchase/1251/ERROR_NOTE_RECOMMENDATION_REVIEW_1249_1250_20261121.json`
- E078 workflow final successful run: `https://github.com/jiae-jeong/lotto-data/actions/runs/44835120396`
- No purchase lines, candidates, freeze, seal, or new DELIVERY_LOG event were created by this run.
