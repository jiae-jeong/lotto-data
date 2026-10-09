# V3 check-only error log (2026-10-09)

Command: `python research/1245_final_pipeline_v3/prepare_1245_final_three_lines_v3.py --check-only`
Exit code: 1. Final selector not called. Summary: BLOCKING_ERROR=18, ADVISORY_WARNING=2, EXPECTED_UNAVAILABLE=1, FINAL_STATUS=NOT_READY.

Observed blocking errors:

1. Missing pinned baseline manifest: `lotto-repo/outputs/research_expansion_framework_v1/project_baseline_manifest.csv`.
2. Missing raw source at prior machine path: `C:\Users\admin\Documents\Codex\2026-10-06\cloud-x20\work\lotto-data\lotto_data.csv`.
3. Missing `b_model_predictions.csv` at the old `cloud-x20/outputs` path.
4. Missing `b_model_holdout_metrics.csv` at the old path.
5. Missing `b_model_classification.csv` at the old path.
6. Missing `b_model_50_round_trends.csv` at the old path.
7. Missing `b_model_recent_predictions.csv` under repository `outputs/`.
8. Missing `b_model_recent_metrics.csv` under repository `outputs/`.
9. Missing `b_model_1245_analysis_predictions.csv` under repository `outputs/`.
10. Missing `b_model_1245_number_stats.csv` under repository `outputs/`.
11. Missing `b_model_1245_ticket_overlaps.csv` under repository `outputs/`.
12. Missing `b_model_1245_candidate_historical_performance.csv` under repository `outputs/`.
13. Missing `b_model_1245_candidate_groups_metrics.csv` under repository `outputs/`.
14. Missing `b_model_1245_candidate_groups_walkforward.csv` under repository `outputs/`.
15. Prospective framework files incomplete (protocol, registry, frozen model manifest, and seal not in repository).
16. Unique full target/model prediction rows=0; expected 8352.
17. Candidate group set mismatch (candidate artifacts absent).
18. Missing GitHub study correlation file at the historical `work/lotto-data-github/.../model_correlation.csv` path; a copy does exist at `research/expansion_framework_v1/studies/study_batch_001/model_correlation.csv`.

Advisories: stored candidate-group metrics are post-hoc/descriptive only; recent B-model performance is a small 44-round diagnostic. Expected unavailable: untouched 1245 actual result and post-draw performance.
