# E051 candidate-stage decomposition — 2026-11-15

**Classification:** POST-RUN EXPLORATORY DIAGNOSTIC — NOT CONFIRMATORY  
**Parent study:** E051 three-line pair-context conditional model  
**Historical cutoff:** 1250  
**Targets:** 401–1250 (850 targets)  
**Result:** candidate recall is essentially at the exact uniform baseline; no promotion.

## 1. What was newly tested

The parent E051 report evaluated the complete three-line portfolio. This diagnostic separates its candidate-ranking stage from the line-allocation stage. It independently recomputes all 45 pair-context scores at each target using only data through target−1, then measures `candidate_recall@10/15/20/25/30`.

A fixed `recent30` ranker from `automation/candidate_recall_v1.py` is the stable signal baseline. The random candidate baseline is exact: a uniformly chosen K-subset has expected (6K/45) winning numbers and recall (K/45).

## 2. Candidate recall results

| K | Pair-context hits | Pair recall | Recent30 recall | Exact random recall | Pair − random |
|---:|---:|---:|---:|---:|---:|
| 10 | 1.342353 | 22.3725% | 22.0196% | 22.2222% | +0.1503 pp |
| 15 | 1.982353 | 33.0392% | 33.1176% | 33.3333% | −0.2941 pp |
| 20 | 2.656471 | 44.2745% | 44.1765% | 44.4444% | −0.1699 pp |
| 25 | 3.311765 | 55.1961% | 54.8627% | 55.5556% | −0.3595 pp |
| 30 | 3.972941 | 66.2157% | 66.2941% | 66.6667% | −0.4510 pp |

The pair-context ranker is only marginally above random at K=10. It is below random at K=15/20/25/30. Its differences from recent30 are tiny and change sign. The other fixed candidate signals (gap, momentum, balanced, contrarian, consensus) also have mixed signs across K; none is above the exact random expectation at all five K values.

## 3. Block stability

Across 17 consecutive 50-target blocks:

| K | Pair-context blocks above random | Pair-context blocks above recent30 |
|---:|---:|---:|
| 10 | 11/17 | 8/17 |
| 15 | 7/17 | 7/17 |
| 20 | 5/17 | 7/17 |
| 25 | 8/17 | 8/17 |
| 30 | 6/17 | 8/17 |

This is descriptive block stability only. No candidate-stage significance or promotion threshold was preregistered for this post-run diagnostic.

## 4. Candidate set versus portfolio union

Across 850 targets there are 5,100 winning-number slots.

- Pair-context top18 ranking captured 2,039 slots (39.9804%); the exact uniform expectation is 2,040 (40.0000%).
- The actual three-line union captured 2,024 slots (39.6863%), matching the parent report's mean union coverage of 2.381176.
- 259 winning slots were inside top18 but not selected in the final line union.
- 244 winning slots were selected by the allocator from outside top18.
- The top18/selected-union intersection captured 1,780 slots; 3,061 slots were outside top18.

The allocator is not a strict subset of the top18 ranking: its role-specific candidate pools can introduce numbers outside top18. Therefore these counts diagnose membership changes but do not provide a causal, additive attribution of every miss to one stage.

## 5. Parent E051 portfolio gate

| Metric | Model | Exact geometry-matched null | Delta | Adjusted moving-block CI |
|---|---:|---:|---:|---:|
| max-hit | 1.498824 | 1.514256 | −0.015433 | [−0.076609, +0.056332] |
| any2+ | 0.465882 | 0.474976 | −0.009094 | [−0.043212, +0.035612] |
| any3+ | 0.069412 | 0.071355 | −0.001943 | [−0.020767, +0.015704] |
| union coverage | 2.381176 | 2.400000 | −0.018824 | [−0.136471, +0.109412] |

Any2-positive 50-target block share was 7/17 (41.18%), below the unchanged 65% requirement. E051 remains **STRICT_FAIL**. No final lines or freeze/seal were generated.

## 6. Reproduction and leakage audit

- Canonical source rows: 1,250; targets: 850.
- Target cutoff violations: 0.
- Actual-outcome mismatches against the canonical CSV: 0.
- Parent top18 set reproduced: 850/850.
- One order-only mismatch at target 472 swaps ranks 12 and 13; the top18 set is unchanged.
- Parent E051 verification: 102,000 matched random bundles; zero training-cutoff violations, leakage failures, or portfolio-geometry violations.
- The E051 source/data hashes are recorded in the companion JSON.

This is historical rolling diagnostics, not a clean holdout. Targets 1244–1249 remain exposed live-history rounds; no retrospective result here is used as prospective confirmation.

## 7. Effect on research direction

The pair-context candidate ranker does not show a stable candidate-recall edge against exact uniform or recent30. The parent portfolio also fails all four adjusted-CI gates and the any2 block-stability gate. Do not tune pair-context smoothing or allocator weights on these same targets.

Next: keep E051 failed; pre-register a distinct candidate-recall experiment under a fixed three-line allocator, and do not declare prospective readiness until the minimum target count and completion rule are formally specified.

