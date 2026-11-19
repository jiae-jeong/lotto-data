# E054 — Rolling draw-frequency concentration regime

- Study status: **STRICT_FAIL**
- Data cutoff: **1250**; source rows: **1250**
- Walk-forward targets: **850** (401..1250)
- Random bundles: **102,000** (120 per target)
- Feature: prior 100-draw main-number HHI classified against the median of 200 earlier rolling HHI windows; bonus excluded
- Estimator: one fixed Beta-smoothed regime-conditional inclusion probability, prior mean 6/45 and strength 45
- Portfolio: three pairwise-disjoint six-number lines, union18, using unchanged E045 selector
- Randomness is used only for the geometry-matched null, never for selection

| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.477647 | 1.514256 | -0.036609 | -0.090727 | +0.023391 |
| any2 | 0.458824 | 0.474976 | -0.016153 | -0.054976 | +0.032083 |
| any3 | 0.062353 | 0.071355 | -0.009002 | -0.026649 | +0.008645 |
| winning_union_coverage | 2.351765 | 2.400000 | -0.048235 | -0.149412 | +0.048235 |

| Regime | Targets | Model mean max hits | Model any2 | Model any3 | Random mean max hits | Random any2 |
|---|---:|---:|---:|---:|---:|---:|
| LOW | 394 | 1.479695 | 45.6853% | 7.6142% | 1.513135 | 47.2758% |
| HIGH | 456 | 1.475877 | 46.0526% | 5.0439% | 1.511531 | 47.3593% |

- Any2-positive 50-target block share: **35.29%** (6/17 blocks)
- Historical strict gate: **FAIL**
- STRICT_PASS_READY: **not created**
- Prospective minimum/completion rule: **unspecified and not adopted**
- No final purchase lines, recommendation, or freeze/seal were generated.

Each target's current regime uses only draws through t-1. Each historical outcome enters its own pre-outcome regime count only after its prediction is frozen. The HHI reference windows end before the current 100-draw window. One frozen signal family, one estimator, no variants or tuning.
