# Policy correction — restore the approved Friday five-line delivery

**Recorded:** 2026-11-13 (KST)

## Finding
The following commits introduced an unapproved target-1251 change from the existing weekly five-line Friday purchase output to three lines with a Thursday-first validation deadline:

- `dc8810e62ef264f0ee73631c6792f2fa737195b6` — appended a three-line / Thursday-deadline policy to `LOTTO_PROJECT_PROTOCOL.md`
- `5f1071d83df211f7d2816cdb9e640c5e7869e4b8` — appended a three-line purchase policy to `AGENTS.md`
- `949b0b765ad8a5b8f3a77e62fb02c3715e802b65` — added `THREE_LINE_POLICY_CHANGE_2026-11-13.md`
- `c1f5fb314065c0ff4289a3060ca17d0f5acfe762` — added `THREE_LINE_POLICY_1251_PLUS.json`

The available prior user instruction explicitly retained **exactly five lines for the weekly Friday final delivery**. No user approval for changing five lines to three, adding a Thursday-first deadline, or replacing the weekly process was found. The commits' assertion that this was a user-requested change is therefore unsupported.

## Restoration performed
- Restored `AGENTS.md` to the prior approved baseline, with an explicit safeguard that research-only three-ticket studies do not change weekly purchase output.
- Restored `LOTTO_PROJECT_PROTOCOL.md` to the prior baseline and updated its active weekly-output section to the user-approved five-line Friday policy.
- Removed the two unapproved target-1251 three-line policy files from the active tree. Their original commits remain in Git history for auditability.
- Preserved the existing Friday delivery workflow and its schedule. No workflow file, automation schedule, notification, freeze/seal mechanism, research threshold, historical recommendation, or lottery source data was changed.

## Effective policy
The weekly purchase output remains **five six-number lines delivered on Friday through the existing workflow**. Daily research and experimental three-ticket studies do not alter that policy. Any future line-count, delivery-day, or automation change requires explicit user approval.
