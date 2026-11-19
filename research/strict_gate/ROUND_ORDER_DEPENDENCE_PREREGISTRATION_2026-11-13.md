# Round-order dependence diagnostic — preregistration (2026-11-13)

## Status
FROZEN BEFORE EVALUATION. Retrospective exploratory diagnostic; not a promotion test and not a strict-gate substitute.

## Question
Do consecutive or short-lag Lotto 6/45 draws share more or fewer main numbers than expected if the observed draw rows were exchangeable in time? This tests temporal dependence in the draw sequence, not persistence of number frequencies.

## Frozen data and scope
- Source: repository `lotto_data.csv` on `main`.
- Include every complete chronological main-number row available at execution; exclude bonus numbers.
- Validate unique sequential round IDs, six distinct main numbers per row, values 1..45, and no missing rows.
- Do not use any result beyond the last round present in the source file.
- The analysis is retrospective and may not be described as an untouched prospective validation.

## Statistics
For each lag k = 1..10, calculate the mean overlap:
`O_k = mean_t |D_t intersect D_(t-k)|`.
The independent-uniform reference for a single pair is 6*6/45 = 0.8 shared numbers. The primary family statistic is the maximum absolute standardized departure across the ten lags, with each lag standardized by its own conditional-permutation mean and standard deviation.

## Null and inference
- Conditional null: uniformly permute whole draw rows, leaving each six-number draw intact. This preserves each observed draw's internal structure and the complete-history count of every number while removing chronological order.
- Monte Carlo: 9,999 permutations; deterministic 32-bit LCG seed 2026111302; Fisher-Yates shuffle.
- Family-wise two-sided inference: max-T adjusted p-value across all ten predeclared lags. Use (1 + exceedances)/(1 + permutations).
- Report observed overlap, conditional-null mean/SD, standardized statistic, max-T family p-value, and the unadjusted per-lag tail probabilities as descriptive only.
- No lag selection, alternative split, parameter search, or threshold changes after seeing results.

## Decision rule
A max-T adjusted p <= 0.05 is a signal to design a separate preregistered predictive test; it is not evidence of a usable predictive model and does not authorize ticket promotion. Otherwise, mark this temporal-dependence hypothesis unsupported in this diagnostic. The project's strict portfolio gate remains unchanged.

## Reproducibility
The implementation must validate source integrity, record source file SHA256 and Git blob SHA, record exact row count/cutoff, seed, permutation count, and include a deterministic output manifest. The source preregistration and implementation are append-only.
