# Do frozen cross-round transition and season-conditioned signals add genuinely independent number rankings beyond the seven B components?

## MAINTENANCE/RECHECK

Canonical data and the frozen seven-component B forecast cache were read as provenance-controlled inputs. No E010-E024 study was rerun.

## NEW STUDY

Exploration was restricted to three frozen cross-round/seasonal conditional families. Correlation is Pearson correlation between candidate score rank and each cached B ticket's 0/1 membership vector; Jaccard compares top-six sets. Signals were screened on prediction geometry only, not hits.

## NEW FINDING

Only signals below every pre-registered B-overlap threshold proceed as independent candidates. This screen tests redundancy, not predictive merit.

## Results

```json
{
  "similarity_summary": [
    {
      "signal": "CROSS_ROUND_MARKOV_v1",
      "target_count": 645,
      "b_component_count": 8,
      "mean_abs_rank_to_selection_correlation": 0.20348659131581903,
      "mean_top6_jaccard": 0.1513434175643478,
      "max_component_mean_jaccard": 0.34645256552233294,
      "max_jaccard_component": "long_frequency",
      "independence_thresholds": "mean_abs_corr<0.20;mean_jaccard<0.20;max_component_mean_jaccard<0.35",
      "status": "DROPPED_AS_B_REDUNDANT"
    },
    {
      "signal": "CALENDAR_SEASON_CONDITIONAL_v1",
      "target_count": 645,
      "b_component_count": 8,
      "mean_abs_rank_to_selection_correlation": 0.16362371664585912,
      "mean_top6_jaccard": 0.12072376589818451,
      "max_component_mean_jaccard": 0.2463015537434142,
      "max_jaccard_component": "long_frequency",
      "independence_thresholds": "mean_abs_corr<0.20;mean_jaccard<0.20;max_component_mean_jaccard<0.35",
      "status": "SURVIVES"
    },
    {
      "signal": "PREVIOUS_SUM_REGIME_CONDITIONAL_v1",
      "target_count": 645,
      "b_component_count": 8,
      "mean_abs_rank_to_selection_correlation": 0.16178587267859687,
      "mean_top6_jaccard": 0.1156237625423672,
      "max_component_mean_jaccard": 0.19984093425953892,
      "max_jaccard_component": "long_frequency",
      "independence_thresholds": "mean_abs_corr<0.20;mean_jaccard<0.20;max_component_mean_jaccard<0.35",
      "status": "SURVIVES"
    }
  ],
  "survivors": [
    "CALENDAR_SEASON_CONDITIONAL_v1",
    "PREVIOUS_SUM_REGIME_CONDITIONAL_v1"
  ],
  "dropped": [
    "CROSS_ROUND_MARKOV_v1"
  ]
}
```

## NEXT TEST

Retain this specification and require the independent promotion gate; do not use the historical result to generate a recommendation.
