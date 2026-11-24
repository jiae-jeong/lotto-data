# Daily Lotto Research — 2026-11-25

## NEW STUDY — E083 prequential dynamic ranker selection

A single dynamic selector was preregistered before evaluation. At each target, it selected among the existing consensus, Borda, and minimum-component-rank rankers using only each ranker's candidate_recall@30 over the preceding 50 target rounds. The target outcome was excluded from selection. The chosen ranking's top 18 were passed through one unchanged allocator: three consecutive disjoint six-number lines.

- Warm-up: targets 401–450. Outer rolling-origin evaluation: targets 451–1251 (801).
- Candidate stage: recall@10/15/20/25/30; primary metric recall@30.
- Portfolio stage: max-hit, any2/3/4/5/6, winning-union coverage, line-hit distributions.
- Candidate random: 200 sets per target. Portfolio exact-geometry matched random: 120 bundles per target.
- Moving-block bootstrap: 4,000 replicates, block length 50, final one-target remainder retained; Bonferroni alpha 0.0125.
- Source integrity: 1,251 contiguous rows, recomputed SHA-256 and Git blob SHA-1 matched the frozen source. Cutoff violations: 0; invalid three-line geometries: 0.

### Candidate stage

| Ranker | Recall@10 | Recall@15 | Recall@20 | Recall@25 | Recall@30 |
|---|---:|---:|---:|---:|---:|
| CONSENSUS | NaN% | NaN% | NaN% | NaN% | 66.750% |
| BORDA | NaN% | NaN% | NaN% | NaN% | 65.980% |
| MIN_RANK | NaN% | NaN% | NaN% | NaN% | 66.750% |
| DYNAMIC | 22.493% | 33.000% | 43.675% | 55.035% | 66.271% |

Dynamic selector primary recall@30 comparisons:
- vs_consensus: -0.479 pp; adjusted CI [-1.332, 0.458] pp.
- vs_borda: 0.291 pp; adjusted CI [-0.916, 1.581] pp.
- vs_min_rank: -0.479 pp; adjusted CI [-1.540, 0.708] pp.
- vs_exact_uniform: -0.395 pp; adjusted CI [-1.873, 1.020] pp.

Selection counts: {"CONSENSUS":363,"BORDA":149,"MIN_RANK":289}; switches: 71. Top-30 miss trace: 1621 of 4806 winner instances omitted; best-component attribution: {"recent30":568,"gap":117,"momentum":495,"balanced":21,"contrarian":420} (rank attribution, not causal proof).

### Three-line portfolio stage

| Metric | Dynamic observed | Exact geometry null | Delta | Adjusted CI |
|---|---:|---:|---:|---:|
| max_hit | 1.489388 | 1.514256 | -0.024868 | [-0.089795, 0.045045] |
| any2 | 0.455680 | 0.474976 | -0.019296 | [-0.066737, 0.025656] |
| any3 | 0.074906 | 0.071355 | 0.003551 | [-0.015175, 0.026023] |
| winning_union_coverage | 2.367041 | 2.400000 | -0.032959 | [-0.136579, 0.059426] |

Any2-positive non-overlapping 50-target blocks: 6/16 (37.50%); required >=65%. Final one-target remainder retained separately. Auxiliary any4/5/6 and full distributions are in RESULTS.json.

### Decision

Historical four-metric gate: FAIL. Prospective confirmation remains unevaluated because the minimum target count and completion rule are still unspecified. External nested execution was not run. Therefore no strict-pass-ready model, no model/allocator promotion, no freeze/seal, no candidate output, and no purchase lines.

## MAINTENANCE / RECHECK — delivery and error-note provenance

The original target-1251 pre-draw artifact and its error note were re-read unchanged and matched by stored SHA. The post-draw note records line-hit distribution 1/1/0, max-hit 1, no any2+/any3+, and union coverage 2/6; purchase confirmation remains NOT_CONFIRMED. Target 1249 remains an intermediate display without purchase confirmation; target 1250's visible-delivery assertion is unverified; targets 1247/1248 retain conflicting preserved sets without purchase proof. No prior record was reconstructed or promoted into the actual-purchase aggregate.

## NEXT TEST

Resolve the prospective minimum-target/completion-rule policy gap through a separately versioned decision. Do not tune E083 on the same historical target range. Preserve the 1252 three-line strict gate unchanged.
