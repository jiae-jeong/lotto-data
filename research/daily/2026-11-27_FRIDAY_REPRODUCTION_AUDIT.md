# Friday Reproduction Audit — 2026-11-27

## Decision

**Target 1252: NOT_READY / STRICT FAIL. No verified three-line artifact exists.**

Friday is reproduction-only. No model search, weight tuning, allocator search, candidate generation, or fallback generation was run. Because Thursday's required three-line freeze/seal was not created and the current gate explicitly prohibits freezing, there is no sealed artifact to reproduce and no purchase lines to deliver.

## 1. Master state and carry-forward

- Latest main commit observed: 6e737959d83fb0ead5f4bbbbfdccd351d30f3c5a (2026-11-26 13:44:13 UTC).
- Read LOTTO_PROJECT_PROTOCOL.md, AGENTS.md, and research/weekly_purchase/1250/REMEDIATION_PLAN_2026-11-06.md.
- Read the 2026-11-26 state snapshot, E084 report/results/manifest, 1252 blocker addendum, 1252 model gate, and strict status.
- The latest completed new study is E084. Its question must not be re-run on the same historical range as a new study.

## 2. H1250-A/B preregistration and external execution audit

The frozen H1250 A/B preregistration was re-fetched:

- Preregistration: research/weekly_purchase/1250/H1250_AB_PREREGISTRATION_2026-11-10_V2.json
- Preregistration blob SHA: bcac96aa1a7db5bfb0f4e973ba7fc14a35f2b417
- Frozen source data cutoff: 1249
- Frozen data SHA-256: a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7
- Frozen candidate generator blob: a4d6bcfcfeea7e40b63bf42f3db1f98a0e4cbe92
- H1250 implementation: automation/h1250_ab_research_v2.py, blob SHA a7a7d7792c7ba84a1c12699f53d8a3f4009d8a66
- Workflow post-registration audit blob SHA: e4b74fb6453c41c662f32cd1ee0f31b282c1750b
- Workflow current blob SHA: 5bfac63506b9fc2d3f68350eafaa8676fa6a64d3
- Preregistered workflow blob SHA: 06a06bfe6ff6875bd4fe2b10dcde3fb746f5b281
- H1250-A/B V2 dispatch run: not found in the preserved post-registration audit.
- Status remains SPEC_FROZEN_IMPLEMENTATION_PENDING; no external nested result is available.

H1250-A/B are five-line historical designs for target 1250. They cannot qualify the active three-line policy from target 1251 onward.

## 3. Current source integrity recheck

Canonical snapshot and lotto_data.csv were both fetched from the current default branch.

- Snapshot: data/snapshots/lotto_data_through_1251_20261122.csv
- Canonical file: lotto_data.csv
- Both Git blob SHAs: be2fa07921a92f335aeb6e715b4f40098e297834
- Recomputed raw-file SHA-256: 2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9
- Stored SHA-256: identical
- Non-empty data rows: 1,251
- Round range: 1–1,251
- Sequence: contiguous after ignoring blank lines
- Main numbers: six distinct integers in 1–45 on every row
- Bonus: integer in 1–45 and distinct from that row's six main numbers
- One internal blank line occurs immediately before round 1246. It is a formatting anomaly, not a missing round; the raw source was not edited.

The parser audit explicitly ignores blank lines before validating row count and round sequence. No future round is present in the source. Target 1252's permissible historical cutoff remains 1251.

## 4. Historical delivery and error-note reconciliation

The exact target-1251 pre-draw artifact and its DELIVERY_LOG event were re-fetched:

- Artifact blob SHA: 9da6f5760367758896f20f8643c771452e7948cd
- DELIVERY_LOG blob SHA: 24f66f12e71f7976db9d25d5bee32c12a02218b6
- The three preserved artifact lines match the three ledger lines exactly.
- Against the recorded 1251 draw, line-hit distribution is [1, 1, 0].
- max-hit: 1
- any2+: false
- winning-union coverage: 2 of 6
- Purchase confirmation: NOT_CONFIRMED.

The purchase-confirmation registry was re-fetched and remains empty (0 confirmed purchases). No source recommendation, error note, or prior ledger event was edited or reconstructed. No new DELIVERY_LOG event was appended because no numbers were displayed.

## 5. Official-result provenance

The direct Donghaeng Lottery API/page remained inaccessible through the available retrieval route. The 1251 result in the canonical CSV was cross-checked against operator-attributed reporting by Yonhap and Newsis, which agree on the draw result and bonus. This is secondary-source corroboration, not a claim that the official API payload was directly retrieved.

- Yonhap, 2026-11-21: https://www.yna.co.kr/view/AKR20261121050800002
- Newsis, 2026-11-21: https://m.newsis.com/view/NISX20261121_0003877831
- Official Donghaeng Lottery channel's 1251 result video: https://www.youtube.com/watch?v=PwYPC5dvk5M

## 6. Target-1252 gate and Friday reproduction

The current 1252 status files remain unchanged:

- MODEL_GATE_1252_20261126.json: NOT_READY
- STRICT_PASS_STATUS_1252_20261126.json: NOT_READY
- Required purchase policy: exactly 3 lines, 6 main numbers each
- Current cutoff: 1251
- Data rows: 1,251
- Current source SHA-256: 2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9
- Failed gate: latest_e045_evidence_cutoff_mismatch
- Unevaluated: max-hit adjusted CI, any2 adjusted CI, any3 adjusted CI, winning-union coverage adjusted CI, any2-positive 50-target block share, prospective confirmation
- ready_file=null; ready_file_exists=false
- final_purchase_freeze_allowed=false
- line_level_output_status=SUPPRESSED_NOT_READY

E084 remains historical diagnostic evidence only: it did not pass the four adjusted CI lower-bound requirements, its any2-positive full-block share was 9/17 (52.94%), and it cannot supply prospective confirmation. The prospective minimum target count and completion rule remain unspecified; neither was invented or borrowed from another policy.

## 7. Friday action

- No candidate numbers, TOP30, core/tail, or purchase lines were generated or displayed.
- No random or arbitrary fallback was generated.
- No freeze/seal was created.
- DELIVERY_LOG and purchase-confirmation registry were not modified.
- No model or allocator was promoted.
- No Friday model search or number tuning was performed.

## 8. Next continuation

After the 1252 draw, update the source only after the result is corroborated, then perform a post-draw review of preserved artifacts without retroactively changing the 1252 decision. For target 1253, keep candidate selection and the exact three-line allocator separate; do not claim prospective confirmation until a separately versioned completion rule is approved and actually satisfied.

**Final status: NO VERIFIED FINAL PURCHASE LINES FOR TARGET 1252.**
