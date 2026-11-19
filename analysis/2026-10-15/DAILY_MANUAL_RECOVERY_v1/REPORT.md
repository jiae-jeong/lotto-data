# Daily manual recovery research — 2026-10-15

Status: PARTIAL MASTER / ACTUAL COMPUTATION COMPLETED. This run was started manually after the scheduled `daily-lotto-research-v2` workflow failed before research execution with `ValueError: Unregistered/unsafe research task`. No recommendation, candidate, or weekly final ticket was generated.

## 1. Data basis / validation

- Cutoff: round 1245, draw date 2026-10-10.
- Rows: 1,245; rounds 1..1245 continuous; duplicate rounds 0.
- Main-number count/range/duplicate failures: 0/0/0.
- Bonus range/main-overlap failures: 0/0.
- Input SHA-256: `e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4`.
- Official and independent external sources were checked before execution; no later draw exists at the 2026-10-15 morning cutoff.

## 2. What was newly executed today

1. Recomputed 1..45 full-history frequencies, gap statistics, rolling 50/100/200 trends, and full vs recent 10/30/50/100 comparisons from all 1,245 rows.
2. Recomputed full and recent structural summaries: odd/even, low/high, sums, consecutive adjacency/run, repeated endings, inter-number gaps/clusters, previous-draw overlap, and range concentration.
3. Recomputed all 990 pairs and all 14,190 triples, including recent 10/30/50/100 counts and full-history binomial tests with BH correction. BH q<0.05 survivors: pair 0; triple 0.
4. Re-executed the frozen E020 B source on the same validated input. It produced 33,480 prediction records, 8,360 unique target-model predictions, 1,045 target rounds (201..1245), and leakage failures 0.
5. Re-execution was semantically identical row-for-row to E020 for predictions, holdout metrics, classification, and 50-round trends. Byte hashes differ because of serialization/line-ending details and the local path-patched execution copy; semantic CSV equality was explicitly checked.
6. Generated 1,000 new uniform random tickets for every one of the same 1,045 target rounds using seed `20261015`: 1,045,000 tickets total. Random mean hits = 0.8017244019.
7. Compared each B component/model with same-target random means using a 20-target circular moving-block bootstrap, 4,000 replicates.
8. Recomputed early/middle/late temporal performance and tested early vs late mean-hit differences; BH correction was applied across the eight B models.

## 3. Full cumulative / long-vs-recent summary

Across the 45 numbers, full-history counts ranged from 137 to 187 (mean 166.0, population SD 10.3966). Current nonappearance ranged from 0 to 21 rounds, median 4. Historical maximum gaps across number histories ranged from 27 to 73; the mean of each number's completed-gap mean was 6.4916 rounds.

Using a fixed quartile rule (long strong >= full-history 75th percentile; long weak <= 25th percentile; recent strong/weak defined analogously within each window), long-strong/recent-weak vs long-weak/recent-strong counts were: 10-window 8 vs 3; 30-window 8 vs 4; 50-window 6 vs 2; 100-window 4 vs 2. These are descriptive categories only and are not recommendation rules.

## 4. Structure / relation

Full-history structural means/rates: sum mean 138.2763 (SD 30.6531), odd-count mean 3.0683, low(1..22) count mean 2.9430, at least one consecutive adjacency 51.73%, repeated ending present 78.15%, previous-draw overlap mean 0.8264, at least three numbers in one fixed range bucket 43.61%, mean minimum sorted gap 1.8056, mean maximum sorted gap 14.1092.

Recent 10/30/50/100 structure summaries were recomputed today and preserved in the run manifest/report inputs. Pair universe = 990; triple universe = 14,190. After BH correction on the full-history relation families, pair q<0.05 = 0 and triple q<0.05 = 0.

## 5. A model

Integrated authoritative legacy A definition was not recovered in today's source review. The long-frequency, gap, recent-change, structure, pair and triple signal inventories were actually recalculated, but they are not represented as an integrated A execution. Status: PARTIAL / A NOT EXECUTED.

## 6. B model — actual rerun + fresh random baseline

Same-target random mean = 0.8017244019.

