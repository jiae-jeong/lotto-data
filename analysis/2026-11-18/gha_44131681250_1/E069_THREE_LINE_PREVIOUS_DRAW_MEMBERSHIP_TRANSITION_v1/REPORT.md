# E069 — Previous-draw membership transition

Execution status: **COMPLETE / VERIFICATION PASS**
Historical strict gate: **FAIL**

## Frozen design
- One lag-one candidate-membership transition feature family; candidate n is conditioned only on whether it appeared in the immediately preceding draw.
- One fixed shrinkage estimator with prior strength 45; one deterministic E045 disjoint-line selector; no variants or parameter search.
- Targets 401–1250; each target uses only draws through t-1.
- 120 jointly permuted, geometry-matched random portfolios per target; 4,000 moving-block bootstrap replicates; 50-target blocks.

## Results
- max_hits: observed=1.490588, random=1.514588, delta=-0.024000, adjusted CI=[-0.072775, 0.024627]
- any2: observed=0.462353, random=0.475069, delta=-0.012716, adjusted CI=[-0.055196, 0.023422]
- any3: observed=0.067059, random=0.072078, delta=-0.005020, adjusted CI=[-0.026657, 0.017637]
- winning_union_coverage: observed=2.363529, random=2.395157, delta=-0.031627, adjusted CI=[-0.117735, 0.056647]
- Positive any2 blocks: 7/17 (41.18%); required: 65%.

## Interpretation and guardrails
- This is a new feature-family test on an already observed historical sample, not an independent prospective sample.
- Even a historical gate PASS cannot create STRICT_PASS_READY because the policy still requires a separately specified prospective confirmation rule.
- No purchase lines, candidate lines, freeze, or seal were generated.
- No strict threshold, alpha, block length, comparator, or purchase policy was changed.
