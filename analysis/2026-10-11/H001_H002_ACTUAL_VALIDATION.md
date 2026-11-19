# H001 / H002 actual validation — 2026-10-11

## Execution scope
- Historical source: repository `lotto_data.csv`, rounds 1..1244.
- Round 1245 was independently cross-checked before this run against Donghaeng Lottery and independent published results: 2026-10-10, main 4,5,25,28,32,42; bonus 12.
- Historical evaluation targets: rounds 201..1245 (n=1,045). Every target uses only rounds 1..t-1.
- Existing `lotto_data.csv` was not overwritten.
- No candidate/final weekly numbers were generated.

## Data integrity
- Repository rows 1..1244: continuous, no duplicate rounds, six unique main numbers per round, all main numbers in 1..45.
- Round 1245 appended only in the analysis runtime after external cross-check; repository raw CSV remains unchanged.

## Random baseline
Exact hypergeometric baseline for a uniform 6-of-45 ticket:
- mean hits 0.800000000
- variance 0.614545455
- P(2+) 17.5308101%
- P(3+) 2.3834079%
- P(4+) 0.1393483%
- P(5+) 0.0028852%
- P(6) 0.00001228%

Matched Monte Carlo was also actually executed with fixed seed 20261011: 2,090,000 ticket-vs-draw comparisons (2,000 random tickets for each of 1,045 targets).
- mean 0.799411962
- variance 0.613996790
- 2+ 17.5222010%
- 3+ 2.3632057%
- 4+ 0.1409570%
- 5+ 0.0026794%
- 6 0 observed in 2,090,000 comparisons

## H002 — gap is not a due-number guarantee
Predefined cutoff-safe test used `current_wait` immediately before each target round.
- `due`: six numbers with largest current wait.
- `anti_due`: six numbers with smallest current wait.
- lower-number tie break only; no target information and no post-hoc tuning.

### Results
| rule | mean | variance | 2+ | 3+ | 4+ | 5+ | 6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| due | 0.795215311 | 0.555724211 | 16.7464% | 1.4354% | 0% | 0% | 0% |
| anti_due | 0.819138756 | 0.625303855 | 18.6603% | 2.2967% | 0.1914% | 0% | 0% |
| exact random | 0.800000000 | 0.614545455 | 17.5308% | 2.3834% | 0.1393% | 0.0029% | 0.000012% |

Hit distributions:
- due: 0=404, 1=466, 2=160, 3=15, 4=0, 5=0, 6=0.
- anti_due: 0=410, 1=440, 2=171, 3=22, 4=2, 5=0, 6=0.

Two-sided mean-vs-exact-random normal approximation: due p=0.8436; anti_due p=0.4300. In the joint H001/H002 family (10 tests), Holm-adjusted p=1.0 for both.

200-round temporal blocks show instability rather than a stable edge. Due mean hits by block: 0.765, 0.795, 0.850, 0.880, 0.655, then 0.933 on the short 45-round tail. Anti-due: 0.875, 0.795, 0.870, 0.745, 0.795, then 0.889 on the short tail.

**H002 result: supported only in the negative sense that a large gap is not evidence of a reliable due-number advantage. Gap-only selection did not establish predictive advantage over uniform random. Status: INSUFFICIENT EVIDENCE for recommendation use; due-number guarantee rejected.**

## H001 — long/recent direction conflicts
For each cutoff, full-history appearance rate was compared with recent 10/30/50/100-round rate. Two frozen directions were evaluated for each window:
- `recent_over_long`: six largest (recent rate - long rate).
- `long_over_recent`: six largest (long rate - recent rate).
No target information or post-hoc retuning was used.

| rule | mean | 2+ | 3+ | unadjusted two-sided p | Holm-adjusted p |
|---|---:|---:|---:|---:|---:|
| recent_over_long_10 | 0.825837321 | 18.3732% | 2.5837% | 0.2867 | 1.0 |
| long_over_recent_10 | 0.804784689 | 16.5550% | 2.3923% | 0.8436 | 1.0 |
| recent_over_long_30 | 0.834449761 | 19.6172% | 2.2967% | 0.1554 | 1.0 |
| long_over_recent_30 | 0.775119617 | 15.7895% | 2.0096% | 0.3049 | 1.0 |
| recent_over_long_50 | 0.790430622 | 17.7990% | 2.2967% | 0.6931 | 1.0 |
| long_over_recent_50 | 0.760765550 | 16.0766% | 2.5837% | 0.1057 | 1.0 |
| recent_over_long_100 | 0.811483254 | 17.1292% | 2.2967% | 0.6358 | 1.0 |
| long_over_recent_100 | 0.811483254 | 17.8947% | 2.8708% | 0.6358 | 1.0 |

The numerically best mean was recent-over-long at 30 rounds (0.83445), but it did not survive even the unadjusted test (p=0.1554), and every H001/H002 Holm-adjusted p-value was 1.0. Direction also changes by window; there is no stable monotonic long-vs-recent advantage.

**H001 result: INSUFFICIENT EVIDENCE. Do not promote a long/recent conflict rule into recommendations.**

## H005 / S008
H005 was reviewed but not falsely marked executed. The preserved source finding says S008 adds six positive structure-derived constant vectors, producing the same +270 term for every number column, so the structure term cannot alter relative number ordering. A valid corrected historical H005 test requires the original S005 bank/source or an explicitly frozen new replacement specification. That executable original is not available in the current repository evidence. Therefore:
- algebraic defect: VERIFIED from preserved source inspection;
- corrected S008 historical walk-forward: NOT EXECUTED;
- reason: required original S005 bank/source not available; inventing a replacement after seeing outcomes would violate the protocol.
- next action: register a separately named H005_FIX version only after freezing its structure-to-number mapping before evaluation.

## Decision
- H001: INSUFFICIENT EVIDENCE / PROHIBITED for recommendation use.
- H002: no due-number guarantee; gap-only predictive advantage NOT ESTABLISHED / PROHIBITED for recommendation use.
- H005: implementation defect VERIFIED; corrected predictive test NOT EXECUTED because the required original executable structure component is unavailable.
- No A/B/C weights were changed from these results.
- No 1245 result was leaked into historical cutoffs.
