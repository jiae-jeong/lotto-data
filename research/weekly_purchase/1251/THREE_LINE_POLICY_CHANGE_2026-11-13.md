# Target 1251 onward — three-line weekly purchase policy

**Effective date:** 2026-11-13  
**First target:** 1251 (expected draw date 2026-11-21)  
**Delivery target:** Friday 2026-11-20, 08:00 KST, using the existing Friday automation  
**Preparation deadline:** Thursday 2026-11-19 (the existing daily 08:00 KST research automation runs that day)

## User-requested output change

The weekly purchase output is changed from five lines to **exactly three lines**, six main numbers per line. This applies prospectively from target 1251. All earlier five-line recommendations, purchases, studies, preregistrations, manifests, and delivery records remain unchanged.

No daily study or Thursday preparation run may reveal the purchase lines. Friday is the delivery point.

## Three-line exact uniform reference

For three pairwise-disjoint six-number tickets, the portfolio union is 18 numbers. Under a uniform draw of six distinct numbers from 1..45, exact combinatorial enumeration gives:

| Metric | Exact reference |
|---|---:|
| Mean max-hit across 3 lines | 1.514256248573 |
| Probability at least one line has 2+ hits | 0.474976243269 |
| Probability at least one line has 3+ hits | 0.071354907146 |
| Expected winning numbers in the 18-number union | 2.400000000000 |

These constants apply only to the disjoint union18 geometry. A proposed portfolio with cross-line overlaps must be evaluated against an exact null preserving its actual number-to-line incidence pattern; do not use the union18 constants for an overlapping portfolio.

The strict promotion rules do not change: all four Bonferroni-adjusted moving-block bootstrap CI lower bounds (max-hit, any2, any3, union coverage) must be strictly above zero versus the appropriate exact geometry-matched null; family alpha remains 0.05, per-metric alpha 0.0125; positive non-overlapping 50-target any2 block share must be at least 0.65; keep the final incomplete block; cutoff-safe nested/rolling walk-forward and prospective confirmation remain mandatory.

## Thursday preparation checklist

For every target:
1. Verify official/latest draw data, row/round continuity, six distinct main numbers in 1..45, no future leakage, source provenance, SHA256 and Git blob.
2. Freeze the champion policy before reading any target outcome. Separate candidate ranking from three-ticket construction.
3. Evaluate exactly three tickets per target against the correct target-specific exact overlap-geometry null and matched random comparators.
4. Calculate max-hit, any2, any3, winning-union coverage, 50-target block stability, adjusted confidence intervals, overlap and multiplicity/selection-bias diagnostics.
5. Validate the final three lines: 3×6 numbers, 1..45, no within-line duplicates, three distinct lines, deterministic version and hashes.
6. Freeze/seal the exact lines only if every strict condition passes. Store all results, including failure status, append-only.

Thursday status is one of:
- THURSDAY_VERIFIED_3_LINE_READY (all required checks pass and exact three lines sealed);
- STRICT_FAIL (a predeclared predictive gate fails);
- NOT_READY (source, hash, computation, leakage, or freeze verification incomplete).

Do not treat computation completion as predictive PASS.

## Friday delivery checklist

Friday 08:00 KST must read Thursday's saved status, revalidate the data cutoff and hashes, then deliver the exact same three sealed lines only when THURSDAY_VERIFIED_3_LINE_READY remains valid. Do not start fresh model exploration or tune numbers on Friday. If status is STRICT_FAIL or NOT_READY, report no verified final purchase lines and show the concrete failing/missing checks; do not issue random, fallback, or unvalidated candidates as final purchase numbers.

Any actual six-number lines shown to the user are delivery events and must be appended to DELIVERY_LOG with exact text, timestamp, model/version, reason and status. Never infer purchase confirmation.

## Existing automation limitation observed 2026-11-13

The current account automation service returned a plan-limit error while editing existing saved automation prompts and rejected an additional scheduled task. The existing daily 08:00 KST research and Friday 08:00 KST delivery schedules were not disabled or replaced. This file and the MASTER/AGENTS policy amendments are the authoritative updated instructions for those runs to read. Do not claim a new Thursday automation was created.
