# How does a pre-frozen three-component ticket bundle compare with same-target random three-ticket bundles on OOS coverage?

## MAINTENANCE/RECHECK

Existing B component forecasts are reused only as the frozen, cutoff-safe input panel; this is not a new B reproduction.

## NEW STUDY

One pre-frozen three-component bundle is evaluated only where all component predictions exist. Random comparisons use three independent uniform tickets on each same target round.

## NEW FINDING

Retrospective portfolio findings do not change any prospective or purchase rules; no bundle is generated for future rounds.

## Results

```json
[
  {
    "bundle": "FIXED_THREE_COMPONENT_BUNDLE",
    "target_rounds": 645,
    "random_bundles": 0,
    "mean_bundle_max_hits": 1.4186046511627908,
    "mean_unique_number_coverage": 16.052713178294574,
    "mean_winning_union_coverage": 2.0651162790697675,
    "rate_any_2plus": 0.4310077519379845,
    "rate_any_3plus": 0.05581395348837209,
    "rate_any_4plus": 0
  },
  {
    "bundle": "RANDOM_THREE_TICKET_BUNDLE",
    "target_rounds": 645,
    "random_bundles": 64500,
    "mean_bundle_max_hits": 1.4531007751937985,
    "mean_unique_number_coverage": 15.716883720930232,
    "mean_winning_union_coverage": 2.1025426356589145,
    "rate_any_2plus": 0.44102325581395346,
    "rate_any_3plus": 0.07103875968992249,
    "rate_any_4plus": 0.0040465116279069764
  }
]
```

## Verification

```json
{
  "status": "PASS",
  "target_rounds": 645,
  "fixed_bundle_records": 645,
  "random_bundle_records": 64500,
  "bundle_components_frozen": [
    "long_frequency",
    "structure_profile",
    "pair_association"
  ],
  "future_predictions": 0,
  "component_sources": "cutoff-safe stored OOS forecasts"
}
```

## NEXT TEST

Retain the frozen experiment and seek independent prospective evidence. Do not tune this result into a future recommendation.
