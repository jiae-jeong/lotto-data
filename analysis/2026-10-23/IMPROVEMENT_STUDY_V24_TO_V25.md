# 1247 Improvement Study — V24 → V25

## Non-negotiable gate
- Do not lower the strict gate to manufacture PASS.
- No random/fallback ticket substitution.
- No 1247 outcome may enter training or model selection.
- Outer evaluation remains targets 401..1246 with matched joint label-permutation comparator and 50-round block bootstrap.

## What V24 improved
V24 kept V18's learned number ranking and fixed ranks 1–6 together, while adapting only ranks 7–30 partitioning from prior data.

Observed delta vs matched random:
- max_hits: +0.02356
- any2: +0.00837
- any3: +0.00749
- any4: +0.00725
- winning_union_coverage: +0.03621

This is the first recent variant in which all primary point estimates were positive.

## Why V24 still failed
Strict lower CIs remained below zero:
- max_hits lower CI: -0.02706
- any2 lower CI: -0.02579
- any3 lower CI: -0.02022

50-round positive-block shares:
- max_hits: 64.71%
- any2: 52.94%
- any3: 52.94%
- winning_union_coverage: 52.94%

The final partial block (targets 1201..1246) is negative for all four tracked deltas, so instability is not only an early-history artifact.

## Diagnosis
Partitioning alone cannot fix the instability. V18 uses a single AdaGrad state accumulated from the entire history. As g2 grows, effective learning rates shrink, so the ranker becomes slow to react to regime shifts. V23 showed that changing line layout without preserving the elite core damages any3. V24 restored the elite core and recovered any3, but the underlying ranking still has time-local weakness.

## V25 hypothesis
Maintain multiple online V18 learners with different memory speeds:
- slow: original cumulative AdaGrad behavior
- medium: mild weight shrink + mild g2 decay
- fast: stronger weight shrink + stronger g2 decay
- blend: equal z-score blend of the three rankers

At every target, choose the learner only from its prior rolling 120-target portfolio outcomes. Keep the V22 core6 + round-robin rank30 layout fixed so the experiment isolates ranking adaptation rather than changing ranking and portfolio geometry simultaneously.

V25 promotion requirement remains exactly the same strict gate. If V25 fails, reject this hypothesis and do not use its 1247 lines as a validated replacement.
