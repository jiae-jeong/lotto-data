# Can a cutoff-safe five-line candidate bank preserve source provenance while removing duplicate and near-duplicate lines?

## MAINTENANCE/RECHECK

Canonical data and the frozen seven-component B forecast cache were read as provenance-controlled inputs. No E010-E024 study was rerun.

## NEW STUDY

For every target, the bank contains the frozen B component/combined forecasts and only E025 survivors validated in E026. Candidate tickets are constructed from t-1 information. Exact/near duplicates with intersection at least five are merged to one canonical candidate while every source remains in CANDIDATE_PROVENANCE.csv.

## NEW FINDING

The bank is a source-preserving historical candidate set; its existence does not imply any candidate outperforms random.

## Results

```json
{
  "status": "PASS",
  "target_count": 645,
  "candidate_rows": 6251,
  "provenance_rows": 6450,
  "overlap_rows": 27254,
  "cutoff_violations": 0,
  "duplicate_or_near_duplicate_pairs": 0,
  "independent_sources_included": [
    "CALENDAR_SEASON_CONDITIONAL_v1",
    "PREVIOUS_SUM_REGIME_CONDITIONAL_v1"
  ],
  "future_outcomes_used_for_bank": false,
  "future_predictions": 0
}
```

## NEXT TEST

Retain this specification and require the independent promotion gate; do not use the historical result to generate a recommendation.
