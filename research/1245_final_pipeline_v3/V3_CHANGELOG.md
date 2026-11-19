# V3 Change Log — 1245 Final Pipeline

Date: 2026-10-08  
Version: 3.0  
Parent reference: `outputs/1245_final_pipeline_v2/` (read only)  
New folder: `outputs/1245_final_pipeline_v3/`

## V2 gate behavior being corrected

V2 grouped every unresolved research warning with blocking conditions, so missing prospective results, model correlation, post-hoc historical evidence and ticket similarity all forced `NOT READY`. That conflated data/integrity failures with evidence limitations that are expected or advisory before the 1245 draw.

## V3 gate states

- `BLOCKING_ERROR`: malformed/extended raw data, SHA or input integrity mismatch, missing inputs, cutoff/leakage, future result access, nondeterministic selector, or post-hoc score wired into final selection.
- `ADVISORY_WARNING`: post-hoc historical evidence, limited recent sample, correlated models, or similar candidate tickets. Warnings remain visible but do not block by themselves.
- `EXPECTED_UNAVAILABLE_FOR_1245`: prospective/untouched 1245 result and future performance are not yet available. This is tracked separately and is not an error.
- Overall state is `NOT_READY` if any blocker exists, `READY_WITH_WARNINGS` if there are no blockers but advisories remain, else `READY`.

## Selection change

V1 ranked candidate groups using their 201–1244 mean hits; V2 retained that post-selected performance only for description but stopped generation on its warning. V3 does not use any candidate-group score to select, reorder, or weight final lines. The selector receives only cutoff-safe S001–S008 model outputs and the pinned model implementation. It uses a fixed six-family rank consensus plus two registered model tickets from distinct families; relationship S006/S007 is averaged as one family, while derived S008 is not an additional vote. Supplemental ticket pairs use fixed structural coverage, unique-number coverage, intersection, and model-ID tie-break order. No manual or arbitrary number is inserted.

## Verification and output

`--check-only` verifies the strict 1,244-row range and source SHA, cutoff-safe inputs, prospective seal and model source, GitHub-synced correlation provenance, selector input isolation, model candidate validity, and candidate overlap. It writes only diagnostic files, computes registered model candidate tickets in memory for overlap analysis, and never calls the final selector. `--generate` runs the same blocking checks; warnings remain visible and allowed. All final outputs are create-only.

Current check result: 0 blocking errors, 5 advisory warnings, 1 expected-unavailable item, `READY_WITH_WARNINGS`. The final selector was not run.

## Preservation

V1, V2, existing B-model and research files, raw data, the prospective registry and GitHub checkout were not modified. No 1245 actual result was read. No final 3-line output was created.