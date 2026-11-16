# E063 — Previous-draw last-digit occupancy transition

Execution status: **COMPLETE / VERIFICATION PASS**
Historical strict gate: **FAIL**

## Frozen design
- One last-digit occupancy transition feature family; candidate number n is conditioned on the count of previous-draw main numbers sharing n mod 10.
- One fixed shrinkage estimator with prior strength 45; one deterministic E045 disjoint-line selector; no variants or parameter search.
- Targets 401–1250; each target uses only draws through t-1.
- 120 jointly permuted, geometry-matched random portfolios per target; 4,000 moving-block bootstrap replicates; 50-target blocks.

## Results
- max_hits: observed=1.550588, random=1.512520, delta=0.038069, adjusted CI=[-0.012559, 0.079588]
- any2: observed=0.500000, random=0.474118, delta=0.025882, adjusted CI=[-0.010382, 0.050941]
- any3: observed=0.077647, random=0.070196, delta=0.007451, adjusted CI=[-0.013255, 0.024608]
- winning_union_coverage: observed=2.423529, random=2.401990, delta=0.021539, adjusted CI=[-0.036931, 0.094333]
- Positive any2 blocks: 11/17 (64.71%); required: 65%.

## Interpretation and guardrails
- This is a new feature-family test on an already observed historical sample, not an independent prospective sample.
- Even a historical gate PASS cannot create STRICT_PASS_READY because the policy still requires a separately specified prospective confirmation rule.
- No purchase lines, candidate lines, freeze, or seal were generated.
- No strict threshold, alpha, block length, comparator, or purchase policy was changed.
