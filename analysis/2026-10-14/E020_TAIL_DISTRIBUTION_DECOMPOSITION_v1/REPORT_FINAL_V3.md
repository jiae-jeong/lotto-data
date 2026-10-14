# Daily lottery research — 2026-10-14

## 1. Data basis, acquisition, and validation

- NEW COMPUTATION: GitHub main commit `01333b4d90a0ea9dc350d1150c748dd51493465d` data copy; local `lotto_data.csv` remains unchanged and stops one draw earlier.
- Validated rows: 1245, rounds 1–1245; latest stored draw date 2026-10-10. No later draw result was available at the 2026-10-14 cutoff.
- Git-normalized CSV SHA-256: `e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4`; raw downloaded SHA-256: `e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4`. All schema, continuity, dates, main/bonus range, and duplicate checks passed.
- Independent cross-checks use official lottery results where available and independent result archives/news reports. See the six sample decisions in `DATA_SOURCE_CROSSCHECK.csv`; number values are deliberately not repeated here.
- Previous local canonical had 1,244 rows; latest GitHub snapshot adds one validated row.

## 2. New computation findings

- NEW STUDY E020: E013's full equal-vote vs structure-component removal changed the selected ticket on 164 of 645 retrospective target rows; paired mean-hit delta=0.02945736434108527; 3+ rate delta=0.009302325581395349. This is retrospective and does not select a better model.
- Frozen B was rerun on 1045 targets with 8 component/rank models; unique target/model predictions=8360 and leakage failures=0.
- Direct random comparison generated 1,045,000 explicit random tickets across the exact same targets; a separate 20,000-path MC estimates complete-path uncertainty.
- Pair/triple enumerations covered 990/14,190 theoretical combinations; BH q<0.05 counts were 0/0 (exploratory, dependent tests).

## 3–6. Frequency, windows, gaps, structures, pair and triple

NEW COMPUTATION: full and 10/30/50/100-window number rates, descriptive standardized differences, current and historical gap lengths, rolling 50/100/200 trends, and per-draw structural distributions were computed from all rows. Gap convention: current gap = latest round − last seen round; completed absent-round gap = interappearance distance − 1. Low/high is fixed at 1–22/23–45. See the CSV artifacts for full numeric detail.
Pair and triple expected counts use the uniform 6/45 per-draw inclusion probability. The full universes (990 pairs; 14,190 triples) are included, including never-observed triples. BH correction is applied separately by family; results are descriptive and dependence-aware caution is recorded.

## 7. A model

A DEFINITION NOT FOUND; A NOT EXECUTED. Descriptive signal inventories are not an integrated A model.

## 8. B walk-forward and random comparison

- `combined_equal_rank`: n=1045, mean=0.763636, variance=0.574754, 0..6=431,449,149,13,3,0,0, 2+/3+/4+/5+/6+=15.7895%/1.5311%/0.2871%/0.0000%/0.0000%; random path mean=0.800113; Δ mean=-0.036477.
- `current_gap`: n=1045, mean=0.795215, variance=0.555192, 0..6=404,466,160,15,0,0,0, 2+/3+/4+/5+/6+=16.7464%/1.4354%/0.0000%/0.0000%/0.0000%; random path mean=0.800113; Δ mean=-0.004898.
- `frequency_plus_gap`: n=1045, mean=0.796172, variance=0.615871, 0..6=425,431,168,19,2,0,0, 2+/3+/4+/5+/6+=18.0861%/2.0096%/0.1914%/0.0000%/0.0000%; random path mean=0.800113; Δ mean=-0.003941.
- `long_frequency`: n=1045, mean=0.782775, variance=0.637024, 0..6=438,427,151,27,2,0,0, 2+/3+/4+/5+/6+=17.2249%/2.7751%/0.1914%/0.0000%/0.0000%; random path mean=0.800113; Δ mean=-0.017338.
- `pair_association`: n=1045, mean=0.805742, variance=0.573747, 0..6=407,448,176,14,0,0,0, 2+/3+/4+/5+/6+=18.1818%/1.3397%/0.0000%/0.0000%/0.0000%; random path mean=0.800113; Δ mean=0.005628.
- `recent_momentum`: n=1045, mean=0.762679, variance=0.552291, 0..6=428,451,152,14,0,0,0, 2+/3+/4+/5+/6+=15.8852%/1.3397%/0.0000%/0.0000%/0.0000%; random path mean=0.800113; Δ mean=-0.037434.
- `structure_profile`: n=1045, mean=0.794258, variance=0.638053, 0..6=434,420,164,26,1,0,0, 2+/3+/4+/5+/6+=18.2775%/2.5837%/0.0957%/0.0000%/0.0000%; random path mean=0.800113; Δ mean=-0.005855.
- `triple_association`: n=1045, mean=0.813397, variance=0.624510, 0..6=418,428,175,24,0,0,0, 2+/3+/4+/5+/6+=19.0431%/2.2967%/0.0000%/0.0000%/0.0000%; random path mean=0.800113; Δ mean=0.013284.
- Exact uniform baseline recomputed from combinations: mean=0.800000, variance=0.614545; details in JSON.
- Monte Carlo: 20,000 full paths × 1,045 same targets; seed 20261014; random full-path mean and percentile intervals are in `RANDOM_MONTE_CARLO_BASELINE.json`.
- B component formula/source hash is recorded in manifest and preserved execution copy. Training cutoff is target−1 for every raw record; target result was not in its feature prefix.

## 9. C model

C DEFINITION NOT FOUND; C NOT EXECUTED. No qualifying frozen integrated source was found.

