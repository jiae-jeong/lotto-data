# Existing evidence review — V4 intake

GitHub base: `bdc38abdcb6a7f511ad2ee39914f9126a69aeb05`; original local HEAD: `6ee07c2a5bca8f7d5e714a6d48bc5a8b7fd9cf5d`.

163 source files were read in full across latest main and preserved local checkout; CSV records parsed, Python syntax parsed, JSON decoded; see source inventory. Reading historical artifacts is not a new backtest.

## B-v1
Exact source + four CSV digests PASS. Stored 33,408 prediction rows were checked for target cutoff and hit agreement against validated raw data. Eight classifications: seven ADDITIONAL VALIDATION, one HOLD (combined_equal_rank). No validated predictive edge. Anchor/horizon rows overlap and must not be counted as independent tests.

## Expansion and failure records
Stored expanding predictions: 8,352; rolling300: 5,952. Expanding overall five means below random, three above; all eight surviving_models rows are NONE_PROMOTED. Failure registry has WEAK 43/HOLD 21 windows; rolling WEAK 20/HOLD 12. These labels are descriptive, not confirmatory significance.
Pair/triple temporal stability 15,180 rows, structure transition 1,346 rows, temporal number features 45 rows and all correlation records were read. Shared frequency inputs, overlapping windows and pair/triple dependence prohibit treating them as independent ensemble votes.

## Independent validation completeness
Latest-main fresh_walkforward_predictions.csv has 1,798 parsed records; preserved local original has 3,200 records. All local 3,200 records (16 mode/model groups x 200 targets) pass cutoff, validity, actual-number and hit checks. Stored reproduction summary says 16/16 matches. The GitHub partial artifact is not silently repaired, overwritten, or treated as complete prospective evidence. Both runs remain historical/post-hoc; schema/sample mismatch remains a separate V3 archival issue.

## Source review issues
S002 completed-gap implementation assigns event to bins(g) and exposures to bins(0..g-1), omits ongoing censored exposure. New V4_G counts directly observed next-draw transitions at the previous age; this is a new corrected hypothesis, not a rerun of old S002.
S008 appends constant score vectors for structure membership over all 45 numbers; the structure vote is not number-specific. V4 excludes this legacy hybrid and does not change its code or historical scores.

## New V4 roles
No model has been promoted. V4_G/C/S are experimental challengers; F/M/P/T are fixed reference/diagnostic controls; U is uniform negative control. All hypotheses are post-hoc in their origin, but evaluation of future pre-registered forecasts can be prospective. Extreme structures are diagnosed without vetoes. No purchasing or edge claim is authorized by this freeze.

## Remaining legacy gaps
Oct 8 candidate/recent-validation outputs and original prospective protocol/registry/model-manifest/seal remain missing. A/C/contrarian original implementations are not fabricated. V3 stays SEALED V3 GATE NOT PASSED. Historical 1245 recovery and reassessed candidate lines are referenced by provenance in the inventory and never replaced.
