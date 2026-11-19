# A/C/Contrarian functional reconstruction v1

Executable successors reconstructed from recovered historical concepts plus surviving exact lineage. Not presented as byte-identical legacy source.

## Walk-forward results

| Model / window | N | Mean hits | Delta vs 0.8 | 95% moving-block CI | 2+ | 3+ | 4+ |
|---|---:|---:|---:|---:|---:|---:|---:|
| A_REBUILT_v1 201-1245 | 1045 | 0.792344 | -0.007656 | [-0.046890, +0.035407] | 17.1292% | 2.7751% | 0.2871% |
| A_REBUILT_v1 401-1245 | 845 | 0.802367 | +0.002367 | [-0.042604, +0.050888] | 18.2249% | 3.1953% | 0.2367% |
| C_REBUILT_v1 401-1245 | 845 | 0.781065 | -0.018935 | [-0.078107, +0.040237] | 16.6864% | 2.4852% | 0.2367% |
| CONTRARIAN_REBUILT_v1 201-1245 | 1045 | 0.802871 | +0.002871 | [-0.045933, +0.046890] | 17.4163% | 2.2010% | 0.0957% |
| CONTRARIAN_REBUILT_v1 401-1245 | 845 | 0.815385 | +0.015385 | [-0.034320, +0.066272] | 17.6331% | 2.1302% | 0.1183% |

## Leakage checks
- Every target t uses draw data only through t-1.
- C model selection uses only component hit records strictly before t.
- State is updated with target actual only after all target forecasts are written.
- No 1246 candidate/final line is generated.

## Reconstruction boundaries
- A historical 35/25/20/20 weights are preserved exactly. Missing legacy scale normalization is explicitly reconstructed with rank normalization.
- C historical principle is operationalized as nested repeated validation; no historical numeric C weights were invented.
- Contrarian historical atypical-structure role is operationalized as a fixed-bank structural-surprisal model.

## Determinism
The reconstruction was executed twice against rounds 1..1245. The output manifest matched byte-for-byte across the two independent runs.

## Current interpretation
No rebuilt model has a 95% moving-block mean-hit interval strictly above the exact uniform-random mean of 0.8. These results establish reproducible restored functionality, not validated predictive superiority.
