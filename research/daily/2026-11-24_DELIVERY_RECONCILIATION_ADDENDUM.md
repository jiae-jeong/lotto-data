# 2026-11-24 — historical delivery/error-note reconciliation addendum

This addendum supplements `research/daily/2026-11-24_DAILY_RESEARCH_REPORT.md`. It preserves the original artifacts and reports no candidate or purchase numbers.

## Target 1251 — actual user-visible research-selected delivery

- Source artifact: `research/weekly_purchase/1251/RESEARCH_SELECTED_LINES_1251_20261120.json`; Git blob SHA `9da6f5760367758896f20f8643c771452e7948cd`.
- Original artifact was read and compared with `ERROR_NOTE_RECOMMENDATION_REVIEW_1251_20261122.json`; no reconstruction or rewrite.
- Model/allocator: E054 / unchanged E045; target 1251, cutoff 1250; three lines of six, pairwise-disjoint union18.
- 1251 result cross-check: operator-attributed Yonhap report and independent listings agree on the draw; the repository's latest source row also matches. Direct Donghaeng API retrieval was not obtained.
- Recomputed delivery outcome: line hits 1/1/0; max-hit 1; any2+/any3+/any4+/any5+/any6 all false; union coverage 2/6; bonus match false.
- Candidate-stage record: top30 recall 5/6; winner rank positions were preserved in the original error note. The same note's separate stage trace records 2 selected winners, 2 winners present in later sequential pools but not allocated, and 2 outside the three-stage pool reach. These are single-target diagnostics; do not reinterpret them as a stable allocator effect or tune to them.
- Status: STRICT_FAIL / research-selected, no predictive-edge claim; purchase NOT_CONFIRMED.

## Earlier displayed/preserved records

- Target 1249: DELIVERY_LOG records an intermediate five-line display, line-hit distribution 2/1/0/0/1, union coverage 4/6, max-hit 2, any2+ realized, any3+ not realized. The original candidate bank was not available, so candidate-stage recall cannot be reconstructed. This is not confirmed purchase evidence.
- Target 1250: the five-line artifact is preserved as a candidate record, but the append-only evidence correction says user-visible delivery is unverified. The saved-candidate diagnostic has union coverage 2/6 and max-hit 1; two retained winners were split across lines. It is not a delivered or purchased result and cannot qualify the three-line policy.
- Targets 1247/1248: multiple preserved line sets and no receipt/explicit confirmation; do not choose among them retrospectively.
- `research/PURCHASE_CONFIRMATION_REGISTRY.json` remains empty (`confirmed_purchases: []`). No recommendation is counted as an actual purchase.

## Learning boundary

The 1251 result is one post-draw observation. It does not establish model or allocator superiority. Keep candidate recall, line allocation, user-visible delivery, and confirmed purchase as four separate records. No DELIVERY_LOG entry was added in this run because no candidate or purchase numbers were displayed to the user.
