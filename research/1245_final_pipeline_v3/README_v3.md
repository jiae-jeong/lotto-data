# 1245 Final Pipeline V3

V3 preserves V1 and V2 and changes only the generation gate and fixed selection rule. It separates blocking errors, advisory warnings, and evidence that is expected to be unavailable before the draw.

## Current run

`--check-only` completed with:

- `BLOCKING_ERROR=0`
- `ADVISORY_WARNING=5`
- `EXPECTED_UNAVAILABLE=1`
- `FINAL_STATUS=READY_WITH_WARNINGS`

This status permits a future `--generate` run under the same frozen rules. This task ran check-only only. The final selector was not called and no final 3-line output was created. For overlap diagnostics, S001–S008 model candidate tickets were computed in memory from rounds 1–1244; no 1245 actual/result was opened.

## Frozen inputs and safety

Raw input is fixed to `C:\Users\user\Documents\Codex\2026-10-06\cloud-x20\work\lotto-data\lotto_data.csv`, exact SHA-256 `243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f`. It must contain exactly the rounds 1–1244 once each, the exact `round,date,no1..no6,bonus` header, valid six-number draws, and a separate valid bonus. An extra record is an error; it is not ignored. Historical input files, candidate source artifacts, prospective registry seal/source hashes, and the synchronized GitHub model-correlation snapshot are checked by the script.

The prospective registry remains unchanged. Generation loads the hash-pinned `study_batch_001/run_batch.py`, forms candidates using exactly rounds 1–1244, seed 20261008 and the registered 5,000-ticket structure bank. The selector has only model outputs and the pinned model module as inputs. A static contract check blocks historical metrics, actual numbers, recent metrics, or candidate-group scores from entering selection.

## V3 fixed selection rule

1. Make one consensus ticket by equal-weight ranks over six signal families: S001 frequency, S002 gap/time, S003 momentum, S004 conditional probability, S005 structure, and one relationship-residual family. For the relationship family, average S006 and S007 ranks; their high correlation is recorded as `DUPLICATED_INFORMATION`, not two votes. S008 remains a derived-ensemble diagnostic and does not receive an additional vote.
2. Make two more lines from registered S001–S007 candidate tickets, requiring two distinct signal families. Among eligible pairs, rank by (a) widest coverage of the seven recorded structure features across all three lines, (b) greatest number of unique portfolio numbers, (c) lowest total pairwise ticket intersection, then (d) ascending model IDs. All ties are deterministic. All chosen numbers originate from the registered model candidates or the fixed six-family consensus; no hand-added number is allowed.
3. Record each line's six numbers, source models/families, pair intersections, Jaccard similarity, structure profiles, and selection rule in final outputs and trace.

Historical candidate-group performance (201–1244) is `HISTORICAL_DESCRIPTIVE_ONLY`; recent performance is `DIAGNOSTIC_POST_HOC`. Neither reaches the selector or receives a weight. The score components file has no composite score. Prospective result absence is recorded as `EXPECTED_UNAVAILABLE_FOR_1245`, not a blocking error.

## Commands

Run validation only:

```powershell
& 'C:\Users\user\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\user\Documents\Codex\2026-10-08\b-model-backtest-py-b-1201\outputs\1245_final_pipeline_v3\prepare_1245_final_three_lines_v3.py' --check-only
```

Generate only when a deliberate separate run is requested:

```powershell
& 'C:\Users\user\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\user\Documents\Codex\2026-10-08\b-model-backtest-py-b-1201\outputs\1245_final_pipeline_v3\prepare_1245_final_three_lines_v3.py' --generate
```

Generation requires zero blocking errors. Advisory warnings and the expected-unavailable prospective outcome do not block it. Existing V3 final output names are create-only; the script refuses to overwrite them.

## Files

- `prepare_1245_final_three_lines_v3.py`
- `FINAL_PIPELINE_V3_AUDIT.md`
- `V3_CHANGELOG.md`
- `README_v3.md`
- `selection_trace_v3.csv`
- `score_components_v3.csv`
- `candidate_overlap_v3.csv`
- `input_audit_v3.md`

V1 and V2 files, raw data, research outputs and prospective registry are unchanged.