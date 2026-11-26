# Lotto Project State — 2026-11-26 (append-only snapshot)

## Master and provenance
- Latest `main` inspected; `LOTTO_PROJECT_PROTOCOL.md` and `AGENTS.md` read in full.
- The legacy `lotto_project_state_2026-10-06.md` is not the current state; this file is the dated snapshot for continuation.
- Current canonical snapshot: `data/snapshots/lotto_data_through_1251_20261122.csv`, 1,251 rows, cutoff 1251.
- SHA-256: `2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9`.
- Git blob SHA: `be2fa07921a92f335aeb6e715b4f40098e297834`.
- Header, sequential rounds, six distinct main numbers, range 1–45, and bonus validity passed. Direct official API retrieval remains unavailable; the 1251 result is corroborated by operator-attributed reporting and independent result listings.
- Targets 1244–1251 remain contaminated live-history diagnostics, not untouched holdout or prospective evidence.

## Active purchase policy
- From target 1251 onward: exactly three lines, six main numbers each.
- Historical five-line records through target 1250 remain immutable and cannot qualify the three-line gate.
- Strict gate unchanged: all four adjusted moving-block CI lower bounds (max-hit, any2, any3, winning-union coverage) strictly >0 versus the exact geometry-matched null; family alpha 0.05, per-metric alpha 0.0125; any2-positive non-overlapping 50-target block share >=0.65; 50-target blocks plus final remainder; cutoff-safe nested/rolling evaluation; multiplicity/selection-bias control; prospective confirmation.
- Prospective minimum target count and completion rule remain unspecified. Do not invent or borrow the separate prospective_v4 200-target endpoint.
- Target 1252 remains STRICT FAIL / NOT READY. No candidate values, TOP30, core/tail, purchase lines, or random fallback are authorized. No freeze/seal exists.

## Current 1252 research results
- E080 Borda rank aggregation: historical diagnostic only; no model promotion.
- E081 MIN_RANK rescue: candidate CIs did not establish advantage; portfolio strict gate failed.
- E082 rank dependence/overlap: diagnostic only; no promotion.
- E083 prequential dynamic ranker selector: 801 historical targets, 160,200 candidate random sets, 96,120 three-line random portfolios, 4,000 bootstrap replicates. Historical strict gate failed; any2-positive block share 6/16 = 37.5%; prospective confirmation absent.
- E084 derived-signal redundancy ablation (2026-11-26): one preregistered challenger removed the derived balanced/contrarian terms from the five-component mean-z consensus. Algebraically, the full five-term score is rank-equivalent to recent30_z + 2*gap_z + momentum_z; the two derived terms add one extra gap vote, not a new feature dimension.
  - Target range 401–1251, 851 targets; target t used only through t−1.
  - Candidate recall@30: full five 66.647%, base-three 66.804%, exact uniform 66.667%; paired base-three minus full-five = +0.157 percentage points, 95% MBB CI [-1.018, +1.195] pp.
  - Base-three recall@30 versus exact uniform = +0.137 pp, 95% MBB CI [-1.293, +1.351] pp.
  - Base-three portfolio vs exact disjoint-union18 null: max-hit delta -0.02072 (adjusted CI lower -0.09240); any2 delta +0.00093 (lower -0.04489); any3 delta -0.01260 (lower -0.03845); union coverage delta -0.03690 (lower -0.14618).
  - Any2-positive full blocks 9/17 = 52.94%, below 65%.
  - E084 historical strict gate failed; no model or allocator promoted.
  - Runner blob SHA `b7049773330c72a7909a45b56e9d2c288ac47257`; preregistration blob SHA `4b2a3e566754f76407cf4dd5877cc8d5f7e2b7c0`; source SHA as above.
  - All E084 output hashes were re-fetched and matched the saved SHA256 manifest.
- E084 report and data: `analysis/2026-11-26/E084_DERIVED_SIGNAL_REDUNDANCY_ABLATION_3LINE_v1/`.
- Daily study report: `research/daily/2026-11-26_DAILY_RESEARCH_REPORT.md`.
- Full-data descriptive maintenance: `research/daily/2026-11-26_MAINTENANCE_ADDENDUM.md`.

## Historical delivery and purchase provenance
- Target 1249: the 2026-11-06 five-line intermediate candidate was displayed, strict FAIL, not a sealed final; no purchase confirmation.
- Target 1250: original delivery evidence was corrected as unverified; the stored five-line artifact is not confirmed as user-visible delivery or purchase.
- Targets 1247/1248: conflicting preserved line sets; no receipts or explicit purchase confirmations. Excluded from a definitive actual-purchase aggregate.
- Target 1251: exact three-line artifact and DELIVERY_LOG event match; line-hit distribution [1,1,0], max-hit 1, any2+ false, union coverage 2/6. Purchase remains unconfirmed.
- Purchase-confirmation registry remains empty. Display is not purchase.
- Original recommendation files, DELIVERY_LOG, and error notes were not edited or reconstructed.

## 1250 remediation carry-forward
- `research/weekly_purchase/1250/REMEDIATION_PLAN_2026-11-06.md` was read. V54/V83/V84/V85/V86 all failed; the last-48 any2 weakness and multi-version selection-bias warning remain.
- H1250-A/B V2 preregistration exists but remains `SPEC_FROZEN_IMPLEMENTATION_PENDING`. The post-registration workflow audit records no workflow_dispatch execution; no external nested result exists.
- H1250-A/B are five-line designs and cannot qualify target 1252's three-line gate.

## Signal/model status
- Latest complete active signal scorecard (2026-11-21) contains five active signals with 1,050 cutoff-safe one-ticket targets each.
- A/C integrated legacy sources remain `NOT_EXECUTED_SOURCE_NOT_RECOVERED`.
- A_v2, C_v2, contrarian_v2 remain `MORE_TEST`; none is three-line purchase evidence.
- B triple_association has the best point mean in the latest one-ticket component scorecard, but E061 simultaneous intervals included zero; no promotion.
- Pair/triple descriptive frequencies were refreshed on the full 1–1251 dataset; no prior multiple-comparison relation hypothesis was re-tested or promoted.

## Next continuation point
1. Do not create another variant on the same 401–1251 historical range for E084's question.
2. Resolve the prospective-confirmation policy gap only through a separately versioned policy decision; do not invent a minimum count.
3. Pursue genuinely independent external/nested validation or a new preregistered research gap, with candidate stage and three-line allocator kept separate.
4. Recheck the official primary result source when accessible; until then preserve the secondary-cross-check limitation.
5. Keep the Thursday freeze/seal and Friday exact-reproduction process unchanged. No strict PASS means no candidate or purchase-line visibility.
