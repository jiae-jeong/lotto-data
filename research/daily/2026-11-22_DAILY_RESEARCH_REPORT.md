# Daily Lotto Research Report — 2026-11-22

## 1. New calculation: E079 fixed-candidate allocator ablation

- Preregistration: E079 frozen at 2026-11-22 08:17 KST; targets 401-1249 (849); rounds 1244-1249 are contaminated live-history diagnostics, not clean holdout.
- Candidate model and candidate scores were fixed. Only the three-line allocator changed: sorted-ticket E045 structural objective versus score-only top-six selection. Both arms use three disjoint six-number lines and union18.
- Canonical data: 1,250 contiguous draws through cutoff 1250; SHA-256 7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2; Git blob 66431d711919f179e4cb1349e2f7295c68a8735e. One internal blank physical line after round 1245 is filtered by the frozen parser; the logical round sequence is valid.
- Independent re-execution: 849/849 targets, t-1 cutoffs, zero metric/line-hit mismatches against PREDICTIONS_V2, zero geometry violations. Exact union18 null recomputation matched registered constants.
- Matched label-permutation baseline: 120 bundles per target per arm (101,880 per arm). Random means were close to exact null.

### Candidate-selection stage

| K | Mean winners in TOP-K | Recall@K | Uniform expected hits | Delta hits |
|---:|---:|---:|---:|---:|
| 10 | 1.299176 | 21.653% | 1.333333 | -0.034158 |
| 15 | 1.954064 | 32.568% | 2.000000 | -0.045936 |
| 20 | 2.584217 | 43.070% | 2.666667 | -0.082450 |
| 25 | 3.294464 | 54.908% | 3.333333 | -0.038869 |
| 30 | 3.962309 | 66.038% | 4.000000 | -0.037691 |

All five point estimates are below the uniform-random expectation. Candidate-stage promotion is not supported.

### Portfolio stage

| Metric | Exact null | A: structural | A delta | B: score-only | B delta |
|---|---:|---:|---:|---:|---:|
| max-hit | 1.514256 | 1.491166 | -0.023090 | 1.497055 | -0.017201 |
| any2+ | 0.474976 | 0.472320 | -0.002656 | 0.452297 | -0.022679 |
| any3+ | 0.071355 | 0.061249 | -0.010106 | 0.078916 | +0.007561 |
| any4+ | 0.004180 | 0.000000 | -0.004180 | 0.001178 | -0.003003 |
| any5+ | 0.000087 | 0.000000 | -0.000087 | 0.000000 | -0.000087 |
| any6 | 0.000000368 | 0.000000 | -0.000000368 | 0.000000 | -0.000000368 |
| union coverage | 2.400000 | 2.361602 | -0.038398 | 2.335689 | -0.064311 |

- A max-hit distribution (0-6): 36, 412, 349, 52, 0, 0, 0.
- B max-hit distribution (0-6): 30, 435, 317, 66, 1, 0, 0.
- A all-line hit counts (0-6; 2,547 tickets): 1,038, 1,065, 392, 52, 0, 0, 0.
- B all-line hit counts (0-6; 2,547 tickets): 1,052, 1,075, 353, 66, 1, 0, 0.
- Any2-positive non-overlapping blocks: A 7/17 = 41.18%; B 4/17 = 23.53%; both below 65%.
- A has higher any2/union point estimates; B has higher any3 point estimate. Paired adjusted intervals include zero for all four endpoints. No robust simultaneous gain.
- Both arms fail the historical strict gate: adjusted CI lower bounds are not positive for max-hit, any2, any3, and union coverage; block share fails; prospective confirmation is not defined.

### Inference conformance issue

The preregistered bootstrap seed is 20261122080. The authoritative V2 runner uses separate seed bases 20261122100, 20261122200, and 20261122300. The schedule is not specified in the preregistration. The reported intervals are diagnostic re-computations using the runner's constants, not a fully conforming preregistered inference record. This mismatch is preserved; no post-hoc seed repair is applied to this run.

## 2. Target-1251 delivered-artifact review

