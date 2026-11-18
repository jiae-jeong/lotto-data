# E071 — Previous-draw bonus-distance transition

Execution status: **COMPLETE / VERIFICATION PASS**
Historical strict gate: **FAIL**

## Frozen design
- One candidate-number distance feature relative only to the immediately preceding draw's bonus ball; the previous six main numbers are not used as features.
- Five bins are fixed by theoretical quintiles of all 45×45 ordered candidate/bonus pairs: 0–5, 6–10, 11–17, 18–25, 26–44.
- One fixed uniform 6/45 prior with strength 45; one unchanged E045 three-line disjoint selector; no variants or parameter search.
- Targets 401–1250; each target uses only the previous draw's bonus and outcome history through t−1.
- 120 jointly permuted geometry-matched random portfolios per target; 4,000 moving-block bootstrap replicates; 50-target blocks.

## Results
- max_hits: observed=1.487059, random=1.512206, delta=-0.025147, adjusted CI=[-0.061216, 0.014343]
- any2: observed=0.463529, random=0.473569, delta=-0.010039, adjusted CI=[-0.035529, 0.018108]
- any3: observed=0.063529, random=0.070608, delta=-0.007078, adjusted CI=[-0.025941, 0.009422]
- winning_union_coverage: observed=2.311765, random=2.397333, delta=-0.085569, adjusted CI=[-0.169010, 0.007510]
- Positive any2 blocks: 10/17 (58.82%); required: 65%.
- Failed historical gates: max_hits, any2, any3, winning_union_coverage, any2_positive_50_target_block_share.

## Interpretation and guardrails
- This is a distinct feature-family test on an already observed historical sample, not an independent prospective sample.
- E048 tests exact previous-bonus identity; E050 tests distance to the previous draw's six main numbers. E071 tests distance to the previous draw's bonus ball only.
- Even a historical gate PASS cannot create STRICT_PASS_READY because the policy still requires a separately specified prospective confirmation rule.
- No purchase lines, candidate lines, random fallback, freeze, or seal were generated.
- No strict threshold, alpha, block length, comparator, or purchase policy was changed.
