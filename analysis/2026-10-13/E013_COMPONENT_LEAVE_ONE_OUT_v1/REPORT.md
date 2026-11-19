# Does dropping any one of the seven frozen B components change equal-vote ensemble performance on the same 601–1245 OOS targets?

## MAINTENANCE/RECHECK

Existing B component forecasts are reused only as the frozen, cutoff-safe input panel; this is not a new B reproduction.

## NEW STUDY

Seven frozen one-component leave-outs were compared with full seven-ticket equal vote, the cached B equal-rank ticket, and exact 6/45 reference. Each target ticket uses the component cache available through t-1.

## NEW FINDING

Ablations are exploratory, outcome-dependent retrospective comparisons. Holm-adjusted paired moving-block bootstrap results are descriptive evidence only; the best-looking ablation is not selected or promoted.

## Results

```json
[
  {
    "policy": "FULL_EQUAL_VOTE",
    "n": 645,
    "mean_hits": 0.7689922480620155,
    "variance_hits_population": 0.611751697614326,
    "hits_0_count": 272,
    "hits_1_count": 265,
    "hits_2_count": 95,
    "hits_3_count": 11,
    "hits_4_count": 2,
    "hits_5_count": 0,
    "hits_6_count": 0,
    "rate_ge_2": 0.16744186046511628,
    "rate_ge_3": 0.020155038759689922,
    "rate_ge_4": 0.0031007751937984496,
    "rate_ge_5": 0.0,
    "rate_ge_6": 0.0
  },
  {
    "policy": "B_EQUAL_RANK",
    "n": 645,
    "mean_hits": 0.7457364341085271,
    "variance_hits_population": 0.5679081785950364,
    "hits_0_count": 272,
    "hits_1_count": 277,
    "hits_2_count": 86,
    "hits_3_count": 8,
    "hits_4_count": 2,
    "hits_5_count": 0,
    "hits_6_count": 0,
    "rate_ge_2": 0.14883720930232558,
    "rate_ge_3": 0.015503875968992248,
    "rate_ge_4": 0.0031007751937984496,
    "rate_ge_5": 0.0,
    "rate_ge_6": 0.0
  },
  {
    "policy": "DROP_LONG_FREQUENCY",
    "n": 645,
    "mean_hits": 0.7689922480620155,
    "variance_hits_population": 0.6086509224205277,
    "hits_0_count": 271,
    "hits_1_count": 268,
    "hits_2_count": 91,
    "hits_3_count": 14,
    "hits_4_count": 1,
    "hits_5_count": 0,
    "hits_6_count": 0,
    "rate_ge_2": 0.16434108527131783,
    "rate_ge_3": 0.023255813953488372,
    "rate_ge_4": 0.0015503875968992248,
    "rate_ge_5": 0.0,
    "rate_ge_6": 0.0
  },
  {
    "policy": "DROP_CURRENT_GAP",
    "n": 645,
    "mean_hits": 0.7689922480620155,
    "variance_hits_population": 0.6241547983895198,
    "hits_0_count": 269,
    "hits_1_count": 277,
    "hits_2_count": 81,
    "hits_3_count": 15,
    "hits_4_count": 3,
    "hits_5_count": 0,
    "hits_6_count": 0,
    "rate_ge_2": 0.15348837209302327,
    "rate_ge_3": 0.027906976744186046,
    "rate_ge_4": 0.004651162790697674,
    "rate_ge_5": 0.0,
    "rate_ge_6": 0.0
  },
  {
    "policy": "DROP_FREQUENCY_PLUS_GAP",
    "n": 645,
    "mean_hits": 0.7596899224806202,
    "variance_hits_population": 0.6197704464875909,
    "hits_0_count": 272,
    "hits_1_count": 276,
    "hits_2_count": 80,
    "hits_3_count": 15,
    "hits_4_count": 1,
    "hits_5_count": 1,
    "hits_6_count": 0,
    "rate_ge_2": 0.15038759689922482,
    "rate_ge_3": 0.02635658914728682,
    "rate_ge_4": 0.0031007751937984496,
    "rate_ge_5": 0.0015503875968992248,
    "rate_ge_6": 0.0
  },
  {
    "policy": "DROP_RECENT_MOMENTUM",
    "n": 645,
    "mean_hits": 0.786046511627907,
    "variance_hits_population": 0.6177897962862808,
    "hits_0_count": 265,
    "hits_1_count": 270,
    "hits_2_count": 94,
    "hits_3_count": 15,
    "hits_4_count": 1,
    "hits_5_count": 0,
    "hits_6_count": 0,
    "rate_ge_2": 0.17054263565891473,
    "rate_ge_3": 0.024806201550387597,
    "rate_ge_4": 0.0015503875968992248,
    "rate_ge_5": 0.0,
    "rate_ge_6": 0.0
  },
  {
    "policy": "DROP_STRUCTURE_PROFILE",
    "n": 645,
    "mean_hits": 0.7984496124031008,
    "variance_hits_population": 0.6043386815696172,
    "hits_0_count": 250,
    "hits_1_count": 296,
    "hits_2_count": 80,
    "hits_3_count": 17,
    "hits_4_count": 2,
    "hits_5_count": 0,
    "hits_6_count": 0,
    "rate_ge_2": 0.15348837209302327,
    "rate_ge_3": 0.02945736434108527,
    "rate_ge_4": 0.0031007751937984496,
    "rate_ge_5": 0.0,
    "rate_ge_6": 0.0
  },
  {
    "policy": "DROP_PAIR_ASSOCIATION",
    "n": 645,
    "mean_hits": 0.7767441860465116,
    "variance_hits_population": 0.6261258337840274,
    "hits_0_count": 270,
    "hits_1_count": 266,
    "hits_2_count": 95,
    "hits_3_count": 11,
    "hits_4_count": 3,
    "hits_5_count": 0,
    "hits_6_count": 0,
    "rate_ge_2": 0.16899224806201552,
    "rate_ge_3": 0.021705426356589147,
    "rate_ge_4": 0.004651162790697674,
    "rate_ge_5": 0.0,
    "rate_ge_6": 0.0
  },
  {
    "policy": "DROP_TRIPLE_ASSOCIATION",
    "n": 645,
    "mean_hits": 0.7705426356589147,
    "variance_hits_population": 0.5799074574845262,
    "hits_0_count": 264,
    "hits_1_count": 278,
    "hits_2_count": 91,
    "hits_3_count": 11,
    "hits_4_count": 1,
    "hits_5_count": 0,
    "hits_6_count": 0,
    "rate_ge_2": 0.15968992248062017,
    "rate_ge_3": 0.018604651162790697,
    "rate_ge_4": 0.0015503875968992248,
    "rate_ge_5": 0.0,
    "rate_ge_6": 0.0
  },
  {
    "policy": "UNIFORM_EXACT",
    "n": 645,
    "mean_hits": 0.8,
    "variance_hits_population": 0.6145454545454546,
    "hits_0_count": null,
    "hits_1_count": null,
    "hits_2_count": null,
    "hits_3_count": null,
    "hits_4_count": null,
    "hits_5_count": null,
    "hits_6_count": null,
    "rate_ge_2": 0.17530810086113546,
    "rate_ge_3": 0.023834078570323606,
    "rate_ge_4": 0.0013934826753885178,
    "rate_ge_5": 2.885184393976226e-05,
    "rate_ge_6": 1.2277380399898834e-07
  }
]
```

## Verification

```json
{
  "status": "PASS",
  "targets_checked": 645,
  "prediction_records_checked": 5805,
  "policies": 9,
  "paired_comparisons": 56,
  "leakage_failures": 0,
  "independent_ticket_replay": "PASS",
  "future_predictions": 0
}
```

## NEXT TEST

Retain the frozen experiment and seek independent prospective evidence. Do not tune this result into a future recommendation.
