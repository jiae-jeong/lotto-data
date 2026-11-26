# Lotto Project State Addendum — 2026-11-26

This append-only addendum supplements `lotto_project_state_2026-11-26.md`.

## Queue audit
- `automation/research_queue_v2.json` blob SHA: `a830d03dd5bab001eba1b4a35f6830efb3d2d505`; the queue itself is older than the 2026-11-25 E083 and 2026-11-26 E084 studies.
- Its latest validation is run 44543887535 on 2026-11-20; 251 tests and E030–E076 queue contract passed, while research and prospective-ledger jobs were skipped.
- E084 was recorded in `automation/research_queue_v2_addendum_20261126.json`; the original queue was not overwritten.
- H1250-A/B remain implemented/awaiting dispatch and are five-line studies, so they cannot qualify target 1252's three-line gate.

## E084 execution transparency
- The actual calculations ran in the connected JavaScript isolate using the registered formulas and fixed execution design.
- The stored Node runner was fetched and hash-verified but was not directly launched in Node in this run.
- E084 is historical cutoff-safe diagnostic work, not independent external nested validation or prospective confirmation.
- The canonical candidate_recall@30 paired CI is the preregistered-seed field documented in `E084_RESULTS_CI_CANONICALIZATION_20261126.json`; the redundant duplicate CI field is not canonical.
- Output SHA256s were re-fetched and matched the manifest.

## Current decision
Target 1252 remains STRICT FAIL / NOT READY. No candidate numbers, TOP30, core/tail, or purchase lines are available for display. No freeze/seal and no DELIVERY_LOG event were created. The prospective minimum target count and completion rule remain unspecified and unchanged.
