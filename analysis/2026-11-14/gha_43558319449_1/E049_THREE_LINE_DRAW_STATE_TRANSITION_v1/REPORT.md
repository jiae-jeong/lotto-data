# E049 — Previous-main-draw-state to next-main transition

- Study status: **STRICT_FAIL**
- Data cutoff: **1249**; source rows: **1249**
- Walk-forward targets: **849** (401..1249)
- Random bundles: **101,880** (120 per target)
- Feature: previous draw's six main numbers only; bonus excluded
- Portfolio: three disjoint six-number lines, union18
- Randomness is used only for the geometry-matched null, never selection

| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.515901 | 1.514256 | +0.001645 | -0.057248 | +0.057004 |
| any2 | 0.484099 | 0.474976 | +0.009123 | -0.028569 | +0.050348 |
| any3 | 0.069494 | 0.071355 | -0.001861 | -0.023063 | +0.015806 |
| winning_union_coverage | 2.408716 | 2.400000 | +0.008716 | -0.071378 | +0.102945 |

- any2-positive 50-target block share: **47.06%** (8/17 blocks)
- Historical strict gate: **FAIL**
- STRICT_PASS_READY: **not created**
- Prospective minimum/completion rule: **unspecified and not adopted**
- No final purchase lines or freeze/seal were generated.

Each target is scored before its outcome enters global counts and transition history. One frozen specification, no variants or tuning.
