# Daily Lotto study — 2026-10-12

## 1. Data / execution
- Repository raw file verified: rounds 1..1244; original was not overwritten.
- Round 1245 was appended only to today's versioned snapshot after external two-source verification.
- Analysis snapshot rows: 1245; continuity=True; duplicate rounds=0; six unique main=True; main range=True; bonus separation=True.

## 2. Actually recalculated today
- Full 1..45 cumulative counts/rates, current/max gaps, average intervals, and 10/30/50/100 deltas: `NUMBER_STATS_1245.csv`.
- Structure, pair/triple concentration, contrarian incidence: recalculated on 1..1245.
- H001/H002 cutoff-safe walk-forward: rerun on targets 201..1245.
- Uniform random baseline: actually simulated 2,090,000 ticket-vs-draw comparisons with seed 20261012.
- B model: actual rerun from the preserved executable B source on the 1..1245 snapshot; returncode=0; prediction rows=33480; leakage invariant=True; target-1245 rows=72.

## 3. New factual findings
- H002 due-only mean=0.795215, 2+=16.7464%, 3+=1.4354%.
- H002 anti-due mean=0.819139, 2+=18.6603%, 3+=2.2967%.
- Numerically best H001 direction/window today was `H001_recent_over_long_30` mean=0.834450; this is not promoted without a stable random-beating result.
- Monte Carlo mean=0.800135, 2+=17.5078%, 3+=2.3698%; theoretical random mean=0.800000, 2+=17.5308%.
- Latest draw structure: odd/even=2:4, low/high=2:4, sum=136, consecutive-pair count=1, ending-repeat-excess=2, previous-overlap=0.
- Stored pre-draw purchase record review: lines=3, max hits=1, 2+ rate=0.0; no historical recommendation was reconstructed.

## 4. Relation / structure summary
- Pair top-10 share all=1.6546%, recent50=5.0667%; triple top-10 share all=0.3052%, recent50=2.1000%.
- Historical sum 5th/95th percentile thresholds=88.2/189.0.
- Contrarian latest flags: {"odd_extreme": false, "lowhigh_extreme": false, "consecutive_dense": false, "ending_repeat_dense": true, "sum_extreme": false}.

## 5. A / B / C status
- A: separable signal components were actually recomputed through B-compatible long-frequency/gap/recent/structure/pair/triple diagnostics. The exact legacy integrated A source is still not verified, so no invented A aggregate is reported.
- B: actual execution today. Detailed outputs saved beside this report.
- C/contrarian: structural incidence recalculated; no new unvalidated weighting was adopted.
- H005/S008 correction: NOT EXECUTED because no pre-frozen corrected mapping exists; inventing one after observing 1245 would violate the protocol.

## 6. Forced-check result
Today contains real new computations, not a state-only summary. However `legacy A integrated`, `legacy C integrated`, and `H005 corrected S008` remain unavailable/not executed, so this report does **not** label the entire MASTER checklist as fully complete.
