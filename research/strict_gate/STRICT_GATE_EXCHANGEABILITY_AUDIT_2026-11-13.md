# Strict-gate exchangeability audit — 2026-11-13

## Decision

Do **not** change the strict thresholds, null, multiplicity correction, or block-stability requirements to force a PASS. Under the project's stated fair, independent six-of-45 draw model, the expected advantage of any deterministic pre-draw five-ticket policy over the exact geometry-matched random null is zero.

This is not a claim that a finite historical sample can never cross the gate. It can cross by chance. Such a crossing is not a model improvement unless it survives new, prospective data.

## Exact result reproduced today

For five disjoint six-number tickets with a 30-number union, there are:

- `C(45,6) = 8,145,060` possible winning sets.
- 15 numbers are outside the portfolio; 30 are inside.
- If the five ticket hit counts are `h1..h5`, the exact number of winning sets giving that composition is
  `C(6,h1) C(6,h2) C(6,h3) C(6,h4) C(6,h5) C(15, 6 - sum(hi))`,
  for `sum(hi) <= 6`.

The independent standard-library enumeration reproduced the exact null:

| Metric | Exact expectation |
|---|---:|
| Mean portfolio max-hit | 1.834653151726 |
| Any line with 2+ hits | 70.9476050514% |
| Any line with 3+ hits | 11.8679297636% |
| Any line with 4+ hits | 0.6967413377% |
| Winning numbers in the union | 4.000000000000 |

The distribution depends on the ticket overlap geometry, not on the number labels. Therefore, for any *fixed* five disjoint tickets, relabeling the 45 numbers leaves the complete hit distribution unchanged. If a policy selects its tickets from past draws only, then conditional on that past, its next ticket set is fixed; an independent uniform next draw has the same exact distribution.

The same exchangeability argument applies to overlapping portfolios when the random comparator preserves the **exact same overlap geometry**. Geometry can change the metric distribution relative to a different geometry, but it cannot create predictive information about the six winning labels.

## What the current records show

1. The V54 portfolio for target 1248 was recorded as `STRICT_PASS` on 847 historical targets. The frozen replay after adding the next target (1249; 848 targets) failed the same gate: Bonferroni lower CI for any2 became `-0.000945`, despite max-hit and any3 lower bounds remaining positive. This is a clear example of a historical pass not persisting when another outcome is added.
2. V83 at cutoff 1248 failed the updated gate because the any3 adjusted lower bound was `-0.005204`.
3. The latest 1250 model validation reports 11 single-ticket models tested and **zero validated models**. The 1250 portfolio gate has no ready file and fails max-hit, any2, any3, union coverage, and 50-round any2 stability.
4. The prior candidate-recall analysis found only small mean lifts versus matched random at K=10..30 (best approximately +0.00553), and no strict portfolio evidence. These are historical exposed results, not prospective confirmation.

## Required model-development change

Stop spending research cycles on allocator geometry as though a different partition can create draw information. Keep geometry research only for operational coverage/overlap preferences, and compare every policy with an exact overlap-matched null.

The only legitimate route to a strict predictive PASS is evidence that the draw process departs from the independent-uniform model in a stable, pre-target-predictable way. Future research must therefore prioritize:

1. verified source/data integrity and draw-process regime changes;
2. preregistered tests for persistent number-level or temporal dependence, with exact/appropriate nulls and multiple-testing correction;
3. a candidate model frozen before a future evaluation window;
4. untouched prospective confirmation across enough future draws to meet the existing confidence-interval and block-stability gate.

Do not promote a policy based on a single lucky window, retrospective model selection, an unmatched random comparator, a relaxed threshold, or a changed null.

## Scope and limits

This audit establishes the mathematical expectation under uniform independent draws. It does not prove that every historical draw was perfectly uniform, and it does not establish that a useful mechanical bias exists. No strict PASS was produced or claimed by this audit. The 1250 strict status remains FAIL / NOT READY.
