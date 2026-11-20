# E077 source-identity audit and hash-type correction

The initially reported mismatch compared two different hash types. The E077 preregistration field named `walkforward_git_blob_sha` contains a file-content SHA-256, while the evaluation result field `predictions_blob_sha` contains the Git blob object ID.

| Identity | Value |
|---|---|
| Git blob SHA returned by GitHub | `da19f4dc6ec500243cf7503abc096867d6dcf5db` |
| Independently recomputed file-content SHA-256 | `575b0f03ceb7f4e8424f3826d2527fa494fdc243aa79728735b986ca200e2c5e` |
| SHA256_MANIFEST entry | `575b0f03ceb7f4e8424f3826d2527fa494fdc243aa79728735b986ca200e2c5e` |
| Raw file bytes | 114,412 |

The recomputed content SHA-256 exactly matches the preregistered value and repository manifest. No input-content mismatch or substitution was found. The E077 calculation remains a reproducible historical diagnostic; this correction changes no selector rule, window, metric, comparator, bootstrap, or result. It does not create prospective evidence, a three-line portfolio, or strict purchase readiness.