| Model | Mean hits | Delta vs fresh random | 95% moving-block CI for delta | 3+ | 4+ |
|---|---:|---:|---:|---:|---:|
| combined_equal_rank | 0.763636 | -0.038088 | [-0.081351, 0.007316] | 1.5311% | 0.2871% |
| current_gap | 0.795215 | -0.006509 | [-0.054895, 0.040572] | 1.4354% | 0.0000% |
| frequency_plus_gap | 0.796172 | -0.005552 | [-0.050755, 0.041567] | 2.0096% | 0.1914% |
| long_frequency | 0.782775 | -0.018949 | [-0.065250, 0.028856] | 2.7751% | 0.1914% |
| pair_association | 0.805742 | +0.004017 | [-0.040081, 0.050702] | 1.3397% | 0.0000% |
| recent_momentum | 0.762679 | -0.039045 | [-0.087508, 0.008944] | 1.3397% | 0.0000% |
| structure_profile | 0.794258 | -0.007466 | [-0.059471, 0.045068] | 2.5837% | 0.0957% |
| triple_association | 0.813397 | +0.011673 | [-0.034104, 0.053830] | 2.2967% | 0.0000% |

No model has a positive 95% paired mean-hit CI against today's fresh random baseline. Therefore pair/triple point-estimate uplifts are not treated as validated superiority.

### Temporal stability finding

Early targets 201..548 vs late targets 897..1245 were compared with Welch tests; BH correction covers all eight B models.

- `recent_momentum`: 0.864943 -> 0.667622, delta -0.197321, raw p=0.0004327, BH q=0.0034614.
- `structure_profile`: 0.916667 -> 0.765043, delta -0.151624, raw p=0.0135161, BH q=0.0540644.
- All other models: BH q >= 0.7852 for the early-late mean comparison.

This is retrospective temporal-instability evidence, not permission to retune the weekly model today.

## 7. C model

No authoritative integrated C definition was recovered/executed today. Later repository research already records that no candidate family passed every registered predictability/promotion test. Status: C NOT EXECUTED / no new signal promoted.

## 8. Contrarian

Non-typical structures were recalculated descriptively instead of being filtered out. No authoritative integrated contrarian model was recovered/executed. Status: descriptive validation only.

## 9. Error-note closed loop

No new draw occurred after round 1245, so there is no new outcome to close today. Current repository prospective evidence still records zero independently verified actual purchase records. The pre-draw sealed historical material remains separated from authenticated purchase evidence. No post-outcome rationale was reconstructed.

## 10. Hypotheses registered today — NOT ADOPTED

- `H_B_MOMENTUM_DRIFT_001`: recent-momentum performance may be temporally unstable enough to dilute a static equal-rank combination. Motivation: corrected early-vs-late degradation. Required next evidence: frozen future/out-of-sample confirmation; no weight change now.
- `H_B_RELATION_COLLAPSE_001`: the standalone pair/triple greedy set constructors and the combined model's per-number node-rank collapse may preserve different relational information. This is source-code/mechanism motivation only; no performance advantage is claimed. Required next evidence: preregistered ablation/representation test on untouched evidence; no recommendation use now.

## 11. Automation incident

The scheduled 2026-10-15 run started at about 09:21 KST. Environment validation and unit tests passed, but the study step failed before executing a research task because `daily_research_v2.py` validates every queue entry before checking which studies are already completed. Older completed queue entries beginning at E030 do not satisfy the stricter current top-level/spec validator contract, producing `ValueError: Unregistered/unsafe research task`.

This incident is separate from the manual calculations above. The automation should be repaired without rewriting or retroactively changing completed research specifications.

## 12. Forced checklist

- Full raw dataset: PASS
- Latest round/source cross-check: PASS
- Full data validation: PASS
- Full number statistics recalculated today: PASS
- Long vs recent 10/30/50/100: PASS
- Gap/nonappearance: PASS
- Structure: PASS
- Pair/triple: PASS
- Integrated A execution: PARTIAL / source not recovered
- B rolling walk-forward rerun today: PASS
- Fresh uniform random baseline today: PASS (1,045,000 tickets)
- Leakage check: PASS (0 failures)
- C integrated execution: PARTIAL / source not recovered
- Contrarian integrated execution: PARTIAL / source not recovered
- Error-note source review: PASS; no new outcome to close
- Model/signal scorecard: PASS for B; unavailable for missing legacy integrated A/C/contrarian
- New hypotheses: PASS, registered as NOT ADOPTED
- Version preservation: PASS; this report is a new dated recovery record and does not overwrite prior outputs

This is not labeled FULL MASTER COMPLETE because authoritative A/C/contrarian integrated sources remain unavailable and the scheduled automation itself failed before research execution.