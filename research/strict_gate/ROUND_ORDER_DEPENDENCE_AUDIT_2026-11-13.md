# Round-order dependence audit — 2026-11-13

## Result

**No temporal-order signal detected.** The preregistered max-T family-wise permutation test across lags 1–10 returned adjusted Monte Carlo p = **0.4572** (9,999 permutations). The strongest lag was 2, with an unadjusted descriptive p = 0.0632; it does not survive the registered family-wise test.

## What was actually tested

- Source: `lotto_data.csv`, rounds 1–1249; 1,249 valid draws, six distinct main numbers per draw.
- Data SHA256: `a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7`
- Git blob SHA: `d012ac7f2395e70466f0c50b71b949515dea1def`
- For each lag 1–10, measured the mean number of main-number overlaps between a draw and the draw k rounds earlier.
- Conditional null: 9,999 uniform permutations of whole draw rows, preserving each draw's six-number set and full-history number totals.
- Seed: `2026111302`; preregistration was committed before the data evaluation.

## Lag results

| Lag | Observed mean overlap | Null mean | Absolute standardized departure | Descriptive unadjusted p |
|---:|---:|---:|---:|---:|
| 1 | 0.826923 | 0.798633 | 1.276 | 0.2113 |
| 2 | 0.840417 | 0.798350 | 1.888 | 0.0632 |
| 3 | 0.788122 | 0.798756 | 0.479 | 0.6399 |
| 4 | 0.767871 | 0.799066 | 1.409 | 0.1577 |
| 5 | 0.807878 | 0.798737 | 0.409 | 0.6999 |
| 6 | 0.775543 | 0.798859 | 1.041 | 0.3018 |
| 7 | 0.836554 | 0.798994 | 1.677 | 0.0973 |
| 8 | 0.814666 | 0.799303 | 0.690 | 0.4929 |
| 9 | 0.829839 | 0.799043 | 1.375 | 0.1704 |
| 10 | 0.761098 | 0.798966 | 1.695 | 0.0940 |

The independent-uniform reference expectation for a pair of draws is 0.8 shared main numbers. None of the predeclared lags produced a max-T family-wise result below 0.05.

## Model decision

Do **not** add a lag-overlap or recent-draw-recurrence feature to the prediction model on this evidence. The test did not find a repeatable temporal signal. This is a real model-development decision: the proposed feature family is rejected for promotion rather than tuned until it looks predictive.

This result does not change the strict portfolio gate and does not create a strict PASS. It is retrospective and cannot establish that all possible forms of draw-process bias are absent. A new predictive feature must be supported by a separate preregistered test and then prospective confirmation.

## Reproduction

- Frozen protocol: `research/strict_gate/ROUND_ORDER_DEPENDENCE_PREREGISTRATION_2026-11-13.md`
- Reproduction code: `research/strict_gate/ROUND_ORDER_DEPENDENCE_AUDIT_2026-11-13.py`
- Machine-readable output: `research/strict_gate/ROUND_ORDER_DEPENDENCE_AUDIT_2026-11-13.json`
