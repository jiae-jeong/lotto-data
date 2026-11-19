# FINAL PIPELINE V3 AUDIT

Date: 2026-10-08  
Mode executed: `--check-only`  
Final selector: **not called**

## Gate totals

- **BLOCKING_ERROR:** 0
- **ADVISORY_WARNING:** 5
- **EXPECTED_UNAVAILABLE:** 1 (`EXPECTED_UNAVAILABLE_FOR_1245`)
- **FINAL STATUS:** `READY_WITH_WARNINGS`

## Blocking checks

|Check|Status|Result|
|---|---|---|
|Input files and baseline hashes|PASS|All required B-model, recent, candidate, candidate-group artifacts exist and match their pinned hashes; prospective artifacts and GitHub-synced correlation file also pass hash/seal checks.|
|Raw range and SHA|PASS|Exact source path; SHA-256 matches baseline (`243cd17e...e43b9f`); exactly 1,244 rows; exact header; rounds 1–1244 once; max=1244; six unique main numbers in 1–45; valid bonus separate. Additional rows cause a blocker and are never ignored.|
|Cutoff/leakage|PASS|Historical predictions require `training_through_round=t-1`; 1245 candidate inputs require cutoff 1244. S001–S008 diagnostic candidates use the pinned implementation and rounds 1–1244 only. No 1245 actual/result is accessed.|
|Deterministic selection|PASS|Selector accepts only model outputs and pinned model implementation; exact tie-breaks and fixed seed/bank are explicit. Historical group scores, actual results, recent metrics and number-history metrics are absent from its inputs. A contract failure is a blocker.|
|Historical score routing|PASS|201–1244 candidate-group performance is marked `HISTORICAL_DESCRIPTIVE_ONLY`, emitted separately, and excluded from final selection. Any historical score input routed into the selector is a blocking error.|

## Advisory warnings

1. Candidate-group history is post-hoc and descriptive only.
2. Recent B-model diagnostic uses 44 rounds and is not a selection weight.
3. B-v1 reference groups contain a 5/6 ticket overlap.
4. At least one S001–S008 model candidate pair also overlaps 5/6; the overlap report retains the cause and exact numbers.
5. GitHub `study_batch_001` finds highly correlated S006/S007 residual models. V3 labels them `DUPLICATED_INFORMATION`, averages them as one relationship-family vote, and excludes derived S008 from an extra independent vote.

These advisories do not block the V3 gate and are not hidden or removed. Final ticket similarity is considered by the deterministic portfolio rule; it never inserts an unmodeled number. Each chosen line and pairwise overlap/Jaccard/structure comparison will be recorded if generation is run later.

## Expected unavailable

Prospective/untouched 1245 actual result and post-draw performance do not yet exist: **`EXPECTED_UNAVAILABLE_FOR_1245`**. Their absence is not an error and is not required before the draw. If an outcome is later published, record it under the sealed prospective framework without modifying its rules.

## Current output and preservation

- `--check-only` exit code: **0**.
- Status: **READY_WITH_WARNINGS**.
- Final selector execution: **NO**.
- 1245 final three lines generated: **NO**.
- 1245 actual result used: **NO**.
- V1/V2, prior research, prospective registry, GitHub checkout and raw source modified: **NO**.

Detailed inventory and SHA evidence: `input_audit_v3.md`. Model-level candidate overlaps: `candidate_overlap_v3.csv`. Historical components and unavailable evidence: `score_components_v3.csv`. Gate/selector execution trace: `selection_trace_v3.csv`.