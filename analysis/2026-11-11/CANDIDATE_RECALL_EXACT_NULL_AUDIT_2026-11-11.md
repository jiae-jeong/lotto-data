# Candidate-recall exact-null audit — 2026-11-11

## 1. Research question

Across the six frozen candidate-ranking signals and five candidate cut sizes, is the observed candidate-stage recall meaningfully above the exact uniform 6/45 null? This audit is separate from five-line allocation and does not promote a model.

## 2. Data and provenance

- Source: `lotto_data.csv`; SHA-256 **a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7**.
- Independently parsed 1,249 nonblank draw rows, rounds 1–1,249. One blank CSV line after round 1,245 was ignored as a blank record; there is no round gap after parsing.
- Validation: sequential round IDs; six unique main numbers in 1–45; bonus in 1–45 and not duplicated among the six main numbers. **PASS**.
- Candidate scorecard: `analysis/2026-11-11/CANDIDATE_RECALL_SCORECARD.csv` (Git blob `8f4dba490b783970bfa65ac270c66f2c442a9826`); 1,049 targets (201–1,249), K={10,15,20,25,30}, six signals, 200 matched random candidate sets per target (209,800 total); source status marks no future leakage.
- All historical targets, including 1,244–1,249, are retrospective/live-history diagnostics. None is described as an untouched holdout.

## 3. Exact-null method

For a fixed K-number candidate set and a fair 6/45 draw, the number of winning main numbers retained is
`X ~ Hypergeometric(N=45, M=K, n=6)`.

- Expected hits: `6K/45`.
- Variance: `6(K/45)(1-K/45)(39/44)`.
- `capture 3+` and `capture 4+`: exact hypergeometric tail probabilities, followed by exact one-sided Binomial upper-tail tests over 1,049 targets.
- Mean recall: one-sided normal approximation using the exact per-target hypergeometric variance.
- Family: 6 signals × 5 K values × 3 endpoints = 90 comparisons; Bonferroni per-test alpha = **0.0005556**.
- Bootstrap CI was not computed because the published scorecard contains aggregate summaries rather than target-level resampling rows. No CI is fabricated.

## 4. Candidate-stage results

The following are the *best descriptive signal per K after looking at the same 1,049 targets*; they are not eligible for champion selection.

| K | Best mean-recall signal | Mean hits vs exact null | Recall delta | One-sided p (normal approx) | Best 3+ signal | 3+ delta | Exact p |
|---:|---|---:|---:|---:|---|---:|---:|
| 10 | balanced | 1.3642 vs 1.3333 | 0.514 pp | 0.149 | momentum | 1.201 pp | 0.120 |
| 15 | consensus | 2.0305 vs 2.0000 | 0.508 pp | 0.182 | consensus | 2.800 pp | 0.028 |
| 20 | recent30 | 2.6854 vs 2.6667 | 0.312 pp | 0.298 | recent30 | 1.450 pp | 0.181 |
| 25 | consensus | 3.3432 vs 3.3333 | 0.164 pp | 0.390 | recent30 | -0.276 pp | 0.601 |
| 30 | recent30 | 4.0229 vs 4.0000 | 0.381 pp | 0.248 | contrarian | 0.069 pp | 0.496 |

Across all 30 signal/K pairs:
- No mean-recall, 3+, or 4+ comparison survives the 90-test Bonferroni family.
- Minimum unadjusted p-values: mean recall **0.1489**, 3+ **0.0278**, 4+ **0.0283**.
- The largest descriptive 3+ excess is consensus@15 (**+2.800 pp**, exact p=0.0278); the largest 4+ excess is balanced@10 (**+0.834 pp**, exact p=0.0283). Neither is close to the adjusted threshold.
- K=30 recent30 has a small positive mean-recall delta (+0.381 pp) but its 3+ capture rate is below the exact null (−0.503 pp). The metrics do not show a consistent tail improvement.

**Candidate-stage verdict: no statistically supported recall champion.** The scorecard's small positive differences are not enough to promote a signal.

## 5. Portfolio-stage separation

The 849-target V9 five-role policy is not a strict pass. Against its geometry-preserving matched label-permutation comparator:

