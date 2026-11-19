# E055 — Triple recent-strength falsification

- Result: **PREDICTIVE_TRIPLE_STRENGTH_NOT_SUPPORTED**
- Source: frozen E045 target-1251 three-line predictions, cutoff 1250; this does not alter E045.
- Predictive question: does the previous 100-target any3 rate predict the next non-overlapping 50-target any3 rate?
- Evaluation blocks: 15 (targets 501–1250); each trailing window ends at block_start−1.
- Random comparator: 120 full geometry-matched random trajectories, 102,000 random portfolios total.
- Correlation statistic: Pearson; one predeclared test, alpha 0.05.
- Uncertainty: 4,000 moving-block bootstrap replicates, block length 3 adjacent 50-target block-pairs.

- Model Pearson correlation: **-0.308742**
- 95% moving-block bootstrap CI: **[-0.612338, -0.017509]**
- Random mean correlation: **-0.091001**
- Random 95th percentile: **+0.280269**
- One-sided random tail probability: **0.8264**
- Predeclared support rule: **FAIL**
- No model selection, ticket generation, purchase recommendation, or STRICT_PASS_READY.

| Block start | Trailing 100 any3 rate | Forward 50 any3 rate | Random trailing mean | Random forward mean |
|---:|---:|---:|---:|---:|
| 501 | 4.0000% | 12.0000% | 7.0417% | 7.2667% |
| 551 | 7.0000% | 6.0000% | 7.3583% | 7.1500% |
| 601 | 9.0000% | 4.0000% | 7.2083% | 7.2500% |
| 651 | 5.0000% | 8.0000% | 7.2000% | 7.2333% |
| 701 | 6.0000% | 6.0000% | 7.2417% | 6.9000% |
| 751 | 7.0000% | 2.0000% | 7.0667% | 6.7167% |
| 801 | 4.0000% | 6.0000% | 6.8083% | 6.7833% |
| 851 | 4.0000% | 2.0000% | 6.7500% | 7.0667% |
| 901 | 4.0000% | 8.0000% | 6.9250% | 7.3500% |
| 951 | 5.0000% | 10.0000% | 7.2083% | 7.3000% |
| 1001 | 9.0000% | 8.0000% | 7.3250% | 6.8167% |
| 1051 | 9.0000% | 0.0000% | 7.0583% | 6.9833% |
| 1101 | 4.0000% | 2.0000% | 6.9000% | 6.8167% |
| 1151 | 1.0000% | 2.0000% | 6.9000% | 6.7333% |
| 1201 | 2.0000% | 16.0000% | 6.7750% | 7.0667% |

This is a historical falsification diagnostic. A positive result would not establish prospective purchase readiness; the existing strict gate and prospective confirmation requirement remain unchanged.
