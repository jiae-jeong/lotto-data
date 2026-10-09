# Independent validation and 1245 candidate reassessment

Date: 2026-10-09 (Asia/Seoul)

## Evidence separation

- New results: model candidate predictions and 200-target expanding/rolling-300 validation were recomputed by this run.
- Existing results: the prior B report, stored batch-001 metrics, V3 check-only output, and 1245 candidate lines remain historical inputs/references; they were not relabeled as newly computed.
- The final 1245 actual result was not loaded. These are algorithmic purchase candidates, not winning predictions.
- The study's evidence is post-hoc. Newly recomputing its last-200 slice does not make it prospective or independent of prior research selection. The worktree byte SHA reflects line endings; LF normalization reproduces the pinned raw hash `243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f`.

## Data integrity

- Source: `lotto_data.csv`; SHA-256 `10beb0a7974f648b39aa130bb714b1c338296bf59ecd106e9407bee5875538aa`.
- Rows: 1244; consecutive unique rounds 1..1244; latest published row date 2026.10.03.
- Exact expected columns; six unique main numbers in 1..45 per round; bonus valid, in range, and separate.
- Training cutoff for every target t was t-1. Expanding uses 1..t-1; rolling uses the latest 300 draws ending t-1.
- 1245 candidate generation uses exactly rounds 1..1244; no outcome row beyond cutoff was read.

## Exact random baseline

- Mean hits per six-number ticket: 0.800000.
- P(2+ hits): 17.530810%; P(3+ hits): 2.383408%.
- The expanding S005 mean (0.680) falls just below the approximate pointwise mean band (0.691?0.909), while rolling S002 mean (0.925) and P(2+) (24.0%) exceed their approximate pointwise bands. These opposite-direction findings are exploratory: they are post-hoc across multiple models/metrics and are not adjusted for multiple comparisons. They do not establish a validated predictive signal. The scorecard bands are descriptive only.

## Fresh model results

See `fresh_model_scorecard.csv` for every model under both newly recomputed windows, and `fresh_walkforward_predictions.csv` for each target/model prediction. The last-200 target interval is 1045–1244 (n=200 per model and window).

## Three-line portfolio results

See `fresh_portfolio_metrics.csv` for the existing V3 selector applied at each target using only prior draws, and `fresh_portfolio_walkforward.csv` for the per-target lines/hits. This checks the selection rule itself; it is not a historical score of the fixed 1245 ticket chosen after observing rounds 1–1244.

## Candidate overlap and number relationships

`fresh_candidate_overlaps.csv` reports all 28 candidate pairs; `fresh_candidate_number_frequency.csv` reports per-number support among S001–S008. `reassessed_portfolio_overlap.csv` gives chosen-line intersections. S006/S007 overlap and number support are diagnostics, not independent model votes.

## Reassessed 1245 lines

|Line|Numbers|Sources|Sum|Odd|Low (1–22)|Line intersection|
|---:|---|---|---:|---:|---:|---|
|1|7 11 13 16 32 34|S001;S002;S003;S004;S005;S006;S007|113|3|4|L2: 2 (13 16); L3: 0 (none)|
|2|13 15 16 18 31 38|S001|131|3|4|L3: 0 (none)|
|3|3 10 17 23 25 27|S003|105|5|3|see overlap CSV|

Selection method remains the V3 rule: equal-family rank consensus, S006/S007 averaged as one relationship family, S008 excluded as another vote, then two tickets chosen from distinct families by structure coverage, portfolio number coverage, intersections, and deterministic ID ties. Previous recovery lines remain preserved in the original dated folder; compare `prior_recovery_sha256` in run metadata.

All three reassessed lines are unchanged from the original recovery file (SHA-256 `d5e6da9e34d68f847a2d674b71e5d20512543d677734697333c21407f8478825`). They are retained because the frozen V3 tie-break rule is deterministic; the walk-forward portfolio diagnostics do not show a repeatable advantage over random.

## Incomplete

- Original sealed V3 gate remains NOT PASSED: the prospective model registry/seal and prior B artifacts listed in `recovery_run_20261009/PIPELINE_ERROR_REPORT.md` were not found.
- No unified A/B/C/contrarian models or their output artifacts were found in the accessible PC scan, Git history, or the only GitHub branch (`main`). A study comparison CSV and B report exist, but neither substitutes for the missing B predictions/classification CSVs.
- No truly untouched prospective holdout exists before round 1245 in the current source; reported 1045–1244 validation is historical/post-hoc.
- Therefore no S-model is labeled a validated predictive signal; repeatable random-level performance remains the null interpretation.

## Re-run

```powershell
& 'C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' research\1245_final_pipeline_v3\independent_validation_20261009.py --run-id next-run
```

The script refuses to overwrite an existing run folder. See the committed `execution.log` for actual command output.
