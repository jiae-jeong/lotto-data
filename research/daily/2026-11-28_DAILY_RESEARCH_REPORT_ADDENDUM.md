# E085 preflight-scope correction — 2026-11-28

The initial repository preflight occurred **before** E085 preregistration. During that preflight, the existing public target-1252 artifact's line array was parsed internally to verify only structural metadata (line count, six entries per line, range, uniqueness, and disjointness). The values were not displayed, copied into any new artifact, or written into today's report.

After E085 preregistration, the guard and its regression tests used metadata only and did not open or parse the target-1252 line artifact.

This corrects the overly broad `line_values_read=false` wording in the E085 result/completion records: it is true for the guard/test execution only, not for the entire pre-registration preflight. The original files remain unchanged; this clarification is append-only. No model, allocator, threshold, delivery log, or purchase-confirmation record was changed.
