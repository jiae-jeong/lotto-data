# 1245 recovery execution report

Date: 2026-10-09 (Asia/Seoul)

## Execution status

- Candidate generator: executed from repository `run_batch.py` using rounds 1..1244.
- V3 selector: executed; produced exactly three six-number lines.
- Original sealed V3 gate: NOT PASSED (`--check-only` returned 18 blockers).
- Interpretation: recoverable algorithm execution, explicitly unsealed due missing external artifacts.

## Input validation

- Raw file: `lotto_data.csv`
- SHA-256: `10beb0a7974f648b39aa130bb714b1c338296bf59ecd106e9407bee5875538aa`
- Rows: 1244; rounds 1..1244 consecutive, unique; latest round 1244, date 2026.10.03.
- All six main numbers are unique and in 1..45; bonus is in range and separate.
- Target result for 1245 was not read.

## Final lines

| Line | Numbers | Sources | Rule |
|---:|---|---|---|
| 1 | 7 11 13 16 32 34 | S001;S002;S003;S004;S005;S006;S007 | equal-family-rank consensus; S008 hybrid not counted again; ties lower number |
| 2 | 13 15 16 18 31 38 | S001 | registered model candidate; distinct signal family; maximize portfolio number coverage |
| 3 | 3 10 17 23 25 27 | S003 | registered model candidate; distinct signal family; maximize portfolio number coverage |

Selection reasons: line 1 is the equal-family-rank consensus across S001-S007, with S006/S007 averaged as one relationship family and S008 excluded as a duplicate hybrid vote. Lines 2–3 are distinct-family registered model tickets selected by the existing V3 selector for structure coverage, portfolio number coverage, overlap, and deterministic model-ID ties.

## Model candidates

The eight actual generated tickets and their registered rules are in `model_candidates.csv`. Model-level historical evidence is summarized in the already committed `research/expansion_framework_v1/studies/study_batch_001/model_metrics.csv` and `rolling300_metrics.csv`; these were read as stored research results, not recomputed during this recovery run. The study report marks the evidence post-hoc/validation-required. The separate B-model report is present, but its prediction/classification CSVs are not.

## Stored model validation results

The table below summarizes the repository's already stored walk-forward study outputs. These were not recomputed during the recovery run and are marked post-hoc/validation-required. Random baseline mean is 0.800 hits per ticket.

| Model | Full n | Mean hits | Delta vs random | Rolling 300 n | Mean | Recent 200 n | Mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| S001 multi_window_frequency | 1044 | 0.784 | -0.016 | 744 | 0.753 | 200 | 0.750 |
| S002 gap_regime_hazard | 1044 | 0.779 | -0.021 | 744 | 0.828 | 200 | 0.925 |
| S003 momentum_state_transition | 1044 | 0.797 | -0.003 | 744 | 0.786 | 200 | 0.790 |
| S004 conditional_probability | 1044 | 0.795 | -0.005 | 744 | 0.765 | 200 | 0.775 |
| S005 structure_transition | 1044 | 0.773 | -0.027 | 744 | 0.733 | 200 | 0.755 |
| S006 pair_residual_node | 1044 | 0.805 | +0.005 | 744 | 0.813 | 200 | 0.805 |
| S007 triple_residual_node | 1044 | 0.803 | +0.003 | 744 | 0.812 | 200 | 0.810 |
| S008 family_balanced_hybrid | 1044 | 0.810 | +0.010 | 744 | 0.792 | 200 | 0.745 |

Detailed rates and deltas are in `model_validation_summary.csv`. None of these post-hoc summaries proves a predictive edge.

## Blocking errors and outstanding verification

- Original pipeline --check-only failed with 18 blocking errors in this environment.
- The original pinned baseline manifest and B-model backtest/recent/candidate artifacts are absent from the GitHub repository.
- The prospective protocol, registry, model manifest, and seal referenced by V3 are absent from the GitHub repository.
- The raw CSV shipped with the repository is available and validates as rounds 1..1244; its SHA differs from the historical V3 machine-specific SHA.
- The V3 generator source run_batch.py and selector are executed, but no missing seal/hash checks are represented as passed.
- A/B/C/contrarian unified validation and the old local B report's backtest rerun were not performed; only stored S001-S008 study summaries are available.
- All historical study summaries are post-hoc and do not establish predictive advantage; exact random baseline is mean 0.8 hits and P(2+) 17.5308% per ticket.

## Re-run

From the repository root run:

```powershell
& 'C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' research\1245_final_pipeline_v3\recover_and_run_20261009.py
```

This runner refuses to overwrite its output directory. Use a new `--run-id` for another run.