## 10. Contrarian model

Contrarian DEFINITION NOT FOUND; NOT EXECUTED. Structural tail frequencies are descriptive only.

## 11. Historical recommendations and 1245 error note

- Recursive inventory contains 16 candidate files. A V4 sealed prospective record for target 1245 exists in Git history on 2026-10-09 before the 2026-10-10 draw; however an independent purchase receipt was NOT FOUND, so this is not confirmed as a purchased recommendation.
- The 1245 lines were evaluated internally; 3 sealed lines. Aggregate hits and bonus checks are in `ERROR_NOTE_1245_AGGREGATE.csv`, without printing combinations in this report. Selection/exclusion rationales are only recorded if present before the draw.
- The broader authenticated historical purchased-line sample remains insufficient; do not generalize a model scorecard from this single sealed target.

## 12. Prior hypothesis and new hypothesis

- E013 is PRIOR RESULT; its raw prediction panel was read-only. The tail decomposition is recomputed from that panel today and remains retrospective, not prospective.
- Registered `H_TAIL_OBJECTIVE_001` as REGISTERED / NOT ADOPTED. Its confirmation requires frozen rules and future unseen targets.

## 13. Limits, checklist, and provenance

- B structure is a separate set-level component; it is absent from `combined_equal_rank`. The source does not expose full 45-number ranks, so Spearman/Kendall and rank displacement are not computable. E013 vote-ticket changes are a different, retrospective comparison.
- No integrated A/C/contrarian models or authenticated purchase records were reconstructed. No weekly recommendation pipeline was run and no recommendation combinations are reported.
- The local `origin/main` fetch failed because Git reported a DNS resolver thread startup error; GitHub API read access verified remote main. Remote write/publish status is assessed after local artifact verification.

### Submission checklist

| Item | Status | Evidence / reason |
|---|---|---|
| full raw dataset and latest round | PASS | DATA_VALIDATION.json |
| 2-source crosscheck | PASS | DATA_SOURCE_CROSSCHECK.csv |
| missing/duplicate/range/date/bonus validation | PASS | DATA_VALIDATION.json |
| full number stats and windows | PASS | NUMBER_FULL_STATS.csv; NUMBER_WINDOW_COMPARISON.csv |
| gap and long trend | PASS | NUMBER_GAPS.csv; NUMBER_LONG_TRENDS.csv |
| structure full/recent | PASS | STRUCTURE_FULL.csv; STRUCTURE_WINDOWS.csv |
| pair all combinations and FDR | PASS | PAIR_STATS.csv; RELATION_MULTIPLICITY_SUMMARY.json |
| triple all combinations and FDR | PASS | TRIPLE_STATS.csv; RELATION_MULTIPLICITY_SUMMARY.json |
| legacy A integrated execution | PARTIAL | A source not found; descriptive A signal table only |
| B real walk-forward | PASS | B_METRICS_AND_RANDOM_COMPARISON.csv; b_model_predictions.csv |
| nonoverlap blocks | PASS | B_BLOCK_STABILITY.csv |
| B leakage | PASS | B_LEAKAGE_CHECK.json |
| direct random tickets same target | PASS | RANDOM_BASELINE_BY_TARGET.csv; RANDOM_EXECUTION_SUMMARY.json |
| 20k random complete paths | PASS | RANDOM_COMPLETE_PATHS.csv; RANDOM_MONTE_CARLO_BASELINE.json |
| E013 tail followup | PASS | E013_FOLLOWUP_COMPONENT_TAIL.csv |
| structure rank influence | PARTIAL | STRUCTURE_RANK_INFLUENCE.json; full per-number B ranks unavailable |
| 1245 source search and pre-draw provenance | PARTIAL | ROUND_1245_PROVENANCE.json; purchase receipt not found |
| 1245 aggregate error note | PASS | ERROR_NOTE_1245_AGGREGATE.csv |
| historical recommendation scorecard | PARTIAL | only one sealed prospective target; insufficient authentic purchase records |
| C authoritative source | PARTIAL | not found; not executed |
| contrarian authoritative source | PARTIAL | not found; descriptive structures only |
| hypothesis registry | PASS | HYPOTHESIS_REGISTRY_UPDATE.csv |
| preservation and hashes | PASS | RUN_MANIFEST.json; SHA256SUMS.txt |
| report generated and reread | PASS | REPORT.md |


## Corrected source cross-check and structure source audit

The first source-comparison output recorded false date flags because it compared dotted raw dates with ISO dates. An independent read-back normalized the date format; six sampled rounds then matched on date, main-number set, and bonus. See `DATA_SOURCE_CROSSCHECK_FINAL.csv`. The earlier cross-check artifacts are retained as execution/debug evidence.

The frozen B source AST shows its combined rank formula contains long frequency, gap, recent momentum, pair, and triple ranks; it does not contain the separate structure-profile term. The source does not emit full 45-number ranks, so Spearman/Kendall and rank-change metrics are unavailable. E013's separate equal-vote omission analysis changed the ticket on 164/645 retrospective targets (25.4%); removing structure changed mean hits by +0.0295, 2+ by −1.40 pp, and 3+ by +0.93 pp. This post-hoc tail tradeoff did not change B. See `STRUCTURE_RANK_SOURCE_AUDIT_V2.json` and `E013_FOLLOWUP_COMPONENT_TAIL.csv`.

Execution note: the analysis wrapper returned exit code 1 only because the final report sanity guard rejected the expected training-cutoff text. It had already produced the full analysis outputs; `FINALIZE_RUN.py` independently re-read them and passed 16/16 checks without repeating calculations.
