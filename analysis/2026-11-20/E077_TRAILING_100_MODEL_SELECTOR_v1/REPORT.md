# E077 — Trailing-100 dynamic model selector

**Classification:** COMPUTATION COMPLETE; historical cutoff-safe diagnostic only; no purchase-policy promotion.

## Frozen rule
For each target t=401..1250, choose among A_v2, C_v2, and contrarian_v2 using the highest mean stored hit count over targets t-100..t-1. Tie order was preregistered as A_v2, C_v2, contrarian_v2. No model parameter, window length, or tie rule was tuned after evaluation.

## Integrity
- Parsed component rows: 3150 (expected 3,150)
- Evaluation targets: 850/850
- Bad cutoff rows: 0; invalid tickets: 0; hit-count mismatches: 0; duplicate target-model rows: 0
- Prospective target labels are not used in the selector decision; all three component predictions for target t state training_through_round=t-1.
- Source data cutoff: 1250; data SHA-256: 7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2

## Dynamic selector outcome
- Mean hits: 0.778824 vs exact uniform 6/45 expectation 0.800000 (delta -0.021176)
- Any2+: 15.882% vs 17.531% (delta -1.648 percentage points)
- Any3+: 2.941% vs 2.383%
- Any4+: 0.118% vs 0.139%
- Model selection counts: A_v2 340; C_v2 144; contrarian_v2 366
- Any2-positive non-overlapping 50-target blocks: 7/17 (41.18%); diagnostic threshold 65%.

## Fixed component comparison
- A_v2: mean hits 0.801176; any2 17.059%; any3 3.294%; any4 0.235%
- C_v2: mean hits 0.798824; any2 17.647%; any3 3.059%; any4 0.235%
- contrarian_v2: mean hits 0.791765; any2 17.529%; any3 2.824%; any4 0.000%

## Adjusted moving-block intervals
Four endpoints; family alpha 0.05, per-endpoint alpha 0.0125; 4,000 two-sided moving-block bootstrap replicates, block length 50, all 850 targets retained.

- Mean hits: [-0.078824, 0.037647]
- Any2+ rate: [-0.047073, 0.012935]
- Any3+ rate: [-0.007363, 0.020872]
- Any4+ rate: [-0.001393, 0.003312]

## Interpretation and limits
This is an adaptive historical selector diagnostic, not independent prospective evidence. It does not recover the original legacy A/C/contrarian models; the candidates are RECOVERED_SUCCESSOR_V2 models. A one-ticket result does not validate the separate three-line weekly portfolio, its allocator, or its strict gate. Even a positive historical point estimate would not create STRICT_PASS_READY. No candidate or final purchase lines, freeze, or seal were generated.
