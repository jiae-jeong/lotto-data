# B same-target Monte Carlo comparison — addendum

- Random tickets: 1,045,000 = 1000 per each of 1045 targets.
- Seed: 20261013; random mean=0.800345, population variance=0.614912.
- Model scores deduplicated by target/model after confirming overlapping holdouts produce identical forecasts. Paired differences use each model's hit count minus the random mean for that same target.

| Model | Mean hits | Random mean | Paired mean difference | Model 2+ | Random 2+ | Model 3+ | Random 3+ | Model 4+ | Random 4+ | Model 5+ | Random 5+ | Model 6 | Random 6 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| combined_equal_rank | 0.7636 | 0.8003 | -0.0367 | 15.79% | 17.55% | 1.53% | 2.38% | 0.287% | 0.145% | 0.000% | 0.004% | 0.000% | 0.000% |
| current_gap | 0.7952 | 0.8003 | -0.0051 | 16.75% | 17.55% | 1.44% | 2.38% | 0.000% | 0.145% | 0.000% | 0.004% | 0.000% | 0.000% |
| frequency_plus_gap | 0.7962 | 0.8003 | -0.0042 | 18.09% | 17.55% | 2.01% | 2.38% | 0.191% | 0.145% | 0.000% | 0.004% | 0.000% | 0.000% |
| long_frequency | 0.7828 | 0.8003 | -0.0176 | 17.22% | 17.55% | 2.78% | 2.38% | 0.191% | 0.145% | 0.000% | 0.004% | 0.000% | 0.000% |
| pair_association | 0.8057 | 0.8003 | +0.0054 | 18.18% | 17.55% | 1.34% | 2.38% | 0.000% | 0.145% | 0.000% | 0.004% | 0.000% | 0.000% |
| recent_momentum | 0.7627 | 0.8003 | -0.0377 | 15.89% | 17.55% | 1.34% | 2.38% | 0.000% | 0.145% | 0.000% | 0.004% | 0.000% | 0.000% |
| structure_profile | 0.7943 | 0.8003 | -0.0061 | 18.28% | 17.55% | 2.58% | 2.38% | 0.096% | 0.145% | 0.000% | 0.004% | 0.000% | 0.000% |
| triple_association | 0.8134 | 0.8003 | +0.0131 | 19.04% | 17.55% | 2.30% | 2.38% | 0.000% | 0.145% | 0.000% | 0.004% | 0.000% | 0.000% |

The MC rates are finite-simulation estimates and can differ slightly from the exact uniform distribution. The main B run also records exact theoretical baseline values. This retrospective comparison is descriptive and does not establish predictive advantage.
