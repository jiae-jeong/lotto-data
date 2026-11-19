# Historical review-index reconciliation — 2026-11-20

**Classification: new provenance / failure-decomposition diagnostic only. No model or purchase-policy promotion.**

## Finding

The repository contains original post-draw review notes for rounds 1245 and 1246, plus a separate 1245 model error-note aggregate. The current structured `HISTORICAL_CLOSED_LOOP_STATUS.json` has an empty `reviews` array and `latest_completed_review: null`. The review artifacts are therefore not represented in the current structured review index.

This is an index/scope gap, not evidence that either recommendation was actually purchased. The canonical purchase registry still has zero confirmed purchases, and rounds 1246–1248 retain unresolved source conflicts.

## Candidate stage vs. allocator stage

| Preserved source | Candidate union recall | Per-line hit counts | max_hit | any2+ |
|---|---:|---|---:|---|
| Round 1245 V4 preserved three-line source | 1/6 | 0, 0, 1 | 1 | No |
| Round 1246 V2 preserved five-line source | 2/6 | 1, 0, 1, 0, 0 | 1 | No |
| Round 1246 fallback five-line source | 4/6 | 1, 1, 1, 1, 1 | 1 | No |

Round 1245 is a candidate-stage failure: with only one winning number in the union, a 2+ line was impossible. Round 1246 fallback is a clear allocator/assembly failure on this single historical diagnostic: four winning numbers were present in the union, but they were spread so no line reached two hits. This does not establish a generally superior allocation policy.

## Provenance treatment

- Preserve all original recommendation files and post-draw reviews unchanged.
- Keep `recommendation_review_inventory` separate from `verified_actual_purchase_inventory`.
- Do not infer actual purchase from filenames, review wording, or a preserved pre-draw decision.
- Keep rounds 1245–1248 as contaminated live-history diagnostics, never clean holdouts.
- No candidate lines, final purchase lines, model weights, gates, or freeze/seal artifacts were created.

## Sources

- `analysis/2026-10-11/ROUND_1245_REVIEW.md`
- `analysis/2026-10-14/E020_TAIL_DISTRIBUTION_DECOMPOSITION_v1/ERROR_NOTE_1245_AGGREGATE.csv`
- `analysis/2026-10-18/ROUND_1246_REVIEW.md`
- `analysis/2026-11-20/HISTORICAL_CLOSED_LOOP_STATUS.json`
- `research/PURCHASE_CONFIRMATION_REGISTRY.json`

Machine-readable source hashes and calculations are in `RESULTS.json`.
