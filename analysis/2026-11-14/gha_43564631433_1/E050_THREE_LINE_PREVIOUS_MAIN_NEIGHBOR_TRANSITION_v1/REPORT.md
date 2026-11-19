# E050 — Previous-main-number neighborhood transition

- Study status: **STRICT_FAIL**
- Data cutoff: **1249**; source rows: **1249**
- Walk-forward targets: **849** (401..1249)
- Random bundles: **101,880** (120 per target)
- Feature: each candidate's minimum absolute distance to the previous draw's six main numbers; bonus excluded
- Fixed bins: exact repeat / distance 1 / distance 2 / distance 3+
- Portfolio: exactly three pairwise-disjoint six-number lines, union18
- Randomness is used only for the geometry-matched null, never for selection

| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.488810 | 1.514256 | -0.025446 | -0.076094 | +0.029913 |
| any2 | 0.460542 | 0.474976 | -0.014434 | -0.053304 | +0.023257 |
| any3 | 0.070671 | 0.071355 | -0.000684 | -0.020707 | +0.021696 |
| winning_union_coverage | 2.378092 | 2.400000 | -0.021908 | -0.114959 | +0.072320 |

- any2-positive 50-target block share: **35.29%** (6/17 blocks)
- Historical strict gate: **FAIL**
- STRICT_PASS_READY: **not created**
- Prospective minimum/completion rule: **unspecified and not adopted**
- No final purchase lines or freeze/seal were generated.

Each target is scored before its outcome enters the global counts and transition history. One frozen specification; no variants or tuning.
