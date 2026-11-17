# E067 — Previous-draw prime-count transition

Execution date: 2026-11-17; data cutoff: 1250; targets: 850 (401..1250).

## Frozen question
Whether the one-component prime-count state of the immediately preceding draw contains cutoff-safe information about the next draw's main-number inclusion, sufficient to improve a deterministic three-line disjoint union18 portfolio over the exact geometry-matched null.

## Execution
- Predictions: 850; random bundles: 102000.
- Training-cutoff violations: 0; leakage failures: 0.
- Portfolio geometry violations: 0; random geometry violations: 0.
- Bootstrap: 4000 replicates; 50-target blocks: 17; final remainder retained.

## Results versus exact geometry-matched null
- max_hits: observed=1.47294118; null=1.51425625; delta=-0.04131507; adjusted CI=[-0.09543272, 0.02456728].
- any2: observed=0.42941176; null=0.47497624; delta=-0.04556448; adjusted CI=[-0.07968213, -0.00438801].
- any3: observed=0.07176471; null=0.07135491; delta=0.00040980; adjusted CI=[-0.02076667, 0.02629215].
- winning_union_coverage: observed=2.32823529; null=2.40000000; delta=-0.07176471; adjusted CI=[-0.15176471, 0.02823529].
- Positive any2 blocks: 2/17 (11.76%); required 65%.

## Interpretation
- Historical strict portfolio gate: FAIL.
- Prospective confirmation remains unspecified by policy; STRICT_PASS_READY is therefore false regardless of historical results.
- This is one historical exploratory signal-family test, not an untouched prospective sample and not a purchase recommendation.
- No thresholds, alpha, block length, comparator, or model variants were changed after registration.

No purchase lines were generated or published.
