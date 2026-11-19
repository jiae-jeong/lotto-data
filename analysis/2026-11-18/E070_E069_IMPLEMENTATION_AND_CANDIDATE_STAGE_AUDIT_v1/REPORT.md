# E070 — E069 implementation conformance and two-stage audit

**Classification:** historical exploratory / post-hoc correction / not prospective confirmation

## 1. Implementation conformance

The E069 preregistration fixed the prior at 6/45 with strength 45:

`(success + 45*(6/45)) / (exposure + 45)`

The executed runner instead uses a number-specific historical frequency prior:

`(success + 45*global_frequency_rate) / (exposure + 45)`

**Formula conformance: FAIL.** The original E069 outputs and verification files are preserved unchanged. The E069 verification PASS checked hashes, cutoff, output counts and geometry, but did not assert that the scoring function matched the registered formula.

## 2. Candidate-selection stage — registered formula

Evaluation: rounds 401–1250 (850 targets), cutoff-safe; exact random expectation is K/45. The 99% moving-block intervals use 4,000 replicates, 50-target blocks and Bonferroni alpha 0.01 across five K values.

| K | Candidate recall | Exact random | Delta | Adjusted CI | Positive blocks |
|---:|---:|---:|---:|---:|---:|
| 10 | 21.608% | 22.222% | -0.614 pp | [-1.850, 0.641] pp | 4/17 |
| 15 | 32.431% | 33.333% | -0.902 pp | [-2.157, 0.373] pp | 5/17 |
| 20 | 44.059% | 44.444% | -0.386 pp | [-1.778, 1.124] pp | 6/17 |
| 25 | 55.294% | 55.556% | -0.261 pp | [-1.556, 0.993] pp | 7/17 |
| 30 | 66.098% | 66.667% | -0.569 pp | [-2.216, 1.157] pp | 6/17 |

All five adjusted intervals include zero. None establishes positive candidate-stage advantage over exact random.

At TOP30, 1,729 winning-number instances were outside the candidate set: 216 were members of the previous draw and 1513 were not. Rank bands 31–35 / 36–40 / 41–45 contained 608 / 562 / 559 misses. Full target-by-target reasons and transition counts are preserved in `MISS_TRACE_TOP30.csv`.

## 3. Portfolio stage — registered formula

The unchanged E045 three-line selector was applied to the registered fixed-prior scores and compared with the exact disjoint-union18 null.

| Metric | Observed | Exact null | Delta | Adjusted CI |
|---|---:|---:|---:|---:|
| max_hits | 1.496471 | 1.514256 | -0.017786 | [-0.076609, 0.042214] |
| any2 | 0.460000 | 0.474976 | -0.014976 | [-0.062035, 0.030906] |
| any3 | 0.072941 | 0.071355 | 0.001586 | [-0.016061, 0.019233] |
| winning_union_coverage | 2.363529 | 2.400000 | -0.036471 | [-0.125882, 0.060000] |

Any2-positive 50-target blocks: 4/17 (23.53%); unchanged requirement: 65%. Historical strict gate: **FAIL**. Any4+ is supplemental only (0.588%).

## 4. Interpretation

- The registered and executed E069 estimators are not the same implementation; E069's original PASS status does not establish estimator conformance.
- The registered-formula candidate recall does not beat exact random at any tested K under the adjusted intervals.
- The registered-formula portfolio fails every strict lower-bound requirement and the any2 block-share requirement.
- This historical sample is already exposed; neither this audit nor the original E069 run is prospective confirmation.
- No thresholds, alpha, block length, selector, or purchase policy were changed. No purchase lines, fallback, freeze, or seal were generated.

## 5. Next actions

1. Preserve E069 unchanged and create a separately versioned corrected runner with a unit test asserting the fixed 6/45 prior.
2. Re-run only as a historical implementation diagnostic; do not call it independent confirmation or promote it.
3. Keep the prospective minimum target count/completion rule unresolved until a separate policy decision. E046's design-only grid reached approximately 80% joint power only at 1,000 targets for a hypothetical 1-SD effect; it did not adopt a rule.
