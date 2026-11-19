# Project State Audit

- Frozen baseline entries: 24.
- Baseline integrity: PASS.
- Raw source: `C:\Users\user\Documents\Codex\2026-10-06\cloud-x20\work\lotto-data\lotto_data.csv`; rows 1..1244 continuous; date/number/bonus validation passed.
- No row after round 1244 was requested by the audit reader.
- Full walk-forward: 33408 stored rows; 8352 consistent unique target/model predictions, 201..1244; cutoff=t-1; raw actual cross-check passed.
- Recent holdout: 352 rows for 1201..1244, all cutoffs t-1; actuals match raw.
- Current 1245 candidates: 8 predicted tickets; target=1245/cutoff=1244; no actual result column.
- Group walk-forward: 3,132 rows, 3 groups × 1,044 targets, cutoff=t-1; actuals match raw.
- Prior preflight snapshot `C:\Users\user\Documents\Codex\2026-10-08\b-model-backtest-py-b-1201\outputs\1245_final_pipeline\input_audit.md` still records the earlier missing-path state; the subsequent --check-only run passed. Snapshot was preserved.
- Final 3-line files currently exist: False (expected false before final run).

## Result

PASS
