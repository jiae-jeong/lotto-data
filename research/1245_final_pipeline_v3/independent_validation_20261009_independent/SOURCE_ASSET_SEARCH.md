# Local and GitHub source-asset search

Search date: 2026-10-09 (Asia/Seoul). This report distinguishes found file content from checksum metadata about files that were not found.

## GitHub verification

- Confirmed `main` HEAD: `f11a0e1a6d170bb76df83b8aea6fc3e259fae286` (`Make recovery runner rerunnable with unique output IDs`).
- Confirmed branch list: only `main`; no other repository branches returned. GitHub code search in the connected `jiae-jeong` account for `b_model_predictions.csv`, `prospective_registry_v1.csv`, and `b_model_backtest_py_b_1201` returned no results.
- Recovery report, pipeline error report, model candidates, validation summary, and final candidate CSV were fetched successfully from `main`.

## Local PC and Git history

- The previous machine roots `C:\Users\admin\Documents\Codex\2026-10-06\cloud-x20` and `C:\Users\admin\Documents\Codex\2026-10-08\b-model-backtest-py-b-1201` do not exist on this PC.
- Exact-name scan under `C:\Users\admin` found no `b_model_predictions.csv`, `b_model_holdout_metrics.csv`, `b_model_classification.csv`, `b_model_backtest.py`, or V3 prospective registry/manifest/seal files outside the current repository copies/references.
- Git history contains the source data and study framework, plus `analysis/2026-10-06/B_MODEL_RESULTS.md` and `research/expansion_framework_v1/studies/study_batch_001/b_model_comparison.csv`; it does not contain B prediction/metrics/classification CSVs, A/C/contrarian model programs/results, or prospective V3 seal files. `git fsck --full --no-reflogs --unreachable` returned no unreachable objects.
- The B report and comparison are not the missing pinned B outputs. The B comparison SHA-256 is `14c4f44b6cf95bef701fe2201465b409e6f78d28e4a48ce4da07041a3a432ad7`; the available B summary SHA-256 is `ec771a8d4a6a3ad340e6df126b0da20afbe74b317bf963dac0e37e9cfe095e22`. The comparison contains 1,044-round pairwise overlap/correlation summaries, not B prediction rows.
The available B summary reports no model meeting its KEEP rule: seven of eight methods were classified as additional validation and combined-equal-rank as HOLD. Its 50-round-block table covers seven blocks / 350 tickets against a random expectation of 0.800 mean hits and 17.5308% 2+ hits; structure-profile (0.851 mean) and frequency-plus-gap (0.829) were still only additional-validation cases. This is a report summary, not a fresh rerun, and the pinned detailed B prediction outputs remain unavailable. The project-state document likewise describes historical output row counts but does not contain those output files.

## Found manifests and pinned B assets

- `research/expansion_framework_v1/project_baseline_manifest.csv` exists; SHA-256 `f9e74a4b7e15631aaebdfdd7d58ae3ace6df64a8b5d115f4ac32ed35d639c4b2`. `UPLOAD_SHA256_MANIFEST.csv` also exists. The V3 script instead looks for the baseline manifest under `outputs/research_expansion_framework_v1/`, so the blocker is an incorrect expected path.
- The baseline manifest records expected historical hashes and old `C:\Users\user\...cloud-x20\outputs` paths. These are metadata only; the file bytes are absent. Missing pinned assets include:

| Asset | Expected bytes | Expected SHA-256 | Search result |
|---|---:|---|---|
| `b_model_backtest.py` | 27,977 | `3ecf4fb805c2448e49c39e01174b3a112d4865c7ff1a31157437515b78be47cb` | not found |
| `b_model_predictions.csv` | 3,236,859 | `088685b5c30275c2640dfda2001beb99cebf5855156ae54ad5e0f6f170cf39be` | not found |
| `b_model_holdout_metrics.csv` | 113,856 | `147765c9f3353deac5cc5c91e37ce0f80a7e4608c9e29738d4724130df5bc2a4` | not found |
| `b_model_classification.csv` | 3,509 | `2c7a8030b0129eef55137852a8e5e297d916239c46a8fc9bbe0e0c467ecf9ff2` | not found |
| `b_model_50_round_trends.csv` | 6,264 | `199bd09e71f9f7171b2c26ee68a7eb8afd40edcd17a1f8907dd09c2a4e7f57df` | not found |
| `b_model_backtest_report.md` | 10,907 | `2d9314c793c6508f2d6d5aab983c74b271c5b0f6c042997cfff1079742cf0512` | pinned version not found; a shorter separate B summary exists |

## Raw source hash clarification

- The current worktree file has SHA-256 `10beb0a7974f648b39aa130bb714b1c338296bf59ecd106e9407bee5875538aa` due to checkout line endings. After CRLF-to-LF normalization its SHA-256 is `243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f`, matching both the pinned baseline and the historical Git blob at commit `9058e4d`/current source history. The raw data is present and byte-normalization explains the earlier hash discrepancy. The earlier report's broad statement that the SHA differed should be read as a worktree-byte difference, not a data-content difference.

## V3 prospective seal files

The current Git tree and local scan contain no `prospective_protocol_v1.md`, `prospective_registry_v1.csv`, `prospective_model_manifest_v1.csv`, or `prospective_seal_v1.txt`. The old V3 input audit lists expected hashes for these historical external assets: protocol `922a14570de7946067e84125109a88b3a098da0a6ad5899e2ae5244f77609e79`, registry `ff15df7b180c04c6bd9b4ca36c752373bdfc9c48c936221920437dd3ad366184`, model manifest `49543f9abb81abe41b8f573ebfa9c56703cb6ef9275ee0434e7c30bea77c9ee4`, seal `154260413c738c2d1dac632ab1d22a9d77f1812496520f620cce17c6b0afef09`. These are recorded expected hashes, not recovered file hashes.
