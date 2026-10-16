# Draw 1246 validation and purchase decision — V1

Created pre-draw on 2026-10-16 UTC. Target 1246 outcome is not available and was not read.

## Data and execution checks

- Round 1245 official result used as the new completed draw: **4, 5, 25, 28, 32, 42 + bonus 12**.
- Training cutoff for target 1246: round **1245** only; no future row was used.
- 1..1245 snapshot rows: **1,245**.
- Snapshot SHA-256: `e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4`.
- Semantic SHA-256 through 1245: `92b52296d340330ddeb0d7325701ae14bd2c10b673ae8775f1de2abee0c6056a`.
- The first 1,244 rows reproduce the frozen V4 semantic hash `a49e74f93e2335a1d7462bbe1424f056f35fd9006499ecf3797dec791324761f`.
- The frozen V4 formulas were reimplemented directly from `prospective_engine_v4.py` and first tested against target 1245. Both 1245 expanding/rolling portfolios and every model top ticket reproduced exactly. Only after this PASS was target 1246 computed.

## Research guardrails carried into the decision

The 2026-10-16 recovery run found no B component with a positive 95% paired mean-hit interval versus the fresh same-target random baseline. Pair/triple BH q<0.05 survivors remained 0/0 and leakage failures were 0. Therefore no B, pair or triple signal is promoted into a new weighting rule for target 1246.

## Frozen V4 target-1246 portfolios

### Expanding
1. G: `1 13 18 26 34 38`
2. C: `2 4 13 18 32 34` — V4 overlap fallback, candidate rank 8
3. S: `5 8 19 24 29 36`

### Rolling300
1. G: `6 12 15 21 22 29`
2. C: `1 5 7 9 12 19`
3. S: `6 13 20 24 26 35`

## Primary-mode update

The existing decision rule is kept: first compare the 200-target portfolio 3+ count, then max-hit sum, mean ticket hits, four-block variance, and finally expanding on a complete tie.

For target 1246 the completed comparison window is shifted from 1045..1244 to **1046..1245**. This update is exact: remove the already recorded target-1045 row and add the newly observed target-1245 result.

- Expanding: 3+ portfolio rounds **20**, 4+ rounds **1**, max-hit sum **289**, total ticket hits **472/600**, mean **0.786667**.
- Rolling300: 3+ portfolio rounds **12**, 4+ rounds **0**, max-hit sum **291**, total ticket hits **489/600**, mean **0.815000**.

The deterministic rule therefore selects **expanding** at criterion 1 (`20 > 12`). This is a purchase-policy tie-break result, not evidence that expanding has a verified predictive advantage.

## Five-line purchase extension

The frozen V4 protocol itself remains a three-line research portfolio. Because the requested real purchase is five lines, the three primary expanding lines are kept unchanged and two extra lines are selected only from the alternate rolling300 V4 candidate pools. The extension does not change V4 formulas or model rankings.

Extra-line optimization is outcome-independent: require distinct model families, then maximize total five-line number coverage; minimize total line intersections, repeated pairs and candidate-rank cost. The selected extras are both rank 2:

- rolling300 V4_G rank 2: `6 12 15 21 22 33`
- rolling300 V4_S rank 2: `9 11 16 24 30 40`

This produces 26 distinct covered numbers across 30 slots and only four total number-overlaps across the ten pairwise line comparisons. The only 3-number overlap is already inside the frozen primary expanding portfolio and is not cosmetically altered.

## Actual purchase final 5 — round 1246

1. **1 13 18 26 34 38**
2. **2 4 13 18 32 34**
3. **5 8 19 24 29 36**
4. **6 12 15 21 22 33**
5. **9 11 16 24 30 40**

These five lines are now the sealed purchase record for this V1 decision. They must not be changed after the target result is known.

## Exact structural null check

Enumerating all `C(45,6)=8,145,060` possible fair outcomes for these exact five lines gives:

- expected total hits across the five lines: **4.0**
- any line 2+: **65.698779%**
- any line 3+: **11.446693%**
- any line 4+: **0.692211%**
- any line 5+: **0.014426%**
- any line 6: **0.0000613869%**

For reference, five independently uniform tickets have exact any-line 3+ probability **11.362355%**. The small difference is a diversification/overlap property only; it is not predictive evidence.
