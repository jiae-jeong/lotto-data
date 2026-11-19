# E062 — B-model trailing-performance selector

Status: **COMPLETE_DIAGNOSTIC_ONLY**

## Frozen design

- Targets 301–1250 (950); seven B component models.
- At target t, choose the component with the highest mean cached OOS hit count over t−100..t−1; lexicographic ascending model ID breaks ties.
- Compare with fixed combined_equal_rank and exact 6/45 random mean 0.8.
- 19 nonoverlapping 50-target blocks; 4,000 paired block-bootstrap replicates; family alpha 0.05 across two primary comparisons, giving 97.5% two-sided Bonferroni-adjusted intervals with nearest-rank quantiles 0.0125 and 0.9875.
- No parameter search, variant sweep, ticket generation, or purchase recommendation.

## Results

| Metric | Result |
|---|---:|
| Selector mean hits | 0.801053 |
| Fixed combined mean hits | 0.764211 |
| Exact random mean hits | 0.800000 |
| Selector minus fixed | 0.036842 |
| 97.5% Bonferroni-adjusted CI vs fixed | [-0.016842, 0.094737] |
| Selector minus random | 0.001053 |
| 97.5% Bonferroni-adjusted CI vs random | [-0.062105, 0.072632] |
| Selector 2+ rate | 17.789% |
| Selector 3+ rate | 1.474% |
| Selector 4+ rate | 0.105% |

Both adjusted confidence intervals include zero. No predictive advantage is confirmed.

## Selected model frequency

- current_gap: 200 targets
- frequency_plus_gap: 52 targets
- long_frequency: 131 targets
- pair_association: 247 targets
- recent_momentum: 133 targets
- structure_profile: 126 targets
- triple_association: 61 targets

Selection ties occurred on 77 targets; the preregistered lexicographic tie-break was applied.

## Integrity

- B cache: 8,400 rows, targets 201–1250, eight models per target.
- All training cutoffs equal target_round−1; selection uses only previous 100 realized outcomes.
- Canonical lotto_data.csv: 1–1250 continuous; SHA256 7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2.
- B cache SHA256: 0d0295e5288043e414637f7a7eb542aac4a31e2ae1dc66e598e754f7f5ecc3e8.
- Missing rows, duplicate rows, cutoff violations: zero.

## Conclusion

E062 is a historical single-ticket diagnostic only. It does not establish an edge over exact random or fixed combined_equal_rank, is not three-line purchase evidence, and cannot create STRICT_PASS_READY.
