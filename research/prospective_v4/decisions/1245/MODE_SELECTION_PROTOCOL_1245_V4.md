# Fixed protocol: choose one already sealed V4 mode for draw 1245

Decision is registered now using historical data only. It does not amend V4 models, seeds, portfolio rules or future holdout evaluation. No target1245 outcome is accessed. Existing six lines are immutable; only one entire mode's three rows may be copied.

## Identical targets and strict cutoff
Targets are exactly 1045..1244 inclusive (200), with no exclusions. Expanding trains1..t-1; rolling300 trains t-300..t-1. Any integrity/run failure aborts rather than drops a bad target. Evaluation reads each historical actual only for targets<=1244. Frozen fit/candidates/portfolio functions are called without modification; the future-only predict API and fixed initial-prefix loader are not altered to manufacture retrospective predictions.

## Random three-line comparison
10000 portfolios per historical target; 2000000 total, 6000000 tickets. New analysis-only master seed2026100904; target seed is SHA256(seed|historical_target|t) first8 big-endian. NumPy PCG64 version is pinned in config. Uniform ticket draws use six smallest random ranks among45. Unique ordered candidate prefixes per G/C/S list, max37, feed the frozen greedy distinctness/overlap<=2/fallback rule. Unneeded candidate suffixes cannot affect a selected highest acceptable prefix. If all37 fail, exact frozen fallback applies. Candidate generation has no outcome input. Single-ticket exact PMF=C(6,k)C(39,6-k)/C(45,6), expectation0.8; portfolio tail probabilities estimated by matched simulation, not independent-line assumptions.

## Metrics and priorities
All600 tickets per mode: mean, 0..6 histogram, 2+/3+/4+ rates. Every target: maximum of3 line hits and portfolio3+/4+ indicators. Compare both paired modes and random. Four nonoverlapping50 blocks; last50/100/200 are descriptive overlapping windows, never independent confirmations. G/C/S hit contributions and overlap/union correlations are diagnostic, not selection features.

## Paired uncertainty and tests
Shared target resampling keeps both mode results paired. Circular moving-block bootstrap length10,20000 replicates seed2026100905; report individual-mode and paired difference95% intervals. Nonoverlapping10-target block sign flip,50000 replicates seed2026100906, two-sided add-one p, Holm across four prespecified endpoints: portfolio3+,portfolio4+,maxhits,meanhits. Exact McNemar for3+/4+ is secondary. Report paired standardized effect dz. Dependence, small rare-event counts and reused development data limit interpretation; no prospective validation is claimed.

## Sufficient historical support gate
For one direction require positive paired3+,4+,mean differences, each Holm p<.05, each bootstrap CI strictly in that direction; maxhits nonnegative. Overall3+/4+/mean above random and all four blocks nonnegative against random3+/exact0.8 mean and other-mode3+/mean. This intentionally conservative gate avoids choosing on one attractive metric. Passing means historical comparative support only, not verified future prediction superiority.

## Required deterministic tie-break when support is insufficient
1 Higher200-target portfolio3+ count.
2 If tied, higher sum of target portfolio max hits.
3 If tied, higher600-ticket mean hits.
4 If tied, lower population variance of four50-block portfolio3+ rates, computed as (4*sum(count_i^2)-sum(count_i)^2)/40000.
5 If still tied, expanding.
Tie-break implies no predictive superiority. No aesthetics, structure, mixed lines, extra targets, alternate seeds or retrospective thresholds may override it.

## Freeze and outputs
Before comparison, config/protocol and both execution source files are SHA-bound in MODE_SELECTION_PRERUN_LOCK. Check those hashes before and after the run and log the UTC lock. Any selection criteria change requires a new decision version, preserving this one. Commit only new decisions/1245 artifacts after verifier PASS. Root seal self hash and publishing commit are recorded externally to avoid circular reference. V3 remains SEALED V3 GATE NOT PASSED; V4 prospective models remain REGISTERED_UNEVALUATED.
