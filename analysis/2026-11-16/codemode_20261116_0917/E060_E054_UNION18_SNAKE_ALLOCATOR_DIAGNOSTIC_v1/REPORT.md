# E060 - E054 frozen-union18 allocator partition diagnostic

Status: COMPLETE; historical allocator-only sensitivity diagnostic, not an independent predictive model and not purchase evidence.

- Cutoff 1250; targets 401-1250 (850).
- Candidate union18 is frozen from E054 predictions and is identical for both partitions.
- Compared the original E054 three-line partition with one fixed numeric-order snake partition; no model, candidate, weight, or parameter search.
- Random baseline: 120 exact-geometry disjoint-union18 portfolios per target (102,000 total).
- Inference: four unchanged strict metrics, 4,000 moving-block bootstrap replicates, 50-target blocks, 17 blocks.

## Results

### E054

| Metric | Observed | Exact null | Delta | Adjusted CI | Positive blocks |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.477647 | 1.514256 | -0.036609 | [-0.088374, 0.023391] | 5/17 |
| any2 | 0.458824 | 0.474976 | -0.016153 | [-0.056153, 0.030906] | 6/17 |
| any3 | 0.062353 | 0.071355 | -0.009002 | [-0.026649, 0.008645] | 7/17 |
| winning_union_coverage | 2.351765 | 2.400000 | -0.048235 | [-0.152941, 0.054118] | 6/17 |

Historical gate diagnostic: FAIL (not eligible for readiness or promotion).

### NUMERIC_SNAKE

| Metric | Observed | Exact null | Delta | Adjusted CI | Positive blocks |
|---|---:|---:|---:|---:|---:|
| max_hits | 1.482353 | 1.514256 | -0.031903 | [-0.087197, 0.025744] | 7/17 |
| any2 | 0.462353 | 0.474976 | -0.012623 | [-0.045564, 0.025024] | 9/17 |
| any3 | 0.063529 | 0.071355 | -0.007825 | [-0.027825, 0.013351] | 7/17 |
| winning_union_coverage | 2.351765 | 2.400000 | -0.048235 | [-0.147059, 0.052941] | 6/17 |

Historical gate diagnostic: FAIL (not eligible for readiness or promotion).

Union coverage is identical by construction because the 18-number candidate set is unchanged.

No candidate numbers are promoted. No STRICT_PASS_READY, purchase lines, freeze, or seal are generated.

The historical targets are already inspected/live-history material, not prospective confirmation.
