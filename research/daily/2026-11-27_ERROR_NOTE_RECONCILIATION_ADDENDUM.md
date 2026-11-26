# Error-note Reconciliation Addendum — 2026-11-27

This append-only addendum supplements the Friday reproduction audit. It does not modify the original recommendation, error note, delivery ledger, or purchase-confirmation registry.

## Original records re-fetched

- Original 1251 error note: research/weekly_purchase/1251/ERROR_NOTE_RECOMMENDATION_REVIEW_1251_20261122.json
  - Git blob SHA: 7e8395a448f86ca96c04c32d90beda0c0ab2ea02
- Independent recalculation addendum: research/weekly_purchase/1251/ERROR_NOTE_RECALC_AUDIT_ADDENDUM_20261122.json
  - Git blob SHA: 43d9f990689d8cfe1e8a18198155531d65c671b9
- Source-link correction: research/weekly_purchase/1251/ERROR_NOTE_SOURCE_LINK_CORRECTION_20261122.json
  - Git blob SHA: 8e91c9db58ed92b02b8391704ad3ac8922674b91
- Original delivered artifact: blob SHA 9da6f5760367758896f20f8643c771452e7948cd
- DELIVERY_LOG: blob SHA 24f66f12e71f7976db9d25d5bee32c12a02218b6

## Reconciled historical outcome

- Original artifact and ledger event match exactly.
- Recomputed line-hit distribution: [1, 1, 0].
- max-hit: 1; any2+: false; any3+: false; any4+: false; any5+: false; any6: false.
- Winning-number union coverage: 2/6.
- Bonus match: false.
- Purchase confirmation: NOT_CONFIRMED.

## Candidate-to-allocator failure decomposition

The preserved one-target diagnostic records:
- Total winning main numbers: 6.
- Candidate TOP30 recall: 5/6 (0.8333333333).
- Winners selected into the three-line portfolio: 2.
- Winners present in later sequential candidate pools but not allocated: 2.
- Winners outside the three-stage pool reach: 2.

This is a single-target post-draw decomposition only. It is not a performance estimate, cannot establish a recurring failure mechanism, and must not be used to tune the same target or promote a model/allocator.

## Provenance

Direct official API retrieval remains false. The corrected source record uses Yonhap's operator-attributed report and independent Newsis/FN News corroboration; the previously unverified LottoFinder/Lotto6 URLs were explicitly rejected. The raw historical source and original records remain unchanged.

No new delivery event was appended. No candidate or purchase lines were generated or displayed.
