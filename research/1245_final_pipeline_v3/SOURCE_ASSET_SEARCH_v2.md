# Source asset recovery search v2

Search date: 2026-10-09 (Asia/Seoul)

## Scope correction and result

The prior `SOURCE_ASSET_SEARCH.md` described the two former roots under `C:\Users\admin`; the user-provided roots are under `C:\Users\user`. This version records the requested paths exactly. This PC has only the profiles `C:\Users\admin` and `C:\Users\Public`; `C:\Users\user` is absent. Therefore the two exact historical paths cannot be traversed on this PC.

Read-only recursive exact-filename searches were run in:

- `C:\Users\user\Documents\Codex\2026-10-06\cloud-x20` — absent.
- `C:\Users\user\Documents\Codex\2026-10-08\b-model-backtest-py-b-1201` — absent.
- `C:\Users\admin\Documents\Codex` — present; recursively searched, including this current task/repository.
- `C:\Users\admin\.codex` — present; recursively searched for the same exact filenames.
- `C:\Users\Public\Documents\Codex` — absent. `C:\Users\Public` is the only other profile found.

No matching files were found in any searchable root. No files were copied because no original asset matched its expected checksum. No existing files, candidates, research artifacts, or automations were modified.

## Exact-name results

| Requested filename | Result in searched roots | Expected SHA-256 | Recovery status |
|---|---|---|---|
| `b_model_backtest.py` | Not found | `3ecf4fb805c2448e49c39e01174b3a112d4865c7ff1a31157437515b78be47cb` | Not recovered |
| `b_model_predictions.csv` | Not found | `088685b5c30275c2640dfda2001beb99cebf5855156ae54ad5e0f6f170cf39be` | Not recovered |
| `b_model_holdout_metrics.csv` | Not found | `147765c9f3353deac5cc5c91e37ce0f80a7e4608c9e29738d4724130df5bc2a4` | Not recovered |
| `b_model_classification.csv` | Not found | `2c7a8030b0129eef55137852a8e5e297d916239c46a8fc9bbe0e0c467ecf9ff2` | Not recovered |
| `b_model_50_round_trends.csv` | Not found | `199bd09e71f9f7171b2c26ee68a7eb8afd40edcd17a1f8907dd09c2a4e7f57df` | Not recovered |
| `b_model_backtest_report.md` | Not found | `2d9314c793c6508f2d6d5aab983c74b271c5b0f6c042997cfff1079742cf0512` | Not recovered; separate shorter summary is not a match |
| `run_b_model_backtest.ps1` | Not found | No pinned hash recorded | Not recovered |
| `prospective_protocol_v1.md` | Not found | `922a14570de7946067e84125109a88b3a098da0a6ad5899e2ae5244f77609e79` | Not recovered |
| `prospective_registry_v1.csv` | Not found | `ff15df7b180c04c6bd9b4ca36c752373bdfc9c48c936221920437dd3ad366184` | Not recovered |
| `prospective_model_manifest_v1.csv` | Not found | `49543f9abb81abe41b8f573ebfa9c56703cb6ef9275ee0434e7c30bea77c9ee4` | Not recovered |
| `prospective_seal_v1.txt` | Not found | `154260413c738c2d1dac632ab1d22a9d77f1812496520f620cce17c6b0afef09` | Not recovered |

Hashes above are expected historical hashes from repository metadata, not hashes of recovered files.

## Related files that do exist

These are different artifacts and do not satisfy exact-name or hash recovery:

| Existing artifact | Original path | Bytes | SHA-256 | Expected B pinned report hash match |
|---|---|---:|---|---|
| B model summary | `lotto-repo/analysis/2026-10-06/B_MODEL_RESULTS.md` | 2,340 | `ec771a8d4a6a3ad340e6df126b0da20afbe74b317bf963dac0e37e9cfe095e22` | No |
| Study comparison | `lotto-repo/research/expansion_framework_v1/studies/study_batch_001/b_model_comparison.csv` | 6,745 | `14c4f44b6cf95bef701fe2201465b409e6f78d28e4a48ce4da07041a3a432ad7` | No; comparison is not prediction rows |
| Baseline manifest | `lotto-repo/research/expansion_framework_v1/project_baseline_manifest.csv` | Present; see prior report | `f9e74a4b7e15631aaebdfdd7d58ae3ace6df64a8b5d115f4ac32ed35d639c4b2` | No; expected hashes/path metadata only |

No discovered file has been copied into a recovery folder; no SHA-matching source was found. The previous report’s old absolute paths are not evidence those roots were actually searched on this PC.

## V3 gate and blocker status

The mandatory original B artifacts and prospective protocol/registry/model manifest/seal remain missing. Consequently there is no newly recovered input set to validate with V3 `--check-only`, and the gate has not passed. `--check-only` was not rerun in this search-only pass: inspection of the existing V3 script shows this mode writes/overwrites `candidate_overlap_v3.csv`, `score_components_v3.csv`, `selection_trace_v3.csv`, and `input_audit_v3.md` in the research directory. Avoiding that run preserves the user’s explicit no-overwrite instruction. The prior recorded V3 check-only attempt exited 1 with 18 blocking errors, 2 advisories, and 1 expected-unavailable item; details are in the existing `outputs/PIPELINE_ERROR_REPORT.md`. Its historical path typo should not be mistaken for the corrected asset-search roots above.

## Minimum next action

Restore the exact original files from the original machine/backup or another source, then compare each SHA-256 to the pinned values above. Only SHA-matching originals should be copied into a new recovery folder. Once all gate-required inputs are available, run V3 check-only against a disposable copy/worktree so its diagnostic outputs cannot overwrite existing research files, inspect the full log, resolve only path/dependency errors supported by evidence, and rerun until `FINAL_STATUS=READY` (or report the remaining blockers).
