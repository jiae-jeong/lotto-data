# E057 — Three-line exact-null strict-gate calibration

**Study status: COMPLETE · Calibration result: PASS for the registered null mechanism · Purchase readiness: unchanged / NOT READY**

## Research question

Under the exact uniform null for exactly three pairwise-disjoint six-number lines with union18, how often does the unchanged target-1251 strict gate falsely pass over an 850-target evaluation?

This is a gate-calibration study, not a predictive-model study. It cannot create a model edge or authorize purchase lines.

## Frozen scope and execution

- Preregistration: research/weekly_purchase/1251/E057_THREE_LINE_NULL_GATE_CALIBRATION_PREREG_20261116.json
- Data: lotto_data.csv, 1,250 consecutive draws, cutoff 1250; verified SHA-256 7203238d…f063b3c2
- Target slots: 401–1250, 850 targets
- Null trajectories: 1,000
- Random portfolios: 850,000 total
- Each portfolio: exactly three pairwise-disjoint six-number lines, union18
- Bootstrap: 4,000 replicates per metric per trajectory; 50-target moving blocks; 17 blocks; no remainder
- Strict thresholds were unchanged: family alpha 0.05, per-metric alpha 0.0125, four lower bounds strictly above zero, and at least 65% positive non-overlapping 50-target any2 blocks.

The random portfolio generator samples a uniform 18-subset without replacement and partitions it into three six-number lines. This is distributionally equivalent to the frozen E045 uniform label-permutation null. The historical winning outcomes are used only as fixed conditional labels; they do not select or rank any ticket.

## Exact-null implementation check

The independently derived expectations match the frozen E045 values to a maximum absolute error of **1.78e-15**, below the preregistered 1e-12 tolerance.

| Metric | Exact null mean |
|---|---:|
| max-hit | 1.514256 |
| any2+ | 47.4976% |
| any3+ | 7.1355% |
| winning-union coverage | 2.400000 |

The empirical means across 850,000 simulated portfolios were all within two Monte Carlo standard errors of the analytic expectations. The largest absolute z-score was 1.81. Geometry violations: **0**.

## False-pass result

**1 / 1,000 null trajectories passed the full gate.**

- Empirical joint false-pass rate: **0.10%**
- 95% Wilson interval: **0.0177%–0.5643%**
- Familywise ceiling: **5%**
- The interval's upper bound remains well below the frozen 5% ceiling.

The 65% any2-positive-block condition alone was met by 118/1,000 null trajectories (11.8%). The four simultaneous adjusted-CI conditions reduced the joint false-pass count to one.

Individual adjusted-CI lower-bound-positive rates were 1.5% (max-hit), 1.5% (any2), 0.9% (any3), and 1.2% (union coverage). These are finite-simulation diagnostics; the primary calibration endpoint is the joint gate, not any single metric.

## Interpretation

The unchanged three-line gate is conservative under this registered independent exact-uniform disjoint-union18 null. This supports the implementation and false-pass control for this one null mechanism; it does **not** prove that every non-predictive temporal or persistent-signal mechanism is controlled, and it does not establish any predictive edge.

No thresholds, alpha, block length, comparator, or model weights were changed. No candidate numbers or purchase lines were generated. No model was promoted. The 1251 purchase gate remains **STRICT_FAIL / NOT READY**.

## Existing research context — not rerun

- E052 trailing-performance selector: historical three-line strict fail.
- E054 rolling concentration regime: all four point deltas negative; any2-positive 50-target block share 6/17 (35.29%); strict fail.
- E055 triple recent-strength persistence: correlation -0.309, bootstrap interval [-0.612, -0.018], random-tail probability 0.826; predictive persistence not supported.
- E056 H005_FIX: mapping repair changed 932/1,050 top-six tickets, but classification remains WEAK; recent100 mean hits 0.70 and recent50 0.62; no promotion.

## Provenance correction

The purchase-confirmation registry currently has **zero confirmed purchases**. The 1245 V4 recommendation and 1246 competing pre-draw sets have no receipt confirmation. The 1247 and 1248 files named ACTUAL_PURCHASE are explicitly unconfirmed by the 2026-11-14 provenance correction; 1249 and 1250 are also not confirmed. These artifacts remain historical recommendation diagnostics, not verified purchased-ticket outcomes.

The 1244–1249 period remains exposed live-history material, not a clean holdout.

## Unresolved items and next work

1. Keep the current strict gate unchanged; extend null calibration to a separately preregistered persistent/block-correlated null before making a broader calibration claim.
2. Resolve the prospective confirmation minimum target count and completion rule before any future strict-pass readiness decision; do not invent these values.
3. E043/E044 remain five-line-only H1250 diagnostics awaiting their dedicated workflow dispatch; they cannot qualify the target-1251 three-line purchase policy.
