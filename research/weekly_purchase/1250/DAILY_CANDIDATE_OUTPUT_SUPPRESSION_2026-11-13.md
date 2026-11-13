# Daily candidate-output suppression audit — 2026-11-13

## Finding

The 09:49 KST daily research artifact `analysis/2026-11-13/FIVE_ROLE_RESEARCH_1250_V9.json` persisted current line-level portfolio details (`final_lines`, per-role ticket/number details, current model predictions, and global number support) even though the combined strict gate was `STRICT_PASS_NOT_READY`.

The same run did **not** create a `STRICT_PASS_READY` file, did not freeze/seal a purchase selection, and did not authorize a weekly purchase output. The issue was unnecessary publication of research-only line-level candidates in a daily artifact and workflow log, contrary to the daily no-candidate-output rule.

Original Git blob SHA of the unsanitized JSON: `dc001c78b627c9889d3f8e0bae7c01fe982e2fee`.

## Correction

- `automation/five_role_research_v9.py` now keeps the current five-line test portfolio only in a runner-temporary payload, records its SHA-256, and omits line-level tickets, per-number details, current predictions, and global support from the published research JSON and stdout.
- The daily workflow verifies the temporary payload hash and uses its lines only if **both** model-level and portfolio-level strict gates pass. It then writes them only to `STRICT_PASS_READY`; otherwise it deletes the temporary payload.
- The already-published 2026-11-13 research JSON was sanitized while preserving aggregate scorecard, inference, gate failures, and integrity fields.
- The daily report now distinguishes an internal transient gate-evaluation portfolio from a purchase recommendation or delivered final lines.

## Preserved

No source data, historical purchase evidence, preregistration, model weights, thresholds, alpha, block size, comparison baseline, weekly five-line Friday policy, schedule, freeze/seal rule, or Friday delivery workflow was changed.

The push-triggered DAILY MASTER rerun is the validation for this correction; its run result and resulting commit are recorded after completion.
