# E058 — Persistent non-predictive portfolio null calibration

Study status: COMPLETE. This result applies only to the preregistered 50%-per-line-retention Markov null. It is not predictive evidence and does not create purchase readiness.

## Frozen design
- Cutoff 1250; targets 401-1250 (850).
- 1,000 independent trajectories; 850,000 portfolios.
- Each portfolio is exactly three disjoint six-number lines, union18.
- Each transition retains exactly 3/6 numbers in each corresponding line and replaces the other 9 numbers from outside the previous union18.
- Portfolio generation is independent of target outcomes. Outcomes are read only after each portfolio is generated, as fixed scoring labels.
- 4,000 moving-block bootstrap replicates per metric per trajectory; 50-target blocks; 17 blocks.
- Strict thresholds unchanged: family alpha 0.05, per-metric alpha 0.0125, all four lower bounds >0, any2-positive block share >=65%.

## Results
- Joint false passes: 0/1000 (0.00%).
- 95% Wilson interval: [0.0000%, 0.3827%].
- Mean lag-1 autocorrelation of any2 trajectory: -0.000733.
- Exact-null implementation inherited from E057 and frozen E045; no comparator or threshold changes.
- All geometry and transition checks passed; 10,000 self-test transitions passed.

## Interpretation
This result estimates the false-pass frequency for one deliberately persistent but outcome-independent portfolio process. It does not validate the gate for every dependent or adversarial null, and it does not establish any predictive edge. Compare the observed rate with E057's independent-portfolio null only descriptively; do not select a gate based on these historical simulations.

No candidate numbers, purchase lines, strict-ready artifact, freeze, or seal were generated. Prospective confirmation minimum count and completion rule remain unspecified. Historical rounds 1244-1249 remain contaminated/live-history diagnostics, not clean holdout data.
