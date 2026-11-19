# Draw-process bias preflight — 2026-11-13

## Question

Do number-specific frequency deviations in the first half of the available draw history persist into the second half, in a way that could support a pre-draw ranking signal?

## Actual calculation

- Data source: repository `lotto_data.csv`, rounds 1–1249 (cutoff 1249), Git blob SHA `d012ac7f2395e70466f0c50b71b949515dea1def`.
- Split: rounds 1–624 versus 625–1249.
- Statistic: Pearson correlation across the 45 numbers between first-half and second-half draw counts.
- Conditional null: 5,000 permutations of whole draw rows. This preserves each draw's six-number composition and the full-history total count of each number.
- Seed: `2026111301`.

| Result | Value |
|---|---:|
| Observed first/second-half frequency correlation | -0.299945 |
| Permutation null mean | -0.131255 |
| Permutation null SD | 0.107692 |
| One-sided permutation probability for positive persistence at least as large as observed | 0.947211 |

## Finding

This split provides **no evidence of positive persistent number-frequency bias**. The observed relationship is negative, and the upper-tail permutation probability for positive persistence is 0.9472. Thus, long-run frequency ranking does not gain support from this test as a stable predictive signal.

This is an exploratory diagnostic, not proof that every possible draw-process bias is absent. It does not meet the strict gate and does not promote any model.

## Immediate research direction change

- Stop trying to obtain strict PASS by rearranging 30 selected numbers across five disjoint lines.
- Retain only predictors whose information advantage can be demonstrated before each target and then replicated on a frozen future window.
- Next investigate independently defined draw-process regimes or serial structure only with preregistered tests, corrected multiplicity, and exact matched comparators.
- Do not optimize on the 1244–1249 exposed targets and call the result prospective.

The strict gate and all thresholds remain unchanged. No PASS is claimed.
