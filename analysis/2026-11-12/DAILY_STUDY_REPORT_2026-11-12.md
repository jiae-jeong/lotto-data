# Daily lotto research — 2026-11-12

## 1. Today's new study

**H1250 exact conditional-null audit:** independently verify the frozen V42 exact null for five disjoint six-number tickets with union size 30, then derive the null conditional on the number of winners retained by the candidate bank.

This is a new mathematical/implementation audit supporting the two preregistered H1250 axes. It is not a new predictive model, not an empirical edge claim, and not a strict-gate pass.

## 2. Work actually executed

- Read current `main`, `AGENTS.md`, `LOTTO_PROJECT_PROTOCOL.md`, H1250 remediation plan, V2 preregistration, current workflow, post-registration workflow audit, latest daily report, strict status, and actual-purchase closed-loop inventory.
- Verified current H1250 runner blob equals the V2 preregistered code hash.
- Verified all five frozen dependency blob hashes match current `main`.
- Verified current workflow blob equals the append-only post-registration workflow audit hash.
- Independently enumerated all candidate-bank hit-count allocations and all five-ticket hit compositions using exact integer combinatorics.
- Independently reproduced the frozen V42 mask-DP null using exact rational arithmetic.
- Ran 100,000 seeded random partitions for each candidate-bank hit count m=0..6 (700,000 total) as a Monte Carlo cross-check.
- Saved the standalone script, machine-readable results, report, and SHA-256 manifest in a new append-only date folder.

## 3. Numerical findings

Under a uniform six-of-45 draw and a fixed 30-number candidate bank:

- Expected candidate-bank winners: **4.0000 of 6**; expected recall@30 **66.6667%**.
- P(M<=2): **8.4575%**; P(M>=3): **91.5425%**; P(M>=4): **68.8625%**.

Unconditional exact null for five disjoint six-number tickets with union30:

| Metric | Exact null |
|---|---:|
| E[max_hit] | 1.834653 |
| P(any2+) | 70.9476% |
| P(any3+) | 11.8679% |
| P(any4+) | 0.6967% |
| E[winning_union_coverage] | 4.000000 |

The independently derived exact rational results match the frozen V42 implementation exactly: maximum absolute difference **0.0**. The 700,000-partition Monte Carlo cross-check's largest absolute discrepancy from exact conditional values was **0.0016903**.

## 4. New candidate/allocator decomposition rules

- With a fixed candidate bank, union coverage is exactly M, the count of winners retained in that bank. Changing the allocator cannot change it.
- H1250-A must have identical per-target union coverage across rr/contig/snake/paired. Any difference is a trace or implementation defect.
- H1250-B rankers reorder the same top30 membership, so recall@30 and union coverage must be invariant. Only recall@10/15/20/25 and downstream ticket assignment can vary.
- The conditional max_hit/any2+/any3+/any4+ distribution by M is the correct allocation-stage null reference. It prevents candidate misses from being mixed with within-bank allocation failures.
- Under the uniform null, all partitions of the same 30 positions into five disjoint groups of six have the same conditional distribution. Geometry does not create a mathematical advantage by itself.

This changes the audit checklist for the H1250-A/B trace files, but **does not change** any model, weight, candidate family, cutoff, alpha, threshold, bootstrap design, or strict gate.

## 5. Existing source and data status

- Data cutoff remains 1249. The current `lotto_data.csv` Git blob is `d012ac7f2395e70466f0c50b71b949515dea1def`; the preregistered raw-file SHA-256 remains `a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7`. This audit did not recompute the raw CSV SHA-256.
- Historical actual-purchase source inventory remains partial: canonical actual-purchase records for 1247 and 1248 only (10 lines); 1246 remains excluded because two pre-draw five-line sources conflict and no receipt resolves which was purchased.
- No whole-history recommendation/purchase closed loop is claimed.
- Rounds 1244–1249 remain exposed/live-history diagnostics, not untouched holdouts.

## 6. 1250 readiness

The latest saved 2026-11-11 status remains `STRICT_PASS_NOT_READY`, with no validated models and no ready file. No H1250-A/B V2 workflow-dispatch run appears in the latest 100 Actions runs inspected on 2026-11-12. The V2 workflow is manual-dispatch-only. The preregistration, runner, workflow, and dependency hashes are intact; the outer 849-target A/B computation and 7,000-replicate moving-block bootstrap have **not** been executed in this run.

No fallback is promoted. No candidate or final purchase lines were generated. The strict gate is unchanged.

## 7. Next work (in order)

1. Execute the unchanged H1250-A/B V2 runner; preserve all 13 expected outputs and queue status.
2. Audit A/B winner traces against the fixed-bank coverage and recall@30 invariants above; decompose candidate misses from within-bank ticket allocation.
3. Complete the preregistered 7,000-replicate moving-block bootstrap, include the final residual block, verify exact-matched null and Bonferroni bounds, and retain strict FAIL unless every existing condition passes.

## 8. Execution limitation

The H1250-A/B workflow is manual-dispatch-only. The available GitHub connection in this execution can read workflow runs and repository files but does not expose a workflow-dispatch action. The exact null audit was therefore completed locally as an independent supporting study; the 849-target preregistered A/B runner was not represented as executed.
