# 2026-11-19 E075 publication-recovery addendum

## E075 — E045 selector-order implementation-conformance correction

**Classification: historical implementation-conformance correction only. Not an independent signal, independent sample, clean holdout, or prospective confirmation.**

### Execution and integrity

- Recovery workflow run: [44430718493](https://github.com/jiae-jeong/lotto-data/actions/runs/44430718493)
- Data cutoff: 1250; data SHA-256: `7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2`
- Walk-forward targets: 401–1250 (850)
- Matched random bundles: 102,000 per version
- Candidate-pool comparisons: 3150; ranking rule identical: True
- First-role pool mismatches: 0; downstream pool-content differences: 7
- Legacy score-order adjacency mismatches: 1229
- Targets with changed line assignments: 5; changed line assignments: 10
- Leakage failures: 0; training-cutoff violations: 0; future predictions: 0
- Portfolio geometry violations: 0; random geometry violations: 0
- Output manifest: PASS (8/8 files)

### Historical metrics

| Metric | Legacy delta vs exact null | Corrected delta vs exact null | Corrected minus legacy | Paired moving-block CI |
|---|---:|---:|---:|---:|
| max_hits | -0.022492 | -0.022492 | 0.000000 | [0.000000, 0.000000] |
| any2 | -0.007917 | -0.007917 | 0.000000 | [0.000000, 0.000000] |
| any3 | -0.012531 | -0.012531 | 0.000000 | [0.000000, 0.000000] |
| winning_union_coverage | -0.016471 | -0.016471 | 0.000000 | [0.000000, 0.000000] |

- Legacy any2-positive 50-target block share: 47.06%
- Corrected any2-positive 50-target block share: 47.06%
- Legacy historical strict gate: FAIL
- Corrected historical strict gate: FAIL
- Prospective confirmation remains required; its minimum target count and completion rule are unspecified.
- STRICT_PASS_READY: **not created**
- Final purchase lines, random fallback, freeze, and seal: **not generated**

### Interpretation

The frozen E045 specification evaluates consecutive pairs and lexicographic tie-breaks on sorted six-number tickets. E075 corrects only those order-dependent operations. The original E045 runner and outputs remain unchanged. Model weights, role order, candidate-pool ranking formula, exact null, random seed, alpha, block length, bootstrap count, and strict gates are unchanged.

This is a reproducible implementation-conformance correction, not new predictive evidence. Historical results remain contaminated live-history diagnostics and cannot create purchase readiness.

No thresholds, alpha levels, block lengths, comparators, model weights, or parameter variants were changed.


### Workflow publication status

- Research calculation, cutoff/leakage/geometry verification, and the 8/8 output manifest succeeded.
- The commit was pushed to `main` successfully (`6be9e19..dfde545 HEAD -> main`).
- The overall Actions run nevertheless concluded **FAILURE** because the final `test -z "$(git status --porcelain)"` assertion exited 1 after the push. The job log does not print the residual paths. The earlier `python -m py_compile` step can leave untracked Python bytecode under `automation/**/__pycache__`; the recovery workflow now removes those generated files before the final cleanliness check.
- This was a post-publication workflow-cleanup failure, not a research-calculation, leakage, or manifest failure. The run is recorded as a workflow failure while its successful publication is recorded separately.
