# E064 — Block-persistent non-predictive portfolio null calibration

Execution status: **COMPLETE / VERIFICATION PASS**

## Frozen design
- One uniformly random disjoint three-line union18 portfolio is held fixed for each non-overlapping 50-target block.
- At each 50-target boundary, a new independent uniform ordered partition is drawn from a seeded PRNG.
- Portfolio generation never reads target outcomes; outcomes are read only after the block portfolio is fixed.
- Targets 401–1250; 1,000 trajectories; 17 portfolios per trajectory; 17,000 generated portfolios total.
- The unchanged strict gate uses four exact-null comparisons, 4,000 moving-block bootstrap replicates, 50-target blocks, and the existing 65% positive-any2-block rule.

## Results
- max_hits: empirical mean=1.513996, exact null=1.514256, delta=-0.000260, trajectory MCSE=0.000750
- any2: empirical mean=0.474825, exact null=0.474976, delta=-0.000152, trajectory MCSE=0.000539
- any3: empirical mean=0.071274, exact null=0.071355, delta=-0.000081, trajectory MCSE=0.000284
- winning_union_coverage: empirical mean=2.398778, exact null=2.400000, delta=-0.001222, trajectory MCSE=0.001257
- Joint strict-gate false passes: **0/1000 (0.00%)**.
- 95% Wilson interval: [0.0000%, 0.3827%].
- Mean lag-1 autocorrelation of any2: -0.002566.
- Mean adjacent-block union overlap: 7.207 numbers; corresponding-line overlap: 0.803 per line.

## Interpretation
This is a gate-calibration stress test under one piecewise-constant, block-persistent random portfolio mechanism. It is not a predictive model, does not test a new signal, and cannot create STRICT_PASS_READY or purchase eligibility.
The strict gate, alpha, block length, comparator, and purchase policy were not changed.

No candidate numbers, purchase lines, freeze, or seal were generated.
