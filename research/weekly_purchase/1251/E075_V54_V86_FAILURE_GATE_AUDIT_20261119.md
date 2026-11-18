# V54–V86 failure-gate audit (2026-11-19)

Evidence class: recheck of existing target-1249 outputs at data cutoff 1248. This is not a clean holdout, not prospective evidence, and not a new model evaluation.

The unchanged 1249 five-line gate requires adjusted moving-block CI lower bounds above zero for max-hit, any2, and any3, plus an any2-positive 50-target block share of at least 65%. The final 48-target remainder block is retained. Winning-union coverage is shown as an auxiliary metric and is not substituted for the target-1251 three-line four-metric gate.

| Version | max-hit CI lower | any2 CI lower | any3 CI lower | any2 positive blocks | Final 48-target any2 delta | Gate |
|---|---:|---:|---:|---:|---:|---|
| V54 | +0.016058 | -0.000945 | +0.002497 | 14/17 (82.35%) | -0.105309 | FAIL: any2 |
| V83 | +0.010134 | +0.001925 | -0.005204 | 14/17 (82.35%) | -0.105309 | FAIL: any3 |
| V84 | +0.000655 | -0.012794 | +0.000706 | 13/17 (76.47%) | -0.105309 | FAIL: any2 |
| V85 | -0.002510 | -0.014901 | +0.003674 | 13/17 (76.47%) | -0.105309 | FAIL: max-hit and any2 |
| V86 | -0.004866 | -0.004287 | -0.007830 | 11/17 (64.71%) | -0.021976 | FAIL: max-hit, any2, any3, block share |

## Interpretation

- V54's any2 lower bound misses zero narrowly; this is still a strict failure.
- V83 trades into an any3 failure despite a positive any2 lower bound.
- V84 does not rescue any2.
- V85 fails both max-hit and any2.
- V86 fails all three lower-bound tests and misses the 65% block-share threshold (64.71%).
- The common -0.105309 final-block any2 delta in V54–V85 is preserved as a descriptive diagnostic. It is not a new rule or a reason to tune the already examined block.
- None of these historical five-line versions is eligible for target-1251 three-line purchase readiness.

No thresholds were relaxed; no model was promoted.
