# E048 — Bonus-to-next-main transition, three-line portfolio

> DUPLICATE REPRODUCTION ONLY: this run reproduces E048 run 43547128786 byte-for-byte for primary outputs. It is not an independent research axis and is not counted toward readiness.

- Study status: **STRICT_FAIL**
- Data cutoff: **1249**; source rows: **1249**
- Walk-forward targets: **849** (401..1249)
- Random bundles: **101,880** (120 per target)
- Portfolio geometry: three disjoint six-number lines, union18
- Selection randomness: prohibited; randomness used only for matched null

## Paired results versus exact union18 null

| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.511190 | 1.514256 | -0.003067 | -0.066671 | +0.067605 |
| any2 | 0.484099 | 0.474976 | +0.009123 | -0.037992 | +0.058593 |
| any3 | 0.062426 | 0.071355 | -0.008929 | -0.026596 | +0.009917 |
| winning_union_coverage | 2.427562 | 2.400000 | +0.027562 | -0.056066 | +0.130035 |

- any2-positive 50-target block share: **47.06%** (8/17 blocks)
- Historical strict gate: **FAIL**
- STRICT_PASS_READY: **not created**
- Prospective confirmation minimum and completion rule: **unspecified; not adopted**
- No purchase lines were released; no final freeze/seal was created.

The model uses only the previous draw's bonus number and prior main-draw outcomes. Each target is scored before its outcome is added to the transition counts. The single frozen specification was evaluated once; no parameter search or threshold change was performed.
