# E059 - E054 candidate-stage decomposition

Study status: FAIL. Historical diagnostic only; no candidate model is promoted.

## Frozen scope
- Cutoff 1250; targets 401-1250 (850).
- Frozen E054 rolling-HHI regime score, no model or weight changes.
- Candidate sets TOP10/15/20/25/30 measured before ticket allocation.
- Exact random candidate baseline: expected recall K/45.
- Stable baseline: recent30 frequency, computed from the prior 30 main draws.
- 10 Bonferroni comparisons; alpha per comparison 0.005; 4,000 moving-block bootstrap replicates; 50-target blocks.

## Candidate recall
- TOP10: E054 recall 21.667%, random 22.222%, delta -0.556 percentage points; adjusted CI [-2.183, 0.699] pp; recent30 22.020%.
- TOP15: E054 recall 32.569%, random 33.333%, delta -0.765 percentage points; adjusted CI [-2.549, 0.569] pp; recent30 33.118%.
- TOP20: E054 recall 43.059%, random 44.444%, delta -1.386 percentage points; adjusted CI [-3.190, 0.261] pp; recent30 44.176%.
- TOP25: E054 recall 54.902%, random 55.556%, delta -0.654 percentage points; adjusted CI [-2.654, 0.797] pp; recent30 54.863%.
- TOP30: E054 recall 66.039%, random 66.667%, delta -0.627 percentage points; adjusted CI [-2.451, 1.176] pp; recent30 66.294%.

## Reproduction and attribution
- E054 score hash matches: 850/850.
- Regime, current HHI, threshold HHI, reference-window count, and exposure matches: regime 850/850; current_hhi 850/850; threshold_hhi 850/850; reference_count 850/850; exposure 850/850.
- Winner trace rows: 5100; each row records the E054 rank/score, regime successes/exposure, recent30 rank, and margin to each K cutoff.
- 1244-1249 are previously inspected live-history material, not clean holdout data.

## Interpretation
This separates E054 candidate ranking from the downstream three-line allocator. It does not change E054, the strict gate, or prospective confirmation rules. Any apparent historical candidate-recall difference is diagnostic and cannot authorize purchase lines.

No final purchase lines, candidate recommendation, strict-ready artifact, freeze, or seal were generated.
