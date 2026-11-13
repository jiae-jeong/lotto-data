# Superseding correction to the 2026-11-13 policy reversion record

**Recorded:** 2026-11-14 (KST)

## Finding

The finding in POLICY_CHANGE_REVERSION_2026-11-13.md that no user approval existed for changing the weekly output from five lines to three was incorrect. The user's 2026-11-13 instruction explicitly requested changing the weekly number delivery to three lines from the following week and completing verification by Thursday for Friday delivery.

The original target-1251 three-line policy was therefore user-authorized. The subsequent reversion was based on incomplete conversation context and must not override that later explicit instruction.

## Corrected effective policy

- Targets through 1250 retain their original five-line records, studies, manifests, and delivery evidence unchanged.
- Target 1251 onward uses exactly three six-number lines for weekly purchase output.
- The existing Friday 08:00 KST delivery automation and schedule remain enabled and unchanged. Thursday preparation uses the existing daily research schedule; no separate Thursday automation is created.
- The strict gate is not relaxed: all four adjusted CI lower bounds must be strictly positive against the target-specific exact geometry-matched null, with family alpha 0.05, per-metric alpha 0.0125, and any2 positive 50-target block share at least 0.65. Keep cutoff-safe nested/rolling validation, the final remainder block, leakage checks, and prospective confirmation.
- Five-line research and five-line STRICT_PASS_READY artifacts are not evidence of three-line purchase readiness for target 1251 onward.
- Until a dedicated three-line research/validation path passes every required gate, the status remains NOT_READY and no final purchase lines may be issued. No random or fallback lines are permitted.

This correction supersedes the unsupported “no user approval” finding without altering historical target-1250 evidence or deleting/changing the existing Friday delivery task.
