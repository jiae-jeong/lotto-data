# Source audit supplement — 2026-11-23

## Target 1252 data source

- Latest snapshot: `data/snapshots/lotto_data_through_1251_20261122.csv`.
- Git blob SHA-1: `be2fa07921a92f335aeb6e715b4f40098e297834`; recomputed Git blob identity from fetched content matches.
- Rows: 1,251; sequence 1–1,251 is contiguous; header, main-number uniqueness/range, and bonus validation pass.
- Independently computed SHA-256 from the exact fetched content: `5586b6ef620c74a1aee672564d070462f835b9ad1ebe445f4765665c507dbae7`.
- Previously recorded corrected SHA-256: `2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9` — **mismatch**.
- The SHA-256 implementation passes the standard `abc` vector and reproduces the canonical 1,250-row `lotto_data.csv` SHA-256. The fetched snapshot content also reproduces its Git blob SHA-1.
- The latest row matches the independently cross-checked 1251 result. Direct official Donghaeng API retrieval remains inaccessible through the available retrieval path; Yonhap and Newsis/FN News plus an independent result listing agree.

**Decision:** target-1252 source integrity is only a partial pass. Do not freeze/seal or generate candidate/purchase lines until the SHA-256 metadata discrepancy is reconciled. Do not overwrite the earlier correction; this is an append-only audit.
