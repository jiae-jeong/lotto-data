# Next-Round Research Baseline after V27

## Decision
Freeze **V26 (HYBRID_SLOW_CORE_BLEND_TAIL_V26)** as the current best research baseline.
Do not promote V27.
Do not continue changing parameters merely to force a PASS on the same 401..1246 outer evaluation window.

## Why V26 is the baseline
Compared with the matched joint label-permutation comparator across 846 walk-forward targets:
- max_hits delta: +0.04968
- any2 delta: +0.02369
- any3 delta: +0.02051
- any4 delta: +0.00505
- winning_union_coverage delta: +0.07007

V26 is the first variant in this sequence whose adjusted max_hits CI lower bound is above zero:
- max_hits adjusted CI: [0.00244, 0.09917]
- max_hits positive 50-round blocks: 76.47%

Remaining blockers:
- any2 adjusted CI lower bound: -0.00618
- any3 adjusted CI lower bound: -0.00729
- any2 positive 50-round blocks: 64.71% (11/17; strict threshold requires >=65%)

## V27 rejection
V27 introduced eight adaptive experts and downside-penalized selection. It reduced stability instead of improving it:
- max_hits delta fell to +0.03846 and its adjusted CI lower bound returned below zero.
- any2 / any3 lower bounds remained below zero.
Therefore V27 is rejected and must not replace V26.

## Research discipline from here
1. Keep V26 code and gate frozen as the baseline.
2. Do not call a later variant validated merely because repeated tuning eventually crosses the same historical gate; repeated use of the same outer window creates research-selection bias.
3. When round 1247 is completed, append the real outcome once, run the frozen V26 prospectively, record its hit metrics, and only then begin a new improvement cycle for round 1248.
4. Any new candidate must be compared against frozen V26, matched random, and the same no-future-leakage protocol.
5. Random/fallback ticket generation is not a research substitute and must not be labeled as a learned final portfolio.
