# H1250 exact conditional-null audit — 2026-11-12

## Research question

Does the frozen exact-null implementation for five disjoint six-number tickets with union size 30 agree with an independent combinatorial derivation, and can the null be decomposed into candidate-bank retention and within-bank allocation?

This is a methodological validation supporting the preregistered H1250-A/B studies. It is not a candidate model test, not a portfolio performance test, and not a strict-gate pass.

## Frozen inputs and scope

- Repository head inspected: \`ddb148e5352eb255c3ae5806be85e95bcfc7b4be\`.
- H1250 target: 1250; training/data cutoff: 1249.
- Preregistration V2 blob: \`bcac96aa1a7db5bfb0f4e973ba7fc14a35f2b417\`.
- H1250 runner blob: \`a7a7d7792c7ba84a1c12699f53d8a3f4009d8a66\`.
- V42 exact-null source blob: \`a4d6bcfcfeea7e40b63bf42f3db1f98a0e4cbe92\`.
- Current workflow blob: \`5bfac63506b9fc2d3f68350eafaa8676fa6a64d3\`, matching the append-only workflow audit.
- All five frozen dependency blob hashes in the V2 preregistration match the current \`main\` tree.
- The canonical draw snapshot remains cutoff 1249; its current Git blob is \`d012ac7f2395e70466f0c50b71b949515dea1def\`. The preregistered file SHA-256 is retained as \`a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7\`; this audit did not recompute the raw CSV SHA-256.
- No H1250-A/B workflow-dispatch run appears in the latest 100 repository Actions runs at inspection time.

## Method

Let \`M\` be the number of winning main numbers retained in a fixed 30-number candidate bank. Under a uniform six-of-45 draw:

\`M ~ Hypergeometric(N=45, K=30, n=6)\`.

Conditional on \`M=m\`, the \`m\` winning positions are uniformly distributed over the 30 bank positions. For five disjoint six-number tickets partitioning the bank, the five ticket hit counts follow the exact multivariate-hypergeometric allocation induced by a uniformly chosen \`m\`-subset of 30 positions.

The independent implementation enumerates all five-part compositions of \`m\` with each ticket capacity six, weighted by \`product(comb(6, h_i))\`. It separately transcribes the frozen V42 mask-DP exact-null implementation and compares exact rational values. A seeded Monte Carlo check uses 100,000 random partitions for each \`m=0..6\` (700,000 total).

## Main results

### Candidate-stage null

- Expected winners retained in a random top30 bank: **4.000000 / 6**.
- Expected recall@30: **66.6667%**.
- \`P(M <= 2)\`: **8.4575%**.
- \`P(M >= 3)\`: **91.5425%**.
- \`P(M >= 4)\`: **68.8625%**.

### Unconditional exact five-line null

| Metric | Exact expectation |
|---|---:|
| \`E[max_hit]\` | **1.834653** |
| \`P(any2+)\` | **70.9476%** |
| \`P(any3+)\` | **11.8679%** |
| \`P(any4+)\` | **0.6967%** |
| \`E[winning_union_coverage]\` | **4.000000** |

Exact rational forms are retained in \`RESULTS.json\`.

### Conditional allocator null by candidate-bank hit count

| Winners retained \`m\` | \`E[max_hit]\` | \`P(any2+)\` | \`P(any3+)\` | \`P(any4+)\` | Union coverage |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.0000 | 0.0000% | 0.0000% | 0.0000% | 0 |
| 1 | 1.0000 | 0.0000% | 0.0000% | 0.0000% | 1 |
| 2 | 1.1724 | 17.2414% | 0.0000% | 0.0000% | 2 |
| 3 | 1.4926 | 46.7980% | 2.4631% | 0.0000% | 3 |
| 4 | 1.8566 | 76.3547% | 9.0312% | 0.2737% | 4 |
| 5 | 2.1650 | 94.5434% | 20.6518% | 1.2842% | 5 |
| 6 | 2.4075 | 100.0000% | 37.0216% | 3.6083% | 6 |

### Implementation verification

- Independent exact composition enumeration and frozen V42 mask-DP implementation match exactly as rational numbers.
- Maximum absolute numerical difference: **0.0**.
- Conditional Monte Carlo: 100,000 draws per \`m\`, 700,000 total; largest absolute discrepancy from exact conditional values: **0.0016903**.
- All assertions passed.

## New decomposition rules for H1250-A/B trace review

1. \`winning_union_coverage\` equals \`M\`, the count of winning numbers in the fixed top30 bank. Once the candidate bank is fixed, changing the allocator cannot change union coverage.
2. H1250-A holds the candidate bank fixed. Therefore all four allocator geometries must have identical per-target union coverage. A difference indicates an implementation or trace-mapping defect.
3. H1250-B rankers reorder the same top30 membership. Therefore recall@30 and union coverage must be invariant across rankers. Only recall@10/15/20/25 and downstream line allocation can change.
4. The conditional \`max_hit\`/\`any2+\`/\`any3+\`/\`any4+\` distribution is the allocation-stage reference conditional on \`M=m\`. It prevents candidate misses from being conflated with within-bank ticket dispersion.
5. Under the uniform null, every partition of the same 30 positions into five disjoint groups of six has the same conditional distribution. A historical allocator difference is an empirical signal to test, not a mathematical advantage guaranteed by geometry.

## Interpretation and status

The V42 exact disjoint30 null implementation is independently verified. The new conditional table gives a clean accounting boundary between candidate recall and within-bank allocation.

This does **not** establish that any candidate signal or allocator beats the lottery null. It does not replace the preregistered 849-target nested walk-forward, matched candidate-bank partitions, 7,000-replicate moving-block bootstrap, Bonferroni-adjusted strict gate, or residual-block requirement.

No model, weight, threshold, alpha, candidate family, allocator, cutoff, or strict gate was changed. No candidate numbers or purchase lines were generated. Rounds 1244–1249 remain exposed/live-history diagnostics, not untouched holdouts.

## Remaining work

- Execute the unchanged H1250-A/B V2 runner and preserve all 13 manifested outputs.
- Audit every A/B trace against the invariants above.
- Complete the preregistered moving-block bootstrap and strict-gate audit.
- Freeze/seal only if the unchanged strict gate passes; otherwise retain \`STRICT_PASS_NOT_READY\`.
