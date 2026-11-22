# Hash-audit correction supplement — 2026-11-23

Two audit-helper defects were corrected append-only.

1. The target-1251 snapshot SHA mismatch was false. The first helper omitted SHA-256 round constant `0xefbe4786`; the corrected implementation passes the standard `abc` vector, reproduces the canonical 1,250-row SHA-256, and matches the recorded 1,251-row snapshot SHA-256 `2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9`.
2. The apparent E080 output-manifest mismatch was also false for the same reason. With the constant restored, all nine output hashes match the original `SHA256_MANIFEST.json`, and all nine Git blob SHA-1 values recompute exactly. The original manifest remains authoritative; the 08:45 correction file is preserved but superseded.

These corrections do not change E080 metrics, model decisions, or strict-gate thresholds. Target-1252 data integrity is PASS; direct official API retrieval remains unavailable, and strict prospective readiness remains false.
