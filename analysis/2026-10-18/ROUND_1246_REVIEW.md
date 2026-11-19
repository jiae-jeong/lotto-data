# Round 1246 post-draw review

## Official result
- Draw: 1246 (2026-10-17)
- Main: 16, 22, 23, 24, 27, 28
- Bonus: 6
- Verified against multiple contemporaneous reports attributing the result to Donghaeng Lottery.

## Pre-draw purchase original
Source: commit bf41eb47359c732e0515776836b77ccb99044c840, `research/prospective_v4/decisions/1246/FIRST_PRIZE_PURCHASE_1246_V2.json`.
The file explicitly says target outcome was NOT AVAILABLE / NOT READ and ranks only frozen V4 challenger tickets by the preserved 200-target historical high-hit tail.

| Line | Final purchase | Frozen source | Main hits | Hit numbers | Misses | Bonus 6 |
|---|---|---|---:|---|---|---|
| 1 | 5 8 19 24 29 36 | V4_S expanding | 1 | 24 | 5 8 19 29 36 | no |
| 2 | 2 13 18 32 34 38 | V4_C expanding | 0 | - | all six | no |
| 3 | 6 12 15 21 22 29 | V4_G rolling300 | 1 | 22 | 6 12 15 21 29 | yes (6) |
| 4 | 1 5 7 9 12 19 | V4_C rolling300 | 0 | - | all six | no |
| 5 | 1 13 18 26 34 38 | V4_G expanding | 0 | - | all six | no |

Distribution: 0-hit 3 lines, 1-hit 2 lines, 2+/3+/4+ all zero. Only line 3 contains the bonus, but with only one main-number hit. Across the five-line portfolio, only 22 and 24 of the six winning main numbers were covered.

Excluded sixth frozen ticket was V4_S rolling300 = 6 13 20 24 26 35, excluded pre-draw because it ranked lowest on the preserved historical high-hit-tail rule. It would also have had only one main hit (24); this is diagnostic only and is not counted as a purchase result.

## Original purchase rationale vs result
The V2 purchase objective prioritized exact-six/high-hit-tail candidate quality rather than union coverage. Ranking order was historical 4+ count, then 3+ count, then mean hits, using the same frozen model/mode over a preserved 200-target diagnostic. This did not work in round 1246: the selected five tickets produced no 2+ line and covered only 2/6 winning numbers. Do not retrospectively replace this rationale with a new one.

## Result structure
- Sum: 140
- Odd:even = 2:4
- Low(1-22):high(23-45) = 2:4
- Consecutive runs: 22-23-24 and 27-28
- Decade/bucket concentration: five of six numbers are 21-30
- Repeated ending digit among main numbers: none
- Previous-draw overlap: 28 only (from round 1245)
- Pre-draw gaps (rounds since prior appearance, using 1245 cutoff): 16=3, 22=6, 23=4, 24=2, 27=21, 28=0.

## Frequency audit
Using a pre-draw 1245 cutoff, cumulative-rank evidence available in the review sources places 27 at rank 3, while 16/24 are around the middle and 22/23/28 below the top 15. Therefore cumulative TOP5/TOP10/TOP15 each contain exactly one winning number: 27. Recent 10/30/50/100 TOP5/TOP10/TOP15 intersections are deliberately not filled in here because they were not recomputed from the raw cutoff dataset in this run; no guessed figures are allowed.

## Model / signal scorecard update
The five purchased lines came from V4_S expanding, V4_C expanding, V4_G rolling300, V4_C rolling300, and V4_G expanding. Round-specific results are 1,0,1,0,0 main hits respectively. This single draw is not sufficient to reweight the models.

Fresh 2026-10-18 walk-forward recomputation in the repository reports: B n=1046 mean hits 0.78776 vs random mean 0.80102; C n=846 mean 0.75414; contrarian n=846 mean 0.74350; common random (401-1246) mean 0.79793. None establishes a predictive edge. B 3+ rate was 0.03155 vs its random 0.02347, but B mean and 2+/4+ do not establish overall superiority and this must not be promoted from one metric. C and contrarian likewise remain unproven.

## Core errors / learning
1. Candidate discovery failed: four winning numbers (16,23,27,28) were absent from all five purchased lines.
2. High-hit-tail purchase ranking did not translate into a 2+ line this draw; keep it as an unproven purchase policy, not a validated edge.
3. The result had extreme local clustering (22-23-24 and 27-28; five numbers in 21-30). Do not turn this into a predictive rule after seeing the draw; test historical prevalence and model sensitivity prospectively.
4. 27 combined very high cumulative frequency with a long pre-draw gap (~21) yet was absent from the purchase set. This is a new interaction hypothesis only, requiring rolling holdout tests.
5. The portfolio repeated several numbers (1,5,12,13,18,19,29,34,38) while missing four winners. Test whether repeated-core allocation improves or harms 2+/3+/4+ distribution versus diversity under identical pre-draw scores; do not infer from this draw alone.
6. The bonus 6 appeared in line 3 but is not evidence that the line/model was close to a high-tier win because only one main number matched.

## Next validation tasks
- Recompute recent 10/30/50/100 frequency TOP5/TOP10/TOP15 strictly at cutoff 1245 and store exact intersections.
- Test cumulative-frequency x gap interaction (especially high-frequency + long-gap) over rolling holdouts against random.
- Ablate structural filters and compare candidate recall separately from final-ticket assembly.
- Compare five-ticket portfolio policies: historical-tail ranking vs repeated-core vs diversity, using identical frozen candidate scores and pre-draw-only data.
- Keep A/B/C/contrarian/V4 weights frozen until repeated holdout evidence justifies a change.
- Continue separating candidate recall from ticket-construction performance.

## Leakage / hindsight control
The purchase original was committed before the 2026-10-17 draw and explicitly marked the target outcome unavailable/not read. This review uses the actual result only for scoring and hypothesis generation. New observations (cluster shape, frequency-gap interaction) remain hypotheses and are not retroactively treated as selection reasons.
