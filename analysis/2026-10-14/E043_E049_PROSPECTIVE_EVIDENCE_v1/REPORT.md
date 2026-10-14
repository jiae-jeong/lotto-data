# E043–E049 Prospective Evidence Freeze v1

Frozen at 2026-10-14T06:41:56.809752+00:00 UTC before target 1246 outcome access. Canonical source is rounds 1–1245, SHA-256 `e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4`. E030 target-1246 prediction is referenced without modification (SHA-256 `719c4cc11174c80dd1ddef75e438a2de36ec76842869128bf17ecacf646cb931`; cutoff 1245).

## Frozen setup

- E043 protocol hash is recorded in `PROSPECTIVE_PROTOCOL_SHA256.txt`.
- E044 purchase ledger schema is ready, but there are **0 verified actual purchase records**. No lines were reconstructed or generated.
- E045 created 10,000 deterministic random five-line portfolios for target 1246 using seed `20261015291`. Compressed pool SHA-256: `da3f890aac5c6eb4ac911bdd5d56de58a66a7bb986927791910e428858f0d583`. These are null comparators, not recommendations.
- E047 also froze 10,000 single-ticket random comparator draws (pool SHA-256 `16a7b9ff3da87c9670a87a412baafe14ca2d14728188d2024f80c90d7c1f0cf3`) for shadow-model paired evaluation.
- E046 outcome/prediction files are separate and write-once; target predictions are not regenerated after outcome.
- E047 uses mixture e-processes with familywise alpha 0.05 and fixed alpha allocation; no weekly p-value restart.
- E048 power/horizon numbers are planning approximations and do not count as evidence.
- E049 remains `PROSPECTIVE_PENDING`; no promotion is available before outcomes and the pre-registered evidence gates.

## Not claimed

No target-1246 outcome was evaluated, no actual purchase ledger entry was supplied, and no recommendation lines were created. Future evidence remains pending.
