# Manual full recovery — 2026-10-16

Status: PARTIAL MASTER / ACTUAL COMPUTATION COMPLETED. No candidate/recommendation/final lines generated.

## Execution

- Canonical snapshot: rounds 1..1245; integrity PASS; SHA-256 `e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4`.
- Full number statistics and 10/30/50/100 windows were recomputed from all 1,245 rows.
- Full structural summaries were recomputed.
- All 990 pairs and all 14,190 triples were recalculated with BH correction; q<0.05 survivors were 0 and 0.
- Frozen B source was rerun for targets 201..1245. The overlapping anchor/horizon implementation produced 33,480 records; unique target-model forecasts = 8,360; leakage failures = 0.
- 1,000 uniform random tickets were newly generated for each of 1,045 targets using seed 20261016: 1,045,000 tickets total. Random mean hits = 0.7992229665.

## B versus fresh same-target random

| Model | Mean hits | Delta | 95% moving-block CI | 3+ | 4+ |
|---|---:|---:|---:|---:|---:|
| combined_equal_rank | 0.763636 | -0.035587 | [-0.079224, +0.009332] | 1.5311% | 0.2871% |
| current_gap | 0.795215 | -0.004008 | [-0.054489, +0.044069] | 1.4354% | 0.0000% |
| frequency_plus_gap | 0.796172 | -0.003051 | [-0.046064, +0.041591] | 2.0096% | 0.1914% |
| long_frequency | 0.782775 | -0.016448 | [-0.063068, +0.031980] | 2.7751% | 0.1914% |
| pair_association | 0.805742 | +0.006519 | [-0.038746, +0.052932] | 1.3397% | 0.0000% |
| recent_momentum | 0.762679 | -0.036544 | [-0.084609, +0.014513] | 1.3397% | 0.0000% |
| structure_profile | 0.794258 | -0.004965 | [-0.057221, +0.046340] | 2.5837% | 0.0957% |
| triple_association | 0.813397 | +0.014174 | [-0.030340, +0.055878] | 2.2967% | 0.0000% |

No B model has a positive 95% paired mean-hit interval versus the fresh random baseline in this run. Point estimates for pair/triple are not treated as validated superiority.

## Model status

- A integrated source: NOT RECOVERED / NOT EXECUTED.
- C integrated source: NOT RECOVERED / NOT EXECUTED.
- Contrarian integrated source: NOT RECOVERED / NOT EXECUTED.
- B: EXECUTED.
- Random baseline: EXECUTED.
- Pair/triple: EXECUTED.

This record is additive and does not overwrite earlier 2026-10-16 partial output.
