# E083 — Prequential dynamic ranker selection (2026-11-25)

## Research question
Does selecting among the three frozen candidate rankers using only the preceding 50 target outcomes improve candidate recall, and does that selection translate under one unchanged three-line allocator?

## Execution
- Historical rolling-origin targets: 451–1251 (801); warm-up targets 401–450.
- Each target ranker used only draws through t−1; the selector used only the prior 50 target outcomes.
- Candidate selection and the three-line portfolio allocator were evaluated separately.
- Candidate matched random: 200 sets per target; portfolio geometry-matched random: 120 bundles per target.
- Moving-block bootstrap: 4,000 replicates, block length 50, final one-target remainder retained; Bonferroni alpha 0.0125.
- Rounds 1244–1251 are contaminated live-history diagnostics, not a clean holdout or prospective confirmation.

## Candidate-stage results

| Ranker | Recall@10 | Recall@15 | Recall@20 | Recall@25 | Recall@30 |
|---|---:|---:|---:|---:|---:|
| CONSENSUS | NaN% | NaN% | NaN% | NaN% | 66.750% |
| BORDA | NaN% | NaN% | NaN% | NaN% | 65.980% |
| MIN_RANK | NaN% | NaN% | NaN% | NaN% | 66.750% |
| DYNAMIC | 22.493% | 33.000% | 43.675% | 55.035% | 66.271% |

Dynamic selector primary candidate_recall@30 comparisons:
- vs_consensus: delta -0.479 pp; adjusted CI [-1.332, 0.458] pp.
- vs_borda: delta 0.291 pp; adjusted CI [-0.916, 1.581] pp.
- vs_min_rank: delta -0.479 pp; adjusted CI [-1.540, 0.708] pp.
- vs_exact_uniform: delta -0.395 pp; adjusted CI [-1.873, 1.020] pp.
- Selection counts: {"CONSENSUS":363,"BORDA":149,"MIN_RANK":289}; switches: 71.
- Top-30 misses: 1621 / 4806 winner instances omitted; best-component attribution: {"recent30":568,"gap":117,"momentum":495,"balanced":21,"contrarian":420}.

## Three-line portfolio results

| Metric | Dynamic observed | Exact geometry null | Delta | Adjusted CI |
|---|---:|---:|---:|---:|
| max_hit | 1.489388 | 1.514256 | -0.024868 | [-0.089795, 0.045045] |
| any2 | 0.455680 | 0.474976 | -0.019296 | [-0.066737, 0.025656] |
| any3 | 0.074906 | 0.071355 | 0.003551 | [-0.015175, 0.026023] |
| winning_union_coverage | 2.367041 | 2.400000 | -0.032959 | [-0.136579, 0.059426] |

- Auxiliary any4/5/6 rates and hit distributions are preserved in RESULTS.json.
- Any2-positive 50-target blocks: 6/16 (37.50%); required >=65%. Final one-target remainder retained separately.
- Exact-null probability sum: 1.000000000000.

## Decision
- Historical four-metric gate: FAIL.
- Prospective confirmation: NOT MET / minimum count and completion rule remain unspecified. External nested execution: NOT RUN.
- No strict-pass-ready model, no promotion, and no candidate numbers or purchase lines generated.

## Interpretation
This is a historical prequential selector diagnostic. It can inform whether trailing-performance selection merits a prospective test, but cannot establish a clean holdout result or predictive edge. The fixed three-line allocator was not tuned.

## Historical delivery review
- Target 1251 original pre-draw artifact and existing error note were re-read unchanged. The preserved result records max-hit 1, no any2+/any3+, and union coverage 2/6; purchase confirmation remains NOT_CONFIRMED.
- Target 1249 remains an intermediate display without purchase confirmation. Target 1250 user-visible delivery is unverified; 1247/1248 retain conflicting preserved sets without purchase proof. None enters the confirmed-purchase aggregate.

## Next test
Resolve the prospective minimum-target/completion-rule policy gap through a separately versioned decision. Do not tune E083 on the same historical target range.
