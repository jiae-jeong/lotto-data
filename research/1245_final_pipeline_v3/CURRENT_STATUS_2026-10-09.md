# Current authoritative status — 1245 V3 (2026-10-09, updated)

**Status: SEALED V3 GATE NOT PASSED. Four pinned B-v1 CSV outputs have now been independently regenerated with exact historical hashes, but other required files and the prospective seal remain unavailable.**

This is an additive status correction. It preserves prior model reports, candidate lines, and execution history; it does not rewrite historical results as prospective evidence.

## Confirmed asset recovery after the initial status note

A search of the ChatGPT file library found the originally uploaded B-v1 source and raw dataset, even though they were absent from the current PC's scanned paths:

- Original B-v1 source: [recovered_original_assets/b_model_backtest.py](recovered_original_assets/b_model_backtest.py). The 27,977-byte materialized source matched the pinned SHA-256 3ecf4fb805c2448e49c39e01174b3a112d4865c7ff1a31157437515b78be47cb.
- Raw dataset: 43,234 bytes, SHA-256 243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f, matching the pinned historical data hash.
- Running the exact source in a separate scratch directory against the exact source data reproduced four historical CSV outputs with exact pinned hashes: predictions (33,408 records), holdout metrics (256 rows), classification (8 rows), and 50-round trends (56 rows).
- Verification table and result interpretation: [B_MODEL_RECOVERY_REPORT_2026-10-09.md](recovered_original_assets/B_MODEL_RECOVERY_REPORT_2026-10-09.md).
- The regenerated Markdown report is **not** byte-identical to the historical report: its path and newline environment differ. It is clearly labelled as regenerated and is not claimed as recovered verbatim.
- The four exact CSVs and the exact source/data are packaged separately in the recovery archive shared in the conversation; the CSVs have not yet been committed to this repository as raw files.

## Current independent validation findings

The 2026-10-09 independent run validated repository data rounds 1–1244 and recomputed 3,200 model predictions across expanding and rolling-300 windows for targets 1045–1244. It did not read round 1245's actual result.

The exact random baseline is 0.800000 mean hits per six-number ticket, 17.530810% for 2+ hits, and 2.383408% for 3+ hits. The selected three candidate lines remain the prior recovery lines. This post-hoc test did not demonstrate a repeatable advantage over random; see [the independent validation report](independent_validation_20261009_independent/INDEPENDENT_VALIDATION_REPORT.md).

## Remaining V3 blockers

The exact original B-v1 core outputs are reproducible, but the separate Oct 8 recent-validation/candidate output set remains unavailable. The original prospective protocol, registry, frozen model manifest, and seal are also unavailable. The baseline manifest itself is tracked at research/expansion_framework_v1/project_baseline_manifest.csv; the old V3 script expects it at a stale output path and also embeds machine-specific external paths.

The current-PC search was corrected to inspect the exact requested paths, and the search log is in [source_asset_search_v2.log](source_asset_search_v2.log). That search did not find the Oct 8 artifact set or prospective seal package locally.

The old README_v3.md, FINAL_PIPELINE_V3_AUDIT.md, and input_audit_v3.md show a historical 2026-10-08 READY_WITH_WARNINGS check-only snapshot. That does not override the later 2026-10-09 recovery result. The prior recorded current-environment V3 check-only attempt exited 1 with 18 blocking errors. It was not rerun during the corrected asset search because the existing script writes/overwrites four audit files in place. A future diagnostic run must use a disposable worktree/copy.

## Required next step

1. Bring the four exact CSVs from the provided recovery package into a dedicated tracked recovery directory, verify them against OUTPUT_SHA256.csv, and commit them without replacing prior files.
2. Search any genuine original-machine/backup copy for the missing Oct 8 recent/candidate artifacts and prospective seal files. If unavailable, keep them marked missing.
3. Do not fabricate old outputs, recreate a historical seal retroactively, or label the V3 gate READY. If the originals cannot be recovered, continue future research in a new, prospectively frozen version and keep the sealed V3 gate NOT PASSED.

No candidate file or automation setting was changed by this status correction.
