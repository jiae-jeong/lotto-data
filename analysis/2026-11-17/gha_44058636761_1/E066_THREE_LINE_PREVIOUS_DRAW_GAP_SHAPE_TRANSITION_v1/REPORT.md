# E066 — Previous-draw gap-shape transition

Execution date: 2026-11-17; data cutoff: 1250; targets: 850 (401..1250).

## Frozen question
Whether the five-component gap-shape state of the immediately preceding draw contains cutoff-safe information about the next draw's main-number inclusion, sufficient to improve a deterministic three-line disjoint union18 portfolio over the exact geometry-matched null.

## Execution
- Predictions: 850; random bundles: 102000.
- Training-cutoff violations: 0; leakage failures: 0.
- Portfolio geometry violations: 0; random geometry violations: 0.
- Bootstrap: 4000 replicates; 50-target blocks: 17; final remainder retained.

## Results versus exact geometry-matched null
- max_hits: observed=1.47058824; null=1.51425625; delta=-0.04366801; adjusted CI=[-0.10837390, 0.01868493].
- any2: observed=0.43764706; null=0.47497624; delta=-0.03732918; adjusted CI=[-0.07850566, 0.00737670].
- any3: observed=0.06823529; null=0.07135491; delta=-0.00311961; adjusted CI=[-0.02429608, 0.01923333].
- winning_union_coverage: observed=2.33058824; null=2.40000000; delta=-0.06941176; adjusted CI=[-0.15294118, 0.01764706].
- Positive any2 blocks: 4/17 (23.53%); required 65%.

## Interpretation
- Historical strict portfolio gate: FAIL.
- Prospective confirmation remains unspecified by policy; STRICT_PASS_READY is therefore false regardless of historical results.
- This is one historical exploratory signal-family test, not an untouched prospective sample and not a purchase recommendation.
- No thresholds, alpha, block length, comparator, or model variants were changed after registration.

No purchase lines were generated or published.
