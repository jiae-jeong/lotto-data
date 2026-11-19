# 2026-10-22 DAILY MASTER strict completion-gate correction

## Why this correction exists
The earlier V5 completion gate could emit `FULL_COMPLETE` after confirming only fresh A/C/contrarian successor prediction counts and leakage. That was insufficient under `LOTTO_PROJECT_PROTOCOL.md`, because it did not require full 0–6 hit scorecards, matched-random comparison, block stability, signal contribution, or five-ticket bundle validation.

The earlier result is preserved for auditability but must not be treated as satisfying the new strict completion standard.

## Code/CI correction
`automation/daily_master_full_v5.py` was changed so `FULL_COMPLETE` now requires, in the same dated execution:
- latest data integrity and fresh cumulative/structure/pair/triple calculations;
- B full walk-forward and fresh matched random baseline;
- historical recommendation/error-note source inventory;
- A/C/contrarian full cutoff-safe walk-forward with zero successor leakage;
- A/C/contrarian 0–6 scorecards, 2+/3+/4+/5+/6 rates, mean, variance and matched-random delta;
- non-overlapping 50-target block stability;
- leave-one-signal-out successor ablation;
- combined model scorecard;
- research-only five-ticket portfolio walk-forward and matched random five-ticket bundles;
- hypothesis status registry.

The workflow also explicitly checks the required output files and strict mandatory-check keys before results can be preserved as a successful run.

## First strict diagnostic results
The first strict calculation covered 1,046 cutoff-safe targets for each successor model, with 0 successor leakage failures.

Matched-random mean hits on those targets: 0.799857.
- A_v2 mean: 0.792543; delta vs matched random: -0.007314.
- C_v2 mean: 0.796367; delta: -0.003489.
- contrarian_v2 mean: 0.790631; delta: -0.009226.

Therefore none of the three successor models is promoted as superior to matched random on mean hits from this diagnostic.

### Signal ablation diagnostic
Full-minus-ablated mean-hit deltas (positive means removing the signal reduced performance; negative means removing it improved performance):
- A_v2: long_frequency -0.017208; recent_100 +0.028681; gap -0.005736; pair -0.015296.
- C_v2: long_frequency +0.002868; recent_100 +0.017208; gap +0.004780; pair -0.012428.
- contrarian_v2: long_frequency -0.000956; recent_100 +0.012428; gap -0.023901; pair +0.008604.

These are diagnostics only. No weight is automatically changed from one ablation run; all remain `MORE_TEST` until stability/prospective evidence is sufficient.

## Five-ticket portfolio diagnostic
A new fixed, outcome-blind `RESEARCH_ONLY_FIVE_TICKET_V1` diagnostic was tested on the same 1,046 targets against 1,000 matched uniform-random five-ticket bundles per target (1,046,000 random bundles total).

Key bundle results:
- max-hit mean: 1.662524 vs random 1.728826;
- any 2+ rate: 0.574570 vs random 0.618185;
- any 3+ rate: 0.093690 vs random 0.113604;
- any 4+ rate: 0.007648 vs random 0.006960 (small sparse difference; not sufficient for promotion);
- winning-number union coverage: 2.846080 vs random 3.066052;
- ticket union size: 21.688337 vs random 22.997611;
- mean pair overlap: 0.906405 vs random 0.799964;
- max pair overlap: 3.929254 vs random 2.094550.

Conclusion: this diagnostic portfolio is more redundant and worse than matched random on most useful bundle metrics. It remains `RESEARCH_ONLY` and is **not** promoted to the weekly purchase policy.

## CI path-selection bug discovered during strict test
The first strict script execution itself produced all strict mandatory checks as true, but the workflow's post-run verifier selected an older V5 directory because it used lexicographic directory-name sorting across midnight-style timestamps. This caused CI to fail for the wrong reason. The workflow was corrected to select the newest V5 directory by filesystem modification time instead. The failed run and its artifact are retained as evidence rather than overwritten.

## Non-negotiable interpretation rule going forward
Do not call a daily run complete merely because prediction records exist. If any strict metric gate is absent or fails, report the run as partial/failed and identify the missing item. Do not substitute an old successful artifact for a current-day missing calculation. Do not promote a research-only hypothesis or portfolio to weekly use without its own validated evidence.
