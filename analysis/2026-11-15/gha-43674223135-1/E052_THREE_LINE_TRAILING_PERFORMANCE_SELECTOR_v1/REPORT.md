# E052 — Nested trailing-performance selector for three-line portfolios

**New research question:** Can one fixed, cutoff-safe selector choose among five already frozen three-line portfolios using only the preceding 100 target rounds' any2 performance, and outperform the exact disjoint-union18 null on the next target?

## What was executed
- Historical nested walk-forward: targets 501–1249 (749 targets).
- Five frozen candidate portfolios; one selector; trailing window 100; selection metric any2; fixed tie-break order.
- Matched-random portfolios: 89,880 (120 per target), preserving three disjoint six-number lines and union18.
- Moving-block bootstrap: 4,000 replicates, block length 50, final remainder retained (49 targets).
- Each target's selected model is chosen using only target outcomes through t−1; no target or future outcome enters its own selection.
- This is a historical nested screen, not prospective confirmation.

## Primary strict metrics
| Metric | Selector mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.502003 | 1.514256 | -0.012254 | -0.079009 | +0.042486 |
| any2 | 0.467290 | 0.474976 | -0.007687 | -0.053080 | +0.035037 |
| any3 | 0.069426 | 0.071355 | -0.001929 | -0.021956 | +0.010087 |
| winning_union_coverage | 2.403204 | 2.400000 | +0.003204 | -0.107610 | +0.085981 |

- Any2-positive 50-target block share: **33.33%** (5/15 blocks; minimum 65%).
- Historical strict gate: **FAIL**.
- Model selection counts: E045_THREE_LINE_DISJOINT_PORTFOLIO_WALKFORWARD_v1=155, E048_THREE_LINE_BONUS_TO_MAIN_TRANSITION_v1=235, E049_THREE_LINE_DRAW_STATE_TRANSITION_v1=202, E050_THREE_LINE_PREVIOUS_MAIN_NEIGHBOR_TRANSITION_v1=98, E051_THREE_LINE_PAIR_CONTEXT_CONDITIONAL_v1=59.

## Interpretation and policy effect
- The selector is a new model-selection procedure, not a new independent signal family. It does not modify any source model or its historical predictions.
- Static model scorecards are descriptive; only the single preregistered nested selector is tested against the strict null.
- No threshold, alpha, block length, comparator, candidate model, or lookback was tuned after evaluation.
- STRICT_PASS_READY is not created. Prospective minimum target count and completion rule remain unspecified.
- No purchase recommendation, final purchase lines, freeze, or seal were generated.

## Source and scope limitations
- The E051 source file includes a 1250 cutoff, but this study uses only its already frozen target rows 401–1249; the target 1250 row is excluded.
- The historical target sample has already been observed and cannot serve as untouched prospective confirmation.
- All source portfolios were independently verified and recomputed against the canonical 1–1249 outcomes before selection.
