# Does nested 3+ or 4+ selection of overlap-weighted ensembles improve the high-hit tail compared with fixed equal weighting?

## NEW STUDY

POST_HOC_EXPLORATORY. Frozen B component cache, targets 601..1245, n=645. All tickets use only pre-target forecasts; nested settings use the preceding 200 out-of-sample rewards. No future prediction or recommendation.

| Policy | Mean | 2+ | 3+ | 4+ |
|---|---:|---:|---:|---:|
|long_frequency|0.741085|15.504%|2.791%|0.000%|
|current_gap|0.804651|17.364%|1.395%|0.000%|
|frequency_plus_gap|0.801550|18.760%|2.171%|0.310%|
|recent_momentum|0.714729|14.574%|1.085%|0.000%|
|structure_profile|0.730233|16.124%|1.705%|0.000%|
|pair_association|0.818605|19.225%|1.085%|0.000%|
|triple_association|0.798450|17.674%|2.171%|0.000%|
|combined_equal_rank|0.745736|14.884%|1.550%|0.310%|
|EQUAL_VOTE_7|0.768992|16.744%|2.016%|0.310%|
|NESTED_TAIL_3|0.750388|15.659%|2.016%|0.310%|
|NESTED_TAIL_4|0.753488|15.814%|2.171%|0.310%|

| UNIFORM_EXACT | 0.800000 | 17.531% | 2.383% | 0.139% |

## NEW FINDING

- NESTED_TAIL_3: mean=0.750388; 3+=13 draws; 4+=2 draws; positive Holm<.05 comparisons=0. No predictive promotion.
- NESTED_TAIL_4: mean=0.753488; 3+=14 draws; 4+=2 draws; positive Holm<.05 comparisons=0. No predictive promotion.

Family grouping is semantic, not a claim of statistical independence. B pair/triple greedy tickets differ from batch001 residual-node tickets. Current-ticket overlap weights never use the current outcome. Bootstrap length20, 10000 replicates; conditional on observed fitted policy paths. Holm covers all primary policies x3 controls x4 metrics in this registered job. Historical design selection is not removed by correction.

## MAINTENANCE/RECHECK

Verified snapshot and published cache hashes, cutoff and outcomes. Existing B/Monte Carlo/H001/H002/regime studies were read and reused as controls, not repeated as new studies.

## NEXT TEST

Retain failed hypotheses. Independently test tail-oriented weight selection, then exact high-tail sample-size/precision, or a new preregistered hypothesis. Do not rerun this same job on the same data as a new daily contribution. Future evaluation requires pre-draw registration.
