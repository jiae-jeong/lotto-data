# B-model original-source recovery package

This package was regenerated in an isolated scratch directory from two exact-hash source assets retrieved from the ChatGPT file library: the historical B-model Python source and `lotto_data.csv`.

## Exact source integrity

- `source/b_model_backtest.py`: SHA-256 `3ecf4fb805c2448e49c39e01174b3a112d4865c7ff1a31157437515b78be47cb` (matches pinned historical source hash).
- `data/lotto_data.csv`: SHA-256 `243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f` (matches pinned dataset hash).

## Reconstructed outputs

The following regenerated output CSVs match the historical manifest SHA-256 exactly:

- `outputs/b_model_predictions.csv`: `088685b5c30275c2640dfda2001beb99cebf5855156ae54ad5e0f6f170cf39be` (33,408 records)
- `outputs/b_model_holdout_metrics.csv`: `147765c9f3353deac5cc5c91e37ce0f80a7e4608c9e29738d4724130df5bc2a4`
- `outputs/b_model_classification.csv`: `2c7a8030b0129eef55137852a8e5e297d916239c46a8fc9bbe0e0c467ecf9ff2`
- `outputs/b_model_50_round_trends.csv`: `199bd09e71f9f7171b2c26ee68a7eb8afd40edcd17a1f8907dd09c2a4e7f57df`

The report is included for reading but is **not** hash-identical to the historical report: a scratch path/platform formatting difference remains. Do not use it as proof that the old report was recovered verbatim. Its generated SHA-256 is `4f3a02ba45ba7fb94498a7e23bb5307beff533ae322b6b47f303cce9465cd1b8`; pinned historical report SHA-256 is `2d9314c793c6508f2d6d5aab983c74b271c5b0f6c042997cfff1079742cf0512`.

## Result interpretation

The script validated 1,244 rows and generated 33,408 prediction records. Random-baseline mean is 0.8 hits per six-number ticket, with `P(2+) = 17.5308%`. Seven of eight models remain `ADDITIONAL VALIDATION`; `combined_equal_rank` is `HOLD`. The script's technical labels are not statistical significance tests or proof of predictive ability.

## Scope limitation

This restores the pinned B-v1 source and four exact B-v1 CSV outputs only. It does not restore the separate Oct 8 recent/candidate artifact set or the original prospective protocol/registry/model-manifest/seal. The sealed V3 gate therefore remains **NOT PASSED**. No 1245 result was read. All commands were run only in a new scratch directory; tracked project data and prior research files were not overwritten.
