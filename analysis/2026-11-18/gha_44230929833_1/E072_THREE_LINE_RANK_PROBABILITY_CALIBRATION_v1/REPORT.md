# E072 — Candidate consensus-rank probability calibration

Status: **HISTORICAL_CALIBRATION_NO_EDGE**

- Frozen calibration window: targets 201–600 (18,000 candidate observations).
- Untouched chronological evaluation: targets 601–1250 (650 targets; 29,250 candidate observations).
- Calibration: five training-score quintile bins, Beta-binomial prior mean 6/45 and strength 45, then per-target probability normalization to six expected inclusions.
- Random control: 120 probability-vector permutations per target (78,000 total).
- Bootstrap: 4,000 moving-block replicates, block length 50, Bonferroni alpha 0.0250 per primary metric.

| Metric | Model | Exact uniform | Model − uniform | Adjusted CI | Random permutation |
|---|---:|---:|---:|---:|---:|
| Brier (lower better) | 0.11557034 | 0.11555556 | 0.00001478 | [-0.00002293, 0.00005976] | 0.11557233 |
| Log loss (lower better) | 0.39273850 | 0.39267447 | 0.00006404 | [-0.00010405, 0.00025302] | 0.39274696 |

Calibration gate: **FAIL**. Both adjusted CI upper bounds must be strictly below zero.

This is candidate-probability calibration, not a three-line portfolio evaluation. It cannot qualify STRICT_PASS_READY and emits no purchase lines. The evaluation window is historical, not an independent future sample. No strict thresholds, alpha levels, block lengths, or portfolio comparators were changed.
