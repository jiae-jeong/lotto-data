# E068 — Previous-two-draw overlap-count transition

Execution date: 2026-11-17; data cutoff: 1250; targets: 850 (401..1250).

## Frozen question
Whether the one-component aggregate overlap-count state of the two immediately preceding draws contains cutoff-safe information about the next draw's main-number inclusion, sufficient to improve a deterministic three-line disjoint union18 portfolio over the exact geometry-matched null.

## Execution
- Predictions: 850; random bundles: 102000.
- Training-cutoff violations: 0; leakage failures: 0.
- Portfolio geometry violations: 0; random geometry violations: 0.
- Bootstrap: 4000 replicates; 50-target blocks: 17; final remainder retained.

## Results versus exact geometry-matched null
- max_hits: observed=1.51882353; null=1.51425625; delta=0.00456728; adjusted CI=[-0.06366801, 0.07868493].
- any2: observed=0.47764706; null=0.47497624; delta=0.00267082; adjusted CI=[-0.04791742, 0.04737670].
- any3: observed=0.07176471; null=0.07135491; delta=0.00040980; adjusted CI=[-0.02782550, 0.03452745].
- winning_union_coverage: observed=2.34235294; null=2.40000000; delta=-0.05764706; adjusted CI=[-0.15529412, 0.04941176].
- Positive any2 blocks: 9/17 (52.94%); required 65%.

## Interpretation
- Historical strict portfolio gate: FAIL.
- Prospective confirmation remains unspecified by policy; STRICT_PASS_READY is therefore false regardless of historical results.
- This is one historical exploratory signal-family test, not an untouched prospective sample and not a purchase recommendation.
- No thresholds, alpha, block length, comparator, or model variants were changed after registration.

No purchase lines were generated or published.
