# How much confirmatory data is required for 3+/4+ effect sizes at a prespecified family error rate?

## NEW STUDY

Exact binomial power for 3+/4+ at 1.5x and 2x uniform probabilities, alpha=.05/4. No Monte Carlo, SciPy or NumPy dependency. This is a new uncertainty/sample-size design question, not a repeat of the large uniform baseline.

| Tail | n | Effect | Critical count | Power |
|---|---:|---:|---:|---:|
|3+|200|1.5x|11|10.560%|
|3+|200|2.0x|11|35.738%|
|3+|500|1.5x|21|25.635%|
|3+|500|2.0x|21|75.288%|
|3+|1000|1.5x|36|50.652%|
|3+|1000|2.0x|36|96.888%|
|3+|2000|1.5x|65|79.902%|
|3+|2000|2.0x|65|99.968%|
|3+|5000|1.5x|145|99.637%|
|3+|5000|2.0x|145|100.000%|
|3+|10000|1.5x|274|100.000%|
|3+|10000|2.0x|274|100.000%|
|4+|200|1.5x|3|0.883%|
|4+|200|2.0x|3|1.894%|
|4+|500|1.5x|4|2.174%|
|4+|500|2.0x|4|5.274%|
|4+|1000|1.5x|6|1.992%|
|4+|1000|2.0x|6|6.371%|
|4+|2000|1.5x|8|6.241%|
|4+|2000|2.0x|8|19.948%|
|4+|5000|1.5x|14|17.038%|
|4+|5000|2.0x|14|52.877%|
|4+|10000|1.5x|24|27.645%|
|4+|10000|2.0x|24|79.376%|

## NEW FINDING

Finite high-tail samples can be substantially underpowered even at doubled event probability. Values above are exact under independent fair draws; they are not evidence any model achieves the hypothetical alternative.

## MAINTENANCE/RECHECK

Exact hypergeometric reference, analytically specified hypothetical effects. This independent theory/design study needs no external data, historical cache, model implementation, NumPy, or large random simulation.

## NEXT TEST

Choose a future confirmatory sample size before outcomes and retain multiplicity control; do not claim 200 targets suffice for 4+ superiority without power evidence.
