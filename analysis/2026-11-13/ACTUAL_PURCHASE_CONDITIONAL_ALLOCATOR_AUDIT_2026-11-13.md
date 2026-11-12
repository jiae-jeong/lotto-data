# Actual-purchase conditional allocator audit — 2026-11-13

## Research question

For the two canonical actual-purchase five-line portfolios preserved in GitHub, separate:
1. winning numbers absent from the portfolio's unique-number union; and
2. winning numbers retained in that union but not concentrated in one line.

This is a new exact conditional failure-decomposition study. It is not a new predictive model, not a strict-gate pass, and not an untouched-holdout evaluation.

## Original-source recovery

- Prior ChatGPT conversation search did not recover authenticated pre-draw final purchase lines or original post-draw error-note text. The retrieved conversation records state that 1245 final purchase lines were not generated.
- GitHub provides canonical actual-purchase records for 1247 and 1248:
  - `research/weekly_purchase/1247/ACTUAL_PURCHASE_FIVE_LINES_1247_20261023_RESEARCH_V8.json`
  - `research/weekly_purchase/1248/ACTUAL_PURCHASE_FIVE_LINES_1248_20261030_FALLBACK_V1.json`
- 1246 remains excluded: two distinct pre-draw five-line sources exist and no receipt resolves which set was purchased.
- For 1248, the separate V54 FINAL artifact is not substituted for the canonical ACTUAL_PURCHASE fallback record.
- Whole-history actual-purchase provenance remains incomplete.

## Data and cutoff integrity

- Canonical data cutoff: 1249; latest draw date: 2026-11-07.
- `lotto_data.csv`: 1,249 contiguous draw rows after blank-line filtering; six unique main numbers in 1–45 and bonus in 1–45 for every row.
- Git blob SHA: `d012ac7f2395e70466f0c50b71b949515dea1def`.
- Independently recomputed raw SHA-256: `a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7`, exactly matching the H1250 preregistered SHA-256.
- The 1249 result in the repository agrees with two independent public result aggregators: [jottto](https://jottto.com/lotto/1249) and [freetto](https://freetto.io/lotto/1249). The dynamic round-specific Donghaeng result endpoint was not directly returned by the web lookup, so this is not represented as a direct official-page confirmation.

## Exact method

For each canonical five-line actual-purchase portfolio:

- Let (U) be the number of unique numbers across all five lines.
- Let (M) be the number of the six winning main numbers contained in that union.
- Candidate/union stage: compute (M/6) and the exact fixed-(U) draw null (X\sim\operatorname{Hypergeometric}(45,U,6)).
- Allocator stage: conditional on the observed (M), enumerate all (inom{U}{M}) equally likely subsets of the fixed union. For every subset, calculate the five line-hit counts, `max_hit`, `any2+`, `any3+`, `any4+`, total winning-number appearances and duplicated winning-number appearances.

This conditional allocator null is specific to the observed overlapping ticket geometry. It is not the primary H1250 strict null and does not establish predictive edge.

## Results

| Target | Unique union (U) | Winners retained (M/6) | Missed | Line-hit distribution | max_hit | any2+ | any3+ | any4+ | Duplicate winning appearances | (M-max\_hit) |
|---|---:|---:|---:|---|---:|---|---|---|---:|---:|
| 1247 | 16 | 3/6 (50.0%) | 3 | 2, 1, 2, 1, 1 | 2 | Yes | No | 4 | 1 |
| 1248 | 18 | 5/6 (83.3%) | 1 | 3, 1, 2, 1, 1 | 3 | Yes | Yes | 3 | 2 |

### Candidate/union-stage exact null

- 1247: expected retained winners (32/15=2.1333); exact (P(X\ge3)=632/1763=35.8480\%\).
- 1248: expected retained winners (12/5=2.4000); exact (P(X\ge5)=595/19393=3.0681\%\).

The 1248 one-round tail is descriptive only. It is one exposed historical observation, selected after a model process, and is not a confirmatory p-value or evidence of a repeatable edge.

### Allocator-stage exact conditional null

| Metric | 1247: (U=16,M=3), 560 subsets | 1248: (U=18,M=5), 8,568 subsets |
|---|---:|---:|
| (E[max\_hit]) | 2.0411 | 2.7875 |
| (P(any2+)) | 88.2143% | 100.0000% |
| (P(any3+)) | 15.8929% | 67.7521% |
| (P(any4+)) | 0.0000% | 10.6443% |
| (E[winning\_appearances]) | 5.6250 | 8.3333 |
| (P(appearances\ge observed)) | 28.3929% | 72.8758% |
| (P(max\_hit\ge observed)) | 88.2143% | 67.7521% |

The observed allocator outcomes are ordinary under the exact conditional distributions:
- 1247's observed max-hit of 2 is common when three winners are retained in that 16-number union.
- 1248's observed max-hit of 3 is also common when five winners are retained in that 18-number union.

## New finding and interpretation

The two canonical actual-purchase portfolios used only 16 and 18 unique numbers across 30 ticket positions. Across the two rounds, 8 of 12 winning-number instances were retained in the portfolio unions; four were absent. Seven winning-number appearances were duplicated across multiple lines.

Once the number of retained winners is held fixed, neither round shows an unusual max-hit or allocation-gap result under the exact conditional allocator null. The observable shortfall is therefore more directly associated with the small unique-number union / candidate retention stage than with an allocator that failed to concentrate retained winners. This is a descriptive diagnosis of two rounds only; it does not prove that a broader or less-overlapping portfolio will outperform.

## Candidate-recall and 1250 readiness context (prior results, not recalculated today)

The 2026-11-12 candidate-recall scorecard covers 1,049 cutoff-safe targets (201–1249) and 209,800 matched random sets. Its best mean recall deltas versus random were small:
- K=10: +0.00552
- K=15: +0.00553
- K=20: +0.00327
- K=25: +0.00192
- K=30: +0.00405

The best K=25 and K=30 signals had negative 3+-capture deltas versus random in the same scorecard. These prior values are not today's new calculation and do not establish simultaneous robust tail improvement.

The latest 1250 model gate remains `STRICT_PASS_NOT_READY`: zero validated models, no ready file, and failures in max-hit, any2, any3, winning-union-coverage and any2 block stability. The preregistered H1250-A/B V2 outer 849-target runner and its 7,000-replicate moving-block bootstrap remain unexecuted. The workflow is manual-dispatch-only and no matching run appears in the latest 100 Actions runs inspected. No fallback was promoted and no final purchase lines were generated.

## Limits and next tests

1. Do not generalize from two exposed rounds or treat 1244–1249 as untouched holdouts.
2. If the unchanged H1250-A/B V2 runner can be executed, preserve its preregistered code, cutoff, candidate/allocator definitions, random seed, null, block design and strict gate without post-hoc changes. If executed after the 1250 draw, it remains a retrospective 401–1249 study, not prospective validation for 1250.
3. For the next prospective target, freeze model, candidate ranking, allocator, thresholds, code/data hashes and final artifact before the draw. Evaluate the future result only after the freeze; do not tune on it.

No candidate numbers or purchase combinations are included in this report.
