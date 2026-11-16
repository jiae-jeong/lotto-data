# E061 — B-model ensemble error-correlation and dilution diagnostic

- Preregistered: 2026-11-16 12:10:53 KST, before E061 calculations
- Source: `analysis/2026-11-16/MASTER_FULL_V4_022804_577202/B_PREDICTIONS_UNIQUE.csv` (Git blob `83e9772654466c092ccef7a7287d8106359a6c80`)
- Targets: 201–1250 (1,050); 8 model rows per target (8,400 total)
- Cutoff rule: each target uses training through target minus one
- Evidence class: historical single-ticket diagnostic; not three-line purchase evidence

## Main findings

- Seven component models produced 21 pairwise correlations of per-target hit counts.
- Mean correlation: **0.0201**; median: **-0.0205**; range: **-0.0820 to 0.3157**.
- The largest pair was long_frequency vs frequency_plus_gap (**0.3157**); other pairs were weakly related or slightly negative.
- Combined equal-rank mean hits: **0.7657**.
- Unweighted component mean: **0.7928**; combined-minus-component-mean: **-0.0271**.
- Exact single-ticket random expectation: **0.8000** mean hits.

## Uncertainty and interpretation

Eight predeclared contrasts were evaluated with 4,000 moving non-overlapping 50-target block-bootstrap replicates (seed 20261116). Simultaneous two-sided intervals use Bonferroni family alpha 0.05 (99.375% per contrast). **All eight intervals include zero.** The historical point estimate is consistent with possible dilution, but the uncertainty is too wide to establish it. No component is promoted.

## Integrity

- Rows: 8,400; targets: 1,050; models per target: 8.
- Duplicate or missing target/model rows: none.
- Training cutoff violations: 0.
- Source SHA256: `c1a342cab80b73703410dd4485427d2ce0cdd2aabfe199fccd6d556723e8ab40`.
- Preregistration SHA256: `d60925e774f1493f9be2f477cd585db39a93bed7671ea8411c278a09dfcbd91e`.

## Limitations

This uses single-ticket B model hit counts, not ticket-number overlap. It is a historical diagnostic, not an untouched prospective test and not evidence for the target-1251 three-line portfolio. No thresholds, alpha, block length, comparators, purchase policy, or finalizer rules were changed. No purchase numbers were generated.
