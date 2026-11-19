# E076 — Historical recommendation candidate-vs-allocator decomposition

**Classification: historical post-hoc diagnostic only. No clean holdout, no actual-purchase claim, no model promotion.**

## Question

For each preserved pre-draw recommendation artifact, separate (1) winning numbers excluded from the portfolio union from (2) winning numbers present in the union but not concentrated on the highest-hit line.

## Integrity and provenance

- Canonical source: `lotto_data.csv`, rounds 1–1250, 1,250 contiguous rows.
- Git blob: `66431d711919f179e4cb1349e2f7295c68a8735e`
- SHA-256 recorded in the current MASTER audit: `7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2`
- All six source recommendation artifacts matched the preregistered Git blob SHA and each cutoff was exactly target round minus one.
- Every line had six unique integers in 1–45; target outcomes were read only for post-draw scoring.
- Purchase registry: **0 confirmed purchases**. These are preserved recommendation artifacts, not verified purchases.

## Results

| Artifact | Lines | Union | Winners in union | Excluded | Recall | Max hit | Line-hit distribution | 2+ possible in union? | 2+ realized? | 3+ possible in union? | 3+ realized? |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---|
| R1245_V4_PRIMARY_3L | 3 | 15 | 1/6 | 5 | 16.7% | 1 | 0/0/1 | No | No | No | No |
| R1246_V2_PURCHASE_DECISION_5L | 5 | 21 | 2/6 | 4 | 33.3% | 1 | 1/0/1/0/0 | Yes | No | No | No |
| R1246_FALLBACK_5L | 5 | 21 | 4/6 | 2 | 66.7% | 1 | 1/1/1/1/1 | Yes | No | Yes | No |
| R1247_PROTOCOL_FULL_V3_5L | 5 | 30 | 5/6 | 1 | 83.3% | 3 | 1/3/0/0/1 | Yes | Yes | Yes | Yes |
| R1248_V54_NAMED_STRICT_PASS_5L | 5 | 30 | 3/6 | 3 | 50.0% | 1 | 0/1/1/0/1 | Yes | No | Yes | No |
| R1248_FALLBACK_5L | 5 | 18 | 5/6 | 1 | 83.3% | 3 | 3/1/2/1/1 | Yes | Yes | Yes | Yes |

## Two-stage failure decomposition

- 5 of 6 artifacts contained at least two winning numbers in their union; 2 of 6 realized a 2+ line. Thus 3 artifacts had a 2+ opportunity at candidate stage but failed at line composition.
- 4 of 6 artifacts contained at least three winning numbers in their union; 2 realized a 3+ line. Thus 2 artifacts had a 3+ candidate opportunity but failed at composition.
- 3 artifacts contained at least four winning numbers in their union; none realized a 4+ line.
- The clearest allocator-stage misses were the 1246 fallback (four winners in the union, one hit on every line) and the 1248 V54-labelled artifact (three winners in the union, maximum one hit on a line).
- The 1245 three-line record had only one winning number in its union, so a 2+ line was impossible before allocation. This is a candidate-stage failure, not an allocator failure.

## Interpretation and limits

This small set is useful for labeling failure modes, not estimating predictive skill. The 1246 and 1248 rounds each have two different preserved recommendation artifacts; they remain separate and are not retrospectively ranked as actual purchases. The 1247 V3 artifact's later model-validation review rejected strict promotion, and the 1248 fallback was explicitly not a strict pass. Different ticket counts and union geometries prevent pooled performance claims. The 1244–1249 interval remains contaminated live-history diagnostic material.

No p-values, confidence intervals, or random superiority claims were calculated. No recommendation rules, weights, strict thresholds, or prospective requirements were changed.

## Next steps

1. Wait for the already-preregistered E075 paired legacy/corrected selector workflow to finish; preserve its two failed attempts and current V3 scope.
2. If E075 completes, report legacy and corrected results separately, with the same cutoff and exact geometry-matched null.
3. Keep the prospective minimum target count/completion rule unresolved until an explicit policy decision; E046 remains design-only and is not adopted.

