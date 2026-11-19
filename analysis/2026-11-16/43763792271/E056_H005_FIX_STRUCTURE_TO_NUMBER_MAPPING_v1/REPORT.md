# H005_FIX — Structure-to-number mapping repair

- Scope: separate corrected implementation; legacy S008 source and historical outputs are untouched.
- Data: 1..1250; expanding walk-forward targets 201..1250 (1050 predictions); each target trains only on 1..t-1.
- Candidate bank: seed 20261008, 5000 fixed six-number tickets; SHA256 134724abb3f8930fbb3cf24499e537aa00ed9e49239dbb79029163d76a412220
- Legacy S008 algebra: 45 structure vectors (six constant 45-vectors and 39 zero-vectors) yield a constant 270/51 contribution for every number.
- Corrected H005_FIX: one 45-dimensional vector, 45 for the six S005 structure-ticket members and 0 for the other 39, appended once to six component rank vectors; seven-family mean.
- Legacy algebra checks: 1050; corrected mapping changed top-six ticket in 932 targets.
- Random baseline: exact six-of-45 hypergeometric distribution; no Monte Carlo approximation.
- This is a historical diagnostic, not a three-line portfolio or purchase recommendation.

| Model | Window | n | Mean hits | 2+ | 3+ | 4+ | Δ mean vs exact random |
|---|---|---:|---:|---:|---:|---:|---:|
| H005_FIX | overall_201_1250 | 1050 | 0.8124 | 18.76% | 2.48% | 0.10% | +0.0124 |
| H005_FIX | recent200 | 200 | 0.7850 | 17.50% | 3.00% | 0.00% | -0.0150 |
| H005_FIX | recent100 | 100 | 0.7000 | 16.00% | 1.00% | 0.00% | -0.1000 |
| H005_FIX | recent50 | 50 | 0.6200 | 16.00% | 2.00% | 0.00% | -0.1800 |
| H005_FIX | block_201_500 | 300 | 0.8600 | 20.33% | 1.67% | 0.00% | +0.0600 |
| H005_FIX | block_501_800 | 300 | 0.8000 | 19.67% | 2.67% | 0.00% | +0.0000 |
| H005_FIX | block_801_1100 | 300 | 0.7900 | 16.67% | 3.00% | 0.33% | -0.0100 |
| H005_FIX | block_1101_1250 | 150 | 0.7867 | 18.00% | 2.67% | 0.00% | -0.0133 |
| LEGACY_S008_REFERENCE | overall_201_1250 | 1050 | 0.8133 | 18.67% | 2.29% | 0.00% | +0.0133 |
| LEGACY_S008_REFERENCE | recent200 | 200 | 0.7900 | 18.00% | 3.00% | 0.00% | -0.0100 |
| LEGACY_S008_REFERENCE | recent100 | 100 | 0.8200 | 20.00% | 2.00% | 0.00% | +0.0200 |
| LEGACY_S008_REFERENCE | recent50 | 50 | 0.7800 | 22.00% | 0.00% | 0.00% | -0.0200 |
| LEGACY_S008_REFERENCE | block_201_500 | 300 | 0.8400 | 18.00% | 2.00% | 0.00% | +0.0400 |
| LEGACY_S008_REFERENCE | block_501_800 | 300 | 0.8133 | 22.00% | 1.67% | 0.00% | +0.0133 |
| LEGACY_S008_REFERENCE | block_801_1100 | 300 | 0.7767 | 15.33% | 2.67% | 0.00% | -0.0233 |
| LEGACY_S008_REFERENCE | block_1101_1250 | 150 | 0.8333 | 20.00% | 3.33% | 0.00% | +0.0333 |
| S005_STRUCTURE_TICKET | overall_201_1250 | 1050 | 0.7752 | 17.33% | 3.43% | 0.00% | -0.0248 |
| S005_STRUCTURE_TICKET | recent200 | 200 | 0.7100 | 17.50% | 3.00% | 0.00% | -0.0900 |
| S005_STRUCTURE_TICKET | recent100 | 100 | 0.6700 | 15.00% | 5.00% | 0.00% | -0.1300 |
| S005_STRUCTURE_TICKET | recent50 | 50 | 0.6000 | 16.00% | 4.00% | 0.00% | -0.2000 |
| S005_STRUCTURE_TICKET | block_201_500 | 300 | 0.8633 | 20.00% | 5.33% | 0.00% | +0.0633 |
| S005_STRUCTURE_TICKET | block_501_800 | 300 | 0.7300 | 14.33% | 2.00% | 0.00% | -0.0700 |
| S005_STRUCTURE_TICKET | block_801_1100 | 300 | 0.7600 | 17.67% | 2.67% | 0.00% | -0.0400 |
| S005_STRUCTURE_TICKET | block_1101_1250 | 150 | 0.7200 | 17.33% | 4.00% | 0.00% | -0.0800 |

## H005_FIX overall result

- Overall mean-hit delta vs exact random: +0.012381
- Recent100 mean-hit delta: -0.100000
- Recent50 mean-hit delta: -0.180000
- Historical classification: **WEAK**
- No promotion, no prospective readiness, no strict PASS, and no purchase numbers generated.

The correction is frozen and evaluated as a separate H005_FIX implementation. It does not rewrite or rename legacy S008. The corrected structure vector is number-specific; the legacy S008 contribution is algebraically constant.
