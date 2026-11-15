# E059 - E054 candidate-stage decomposition (verified)

Status: PASS for deterministic reproduction and calculation integrity. Historical diagnostic only; no candidate model is promoted.

## Frozen scope
- Cutoff 1250; targets 401-1250 (850).
- Frozen E054 rolling-HHI regime score; no model or weight changes.
- Candidate TOP10/15/20/25/30 evaluated before ticket allocation.
- Exact random baseline: expected recall K/45.
- Stable baseline: recent30 frequency using only the 30 draws before each target.
- Ten paired comparisons; Bonferroni alpha 0.005 per comparison; 4,000 moving-block bootstrap replicates; 50-target blocks.

## Candidate recall
| K | E054 recall | Random expectation | Delta vs random | Adjusted CI (pp) | recent30 recall |
|---:|---:|---:|---:|---:|---:|
| 10 | 21.667% | 22.222% | -0.556 pp | [-2.183, 0.699] | 22.020% |
| 15 | 32.569% | 33.333% | -0.765 pp | [-2.549, 0.569] | 33.118% |
| 20 | 43.059% | 44.444% | -1.386 pp | [-3.190, 0.261] | 44.176% |
| 25 | 54.902% | 55.556% | -0.654 pp | [-2.654, 0.797] | 54.863% |
| 30 | 66.039% | 66.667% | -0.627 pp | [-2.451, 1.176] | 66.294% |

All five E054 point estimates are below exact random expectation; all five Bonferroni-adjusted intervals include zero. The E054-versus-recent30 adjusted intervals also include zero at every K. No stable candidate-stage advantage is demonstrated.

## Miss attribution
- 5,100 winner instances traced (six per target).
- TOP10 misses: 3,995; recent30 would retain 749 of those.
- TOP15 misses: 3,439; recent30 would retain 945 of those.
- TOP20 misses: 2,904; recent30 would retain 1,039 of those.
- TOP25 misses: 2,300; recent30 would retain 1,020 of those.
- TOP30 misses: 1,732; recent30 would retain 924 of those.

Each trace row records the E054 regime, winning number's posterior score and rank, regime-specific success/exposure, recent30 rank/count, and score gap to each K cutoff. This attributes exclusions to the single frozen E054 regime-posterior signal, without inventing additional factors.

## Reproduction
- Target sequence: 401-1250, 850/850.
- E054 score hashes: 850/850.
- Regime, current HHI, threshold HHI, reference count, exposure, and training-through-round checks: 850/850.
- The original false FAIL label was caused only by a summary-key check; the original record is preserved and corrected by the linked addendum.

## Interpretation
E054's candidate ranking does not explain away the portfolio failure: the candidate stage itself did not beat the exact random expectation or recent30 in this historical diagnostic. This is not a clean holdout result; rounds 1244-1249 remain contaminated/live-history. No candidate threshold is specified in the policy, so none is invented.

No candidate list, final purchase lines, strict-ready artifact, freeze, or seal was generated.
