# Current authoritative status — 1245 V3 (2026-10-09)

**Status: V3 SEALED GATE NOT PASSED. Candidate reassessment exists, but is unsealed and does not establish predictive advantage.**

This note is an additive status index. It does not replace or alter prior reports, candidate lines, model results, the source dataset, or automation settings.

## Evidence currently confirmed

- The current `main` head before this note was `1ae9e4fe55db5aadce4cc095d7cce14ce4a36f4c`.
- The corrected local asset search is recorded in [SOURCE_ASSET_SEARCH_v2.md](SOURCE_ASSET_SEARCH_v2.md) and its actual read-only log in [source_asset_search_v2.log](source_asset_search_v2.log).
- The repository data has 1,244 consecutive rounds (1–1244), with the round 1244 date 2026-10-03. The independent report records the exact source validation and LF-normalized hash.
- The new post-hoc walk-forward run evaluated targets 1045–1244 using eight models and two windows: 200 target rounds × 8 models × 2 windows = 3,200 model predictions. Round 1245's actual result was not read.
- The exact random baseline is 0.800000 mean hits per six-number ticket, 17.530810% for 2+ hits, and 2.383408% for 3+ hits.
- Reassessment kept the three prior recovery lines unchanged. Historical portfolio means were 0.7283 hits per line (expanding) and 0.8117 (rolling-300), against 0.8000 random mean. This post-hoc evidence does **not** establish a repeatable predictive advantage.
- The detailed results are in [INDEPENDENT_VALIDATION_REPORT.md](independent_validation_20261009_independent/INDEPENDENT_VALIDATION_REPORT.md), [fresh_model_scorecard.csv](independent_validation_20261009_independent/fresh_model_scorecard.csv), and [fresh_portfolio_metrics.csv](independent_validation_20261009_independent/fresh_portfolio_metrics.csv).

## Why the V3 gate remains blocked

The 2026-10-09 asset search did not find the pinned original B-model assets or prospective seal package on the current PC. Related summaries and the study comparison CSV are not replacements for the expected original files or their hashes. Other V3-required historical B recent/candidate outputs are also absent from the current repository locations.

The existing V3 code additionally points to machine-specific directories, and its baseline-manifest path does not match the tracked repository location. Correcting paths alone would not restore the missing pinned inputs and must not be treated as passing the gate.

The prior recorded V3 check-only attempt in [PIPELINE_ERROR_REPORT.md](recovery_run_20261009/PIPELINE_ERROR_REPORT.md) exited 1 with 18 blocking errors. The 2026-10-09 search did **not** rerun `--check-only`, because inspection showed it writes/overwrites four audit artifacts in place. Any future diagnostic run must use a disposable copy/worktree and capture the exit code and full log.

## Important distinction: historical READY snapshot

The tracked [README_v3.md](README_v3.md), [FINAL_PIPELINE_V3_AUDIT.md](FINAL_PIPELINE_V3_AUDIT.md), and [input_audit_v3.md](input_audit_v3.md) contain an earlier 2026-10-08 snapshot saying `READY_WITH_WARNINGS` and listing historical external assets as present. That snapshot is not the current machine's asset-search result and must not be cited as evidence that the gate is ready today. The earlier files are intentionally preserved; this status note clarifies their temporal scope rather than rewriting them.

## Next actions

1. If an original PC, external disk, backup, cloud-synced folder, or archived project copy becomes accessible, recover the original assets and compare each to its recorded SHA-256 before use.
2. Do not fabricate the missing files, substitute summaries for pinned originals, or recreate a historical seal retroactively.
3. If the originals cannot be recovered, continue only in a clearly labelled unsealed research track based on the available repository sources; keep the sealed V3 gate marked **NOT PASSED**.
4. For future rounds, define and freeze any new protocol/model registry before producing those round's candidates, store its hashes and logs, and validate in an isolated worktree. Do not backdate a new protocol to round 1245.
5. Preserve prior candidate lines and research records. Do not change automation settings without an explicit request.

## Source links

- [Asset search v2](SOURCE_ASSET_SEARCH_v2.md)
- [Actual search log v2](source_asset_search_v2.log)
- [Independent validation](independent_validation_20261009_independent/INDEPENDENT_VALIDATION_REPORT.md)
- [Recovery pipeline error report](recovery_run_20261009/PIPELINE_ERROR_REPORT.md)