The preserved 2026-11-20 E054/E045 pre-draw artifact was reproduced exactly from cutoff 1250 and compared with the 2026-11-21 draw. The delivered three-line portfolio had line hits [1,1,0], max-hit 1, no any2+/any3+, union coverage 2/6, and no bonus match. Purchase remains unconfirmed.

Candidate/allocator diagnostic: 2 of 6 winners were in the delivered union; 2 more were available in later sequential top-16 candidate pools but not allocated; 2 were outside the three-stage pool reach. This is a one-draw diagnosis only and is not used to tune the model. The original artifact and delivery event were preserved; the post-draw review was appended to DELIVERY_LOG and recorded in a separate error note.

The 1251 result was cross-checked against a Yonhap report quoting the Donghaeng Lottery operator, a Newsis/FNNews report, and two independent result listings. Direct official API retrieval was not accessible in this run. An immutable cutoff-1251 snapshot was created without overwriting lotto_data.csv.

## 3. Prior failure and nested-validation review

- V54: max-hit and any3 passed their lower-bound checks but any2 lower bound -0.000945 failed; final 48-target any2 delta -0.105309.
- V83: any3 lower bound -0.005204 failed.
- V84: any2 lower bound -0.012794 failed.
- V85: max-hit -0.002510 and any2 -0.014901 failed.
- V86: all three lower bounds failed and positive-block share 64.71% was below 65%.
- E052 nested trailing-100 selector: 749 outer targets, max-hit/any2/any3/union adjusted CI lower bounds all negative, any2-positive block share 33.33%; strict FAIL.
- E078 was a design-only empirical block-power stress test, not model evidence or prospective confirmation.
- E077 one-ticket trailing-100 selector remained historical diagnostic only and did not qualify the three-line policy.

## 4. Data and policy status

- The canonical 1250-row file was not overwritten. New immutable snapshot: data/snapshots/lotto_data_through_1251_20261122.csv; 1,251 valid sequential draws; SHA-256 e3a43c7ba1217597cf5827a4f10f13c038744d3795e9fdf292c52481001ab064.
- Direct official API retrieval remains unavailable; the snapshot provenance explicitly labels the result secondary-cross-checked, not directly official.
- Three-line policy from target 1251 remains in force. No candidate numbers, TOP30, core/tail list, or purchase lines were generated or displayed. No freeze/seal or purchase confirmation was created.
- Prospective minimum target count and completion rule remain unspecified; no STRICT_PASS_READY status is possible until a rule is separately pre-registered and satisfied.

## 5. Next independent work

1. Pre-register a conforming bootstrap seed schedule before any further E079 inference; do not overwrite this audit.
2. Continue the fixed-allocator candidate-recall axis or a genuinely new allocator hypothesis, with untouched prospective evaluation beginning only after a pre-draw freeze.
3. Resolve the prospective confirmation minimum/completion rule without changing historical gates or using 1244-1249 as clean holdout.


## Append-only hash correction — 2026-11-22

The first metadata helper used for the new 1251 snapshot omitted SHA-256 round constant `0xefbe4786`. The snapshot bytes and 1,251 records are unchanged. A corrected standard SHA-256 implementation passed the published `abc` test vector and reproduced the canonical `lotto_data.csv` hash exactly. The correct snapshot SHA-256 is `2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9`; the earlier `e3a43c7ba1217597cf5827a4f10f13c038744d3795e9fdf292c52481001ab064` value is invalid and superseded. Correction artifact: `data/snapshots/lotto_data_through_1251_20261122_SOURCE_HASH_CORRECTION.json`. The original snapshot and original source metadata remain preserved.


## Append-only source-link correction — 2026-11-22

Two third-party URLs in the first source metadata/error-note drafts were not verified and are superseded. Use the verified links in `data/snapshots/lotto_data_through_1251_20261122_SOURCE_LINK_CORRECTION.json`: Yonhap, Newsis via FNNews, LottoLottery, and LottoKing. No result values changed. Direct official API retrieval remains unavailable. The prior source records remain preserved for audit.