- max-hit delta: **−0.01218**; adjusted CI [−0.07993, +0.06556].
- any2 delta: **−0.00129**; adjusted CI [−0.03330, +0.03223].
- any3 delta: **−0.00872**; adjusted CI [−0.03581, +0.02106].
- winning-union-coverage delta: **−0.04381**; adjusted CI [−0.11507, +0.03282].
- any4 delta is +0.00279, but it is supplementary and does not rescue the failed primary gates.
- Positive 50-target block shares: max-hit 0.294, any2 0.471, any3 0.412, union coverage 0.412; each is below the required 0.65 where applicable.

### Prior V54/V83/V84/V85/V86 failure audit

All five used the same V38/V28 hybrid top30 candidate-generator family and 30-unique-number geometry. Their adjusted lower bounds and final 48-target residual any2 deltas are:

| Version | max-hit CI lower | any2 CI lower | any3 CI lower | union-coverage CI lower | any2 positive-block share | final 48-target any2 delta |
|---|---:|---:|---:|---:|---:|---:|
| V54 | 0.016058 | -0.000945 | 0.002497 | -0.000000 | 0.824 | -0.105309 |
| V83 | 0.010134 | 0.001925 | -0.005204 | -0.000000 | 0.824 | -0.105309 |
| V84 | 0.000655 | -0.012794 | 0.000706 | -0.000000 | 0.765 | -0.105309 |
| V85 | -0.002510 | -0.014901 | 0.003674 | -0.000000 | 0.765 | -0.105309 |
| V86 | -0.004866 | -0.004287 | -0.007830 | 0.001182 | 0.647 | -0.021976 |

The common top30 membership makes recall@30 invariant across tail-order variants; the policies can still change within-top30 ordering and ticket allocation. The summaries do **not** contain target-level winner-rank/line-assignment traces, so the final 48-target loss cannot yet be causally split into missed candidates versus within-bank allocation failures. H1250-A (fixed bank, varying allocator) and H1250-B (fixed allocator, varying tail ranking) remain the correct preregistered separation tests.

## 6. Actual-purchase closed loop

Canonical actual-purchase records were found for only two rounds: 1247 and 1248 (10 lines total). Their combined hit distribution is 0-hit:0, 1-hit:6, 2-hit:3, 3-hit:1, 4+-hit:0; mean 1.5 hits/line, 2+ rate 0.40, 3+ rate 0.10. This is a two-round descriptive audit, not a performance estimate.

Round 1246 remains excluded: two distinct pre-draw five-line sets exist and no receipt establishes which was purchased. Whole-history recommendation/purchase provenance is incomplete; no missing historical lines or failure reasons were reconstructed.

## 7. H1250-A/B execution state

- V2 preregistration remains frozen at cutoff 1,249; implementation hash `a7a7d7792c7ba84a1c12699f53d8a3f4009d8a66`; the workflow integrity audit preserves the amended workflow hash.
- No H1250 v2 workflow-dispatch run was found in the repository's Actions run list. The workflow is manual-dispatch-only; this run had no GitHub workflow-dispatch action, so the A/B outer computation and its 7000-replicate moving-block bootstrap were **not** executed here.
- No threshold, alpha, candidate family, cutoff, or model weight was changed. Strict gate remains **FAIL / NOT READY**; no fallback is promoted.

## 8. Next registered work

1. Execute unchanged H1250-A/B V2 from its manual workflow dispatch and preserve all 13 manifested outputs plus the queue update.
2. Independently verify the 849-target traces, residual 49-target block, exact disjoint-30 null, and Bonferroni/block-bootstrap calculations.
3. Use the A/B winner traces to decompose candidate-stage misses from within-bank ticket-allocation misses; do not alter the strict gate after seeing outer results.

## 9. Reproducibility and limits

Full machine-readable values for all 30 signal/K pairs, exact null probabilities, p-values, source hashes, V9 metrics, and V54–V86 failure summaries are in the adjacent JSON file. This is an analytical exact-null audit of the aggregate candidate-recall scorecard, not a replacement for the preregistered H1250-A/B nested experiment.
