# E069 corrective re-execution — fixed 6/45 prior

Classification: historical corrective re-execution; not an independent research axis; not prospective confirmation.

The original E069 runner did not conform to its frozen prior. E070 documented the mismatch. This separately versioned re-execution preserves the original E069 files and applies only the preregistered fixed 6/45 prior with strength 45.

## Frozen design
- Data cutoff: 1250; targets: 401–1250 (850 targets).
- Estimator: (success + 45*(6/45)) / (exposure + 45).
- Random comparator: 120 geometry-matched label permutations per target; total 102,000.
- Moving-block bootstrap: 4,000 replicates; block length 50; per-metric alpha 0.0125.
- The E045 selector and exact three disjoint six-number / union18 geometry are unchanged.
- No parameter search, variants, threshold changes, or purchase output.

## Results
- max_hits: observed=1.496471, random=1.515078, delta=-0.018608, adjusted CI=[-0.075324, 0.046941]
- any2: observed=0.460000, random=0.475824, delta=-0.015824, adjusted CI=[-0.061696, 0.035598]
- any3: observed=0.072941, random=0.072029, delta=0.000912, adjusted CI=[-0.017029, 0.017480]
- winning_union_coverage: observed=2.363529, random=2.393882, delta=-0.030353, adjusted CI=[-0.121912, 0.065461]
- Positive any2 blocks: 4/17 (23.53%); required: 65%.
- Historical strict gate: FAIL.

## Guardrails
- This is a corrective re-execution of the same frozen hypothesis, not a new independent research axis.
- Historical evidence cannot create STRICT_PASS_READY; prospective confirmation remains unspecified in policy.
- Original E069 artifacts remain unchanged and are not treated as evidence for the registered fixed-prior estimator.
- No purchase lines, random fallback, freeze, or seal were generated.
