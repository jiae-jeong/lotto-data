# E046 — Three-line prospective confirmation design planning

**Classification: DESIGN ONLY — NOT MODEL EVIDENCE, NOT STRICT PASS.**

- Frozen source: E045, cutoff 1249, targets 401–1249 (849 targets)
- E045 manifest entries independently verified: 8/8
- Historical source prefix SHA256 rechecked: a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7
- No future outcomes, model tuning, ticket generation, or threshold changes.

## Historical block-level variance used for planning

| Metric | Historical paired-difference mean (diagnostic only) | SD of 50-target block means |
|---|---:|---:|
| max_hits | -0.021912 | 0.105617 |
| any2 | -0.007367 | 0.061432 |
| any3 | -0.012462 | 0.042608 |
| winning_union_coverage | -0.017197 | 0.168540 |

## Prospective design grid

The grid applies hypothetical positive shifts of 0.25, 0.5, 0.75, and 1.0 historical block SD. It uses the frozen 0.0125 per-metric alpha, a normal-theory lower-CI approximation, 50-target blocks, and retains a final remainder block.

| Targets | Blocks (incl. remainder) | Effect d | Any2 block-share gate probability | Joint power (independence approx.) | Conservative joint lower bound |
|---:|---:|---:|---:|---:|---:|
| 100 | 2 (50) | 0.25 | 0.3584 | 0.0000 | 0.0000 |
| 100 | 2 (50) | 0.50 | 0.4781 | 0.0000 | 0.0000 |
| 100 | 2 (50) | 0.75 | 0.5981 | 0.0000 | 0.0000 |
| 100 | 2 (50) | 1.00 | 0.7079 | 0.0003 | 0.0000 |
| 125 | 3 (25) | 0.25 | 0.6461 | 0.0000 | 0.0000 |
| 125 | 3 (25) | 0.50 | 0.7732 | 0.0000 | 0.0000 |
| 125 | 3 (25) | 0.75 | 0.8692 | 0.0001 | 0.0000 |
| 125 | 3 (25) | 1.00 | 0.9325 | 0.0016 | 0.0000 |
| 150 | 3 (50) | 0.25 | 0.6461 | 0.0000 | 0.0000 |
| 150 | 3 (50) | 0.50 | 0.7732 | 0.0000 | 0.0000 |
| 150 | 3 (50) | 0.75 | 0.8692 | 0.0002 | 0.0000 |
| 150 | 3 (50) | 1.00 | 0.9325 | 0.0023 | 0.0000 |
| 175 | 4 (25) | 0.25 | 0.4730 | 0.0000 | 0.0000 |
| 175 | 4 (25) | 0.50 | 0.6366 | 0.0000 | 0.0000 |
| 175 | 4 (25) | 0.75 | 0.7770 | 0.0004 | 0.0000 |
| 175 | 4 (25) | 1.00 | 0.8790 | 0.0061 | 0.0000 |
| 200 | 4 (50) | 0.25 | 0.4730 | 0.0000 | 0.0000 |
| 200 | 4 (50) | 0.50 | 0.6366 | 0.0000 | 0.0000 |
| 200 | 4 (50) | 0.75 | 0.7770 | 0.0005 | 0.0000 |
| 200 | 4 (50) | 1.00 | 0.8790 | 0.0080 | 0.0000 |
| 250 | 5 (50) | 0.25 | 0.3347 | 0.0000 | 0.0000 |
| 250 | 5 (50) | 0.50 | 0.5107 | 0.0000 | 0.0000 |
| 250 | 5 (50) | 0.75 | 0.6820 | 0.0012 | 0.0000 |
| 250 | 5 (50) | 1.00 | 0.8191 | 0.0203 | 0.0000 |
| 300 | 6 (50) | 0.25 | 0.5416 | 0.0000 | 0.0000 |
| 300 | 6 (50) | 0.50 | 0.7283 | 0.0001 | 0.0000 |
| 300 | 6 (50) | 0.75 | 0.8657 | 0.0036 | 0.0000 |
| 300 | 6 (50) | 1.00 | 0.9452 | 0.0505 | 0.0000 |
| 400 | 8 (50) | 0.25 | 0.3127 | 0.0000 | 0.0000 |
| 400 | 8 (50) | 0.50 | 0.5301 | 0.0002 | 0.0000 |
| 400 | 8 (50) | 0.75 | 0.7357 | 0.0115 | 0.0000 |
| 400 | 8 (50) | 1.00 | 0.8798 | 0.1382 | 0.0000 |
| 500 | 10 (50) | 0.25 | 0.3790 | 0.0000 | 0.0000 |
| 500 | 10 (50) | 0.50 | 0.6267 | 0.0007 | 0.0000 |
| 500 | 10 (50) | 0.75 | 0.8277 | 0.0339 | 0.0000 |
| 500 | 10 (50) | 1.00 | 0.9403 | 0.2925 | 0.0000 |
| 600 | 12 (50) | 0.25 | 0.4345 | 0.0000 | 0.0000 |
| 600 | 12 (50) | 0.50 | 0.7008 | 0.0017 | 0.0000 |
| 600 | 12 (50) | 0.75 | 0.8867 | 0.0754 | 0.0000 |
| 600 | 12 (50) | 1.00 | 0.9701 | 0.4672 | 0.3024 |
| 800 | 16 (50) | 0.25 | 0.3250 | 0.0000 | 0.0000 |
| 800 | 16 (50) | 0.50 | 0.6314 | 0.0058 | 0.0000 |
| 800 | 16 (50) | 0.75 | 0.8670 | 0.1991 | 0.0000 |
| 800 | 16 (50) | 1.00 | 0.9696 | 0.7363 | 0.7036 |
| 1000 | 20 (50) | 0.25 | 0.4113 | 0.0000 | 0.0000 |
| 1000 | 20 (50) | 0.50 | 0.7456 | 0.0185 | 0.0000 |
| 1000 | 20 (50) | 0.75 | 0.9374 | 0.3919 | 0.1539 |
| 1000 | 20 (50) | 1.00 | 0.9916 | 0.8992 | 0.8950 |

## First grid point reaching 80%

| Standardized effect d | Independence approximation | Conservative union-bound lower estimate |
|---:|---:|---:|
| 0.25 | Not reached in grid | Not reached in grid |
| 0.50 | Not reached in grid | Not reached in grid |
| 0.75 | Not reached in grid | Not reached in grid |
| 1.00 | 1000 | 1000 |

## Interpretation and limits

This analysis quantifies how demanding the fixed prospective confirmation gate may be under hypothetical standardized effects. It does not identify a model, prove a predictive edge, satisfy prospective confirmation, create STRICT_PASS_READY, or alter the policy. The operational gate still requires the actual preregistered moving-block bootstrap and all four lower bounds strictly above zero plus the 0.65 block-stability threshold.

The prospective minimum target count and completion rule remain unspecified in the governing policy. This report is evidence for a later protocol decision only; it does not adopt a new rule.
