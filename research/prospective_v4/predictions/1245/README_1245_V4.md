# V4 prediction registration: draw 1245

Status: REGISTERED_UNEVALUATED. Actual result: NOT READ / NOT USED.
Freeze commit: 746efc843d53dff4e61394e26d458ea3f50c93e4
Freeze seal SHA-256: 6a018e3036187a26ac9bcffda9fd7379d65d86cde84514faa08f4ea349b0f4bb
Data cutoff: 1244; raw SHA-256: 243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f.
Execution kind: official. Generated UTC: 2026-10-09T05:23:31.820932+00:00.

The immutable frozen engine was called once in this invocation for both registered modes and all eight models. A Python profile return observer captures scores without replacing or modifying model computations. Reproduction invocation must use determinism_verification_only in a separate output directory; it is not another official selection.

Both expanding and rolling300 portfolios are preserved because the freeze defines one three-line portfolio per mode and does not name a primary buying mode. This prediction never replaces historical V3 candidate lines. Portfolio order G, C, S; equal weights; overlap <=2 priority and frozen fallback. All structure diagnostics are descriptive, with no veto or manual substitutions.

Number scores/ranks are defined for F/G/C/M/P/T. U has equal inclusion probability and seed generation order, not a learned number ranking. S ranks tickets, not individual numbers; those undefined fields remain explicit. Full 10,000-bank S ticket scores are preserved for each mode.

Artifacts require raw/freeze hashes and independent verification before publication. No actual target outcome input or score is present. Publication commit/time and independent pre-draw eligibility are recorded externally to avoid circular Git/hash references. Commit timestamps alone are not independent deadline proof. V3 remains SEALED V3 GATE NOT PASSED.

Reproduction example: python run_prediction_1245_v4.py --data <frozen-repository>/lotto_data.csv --output-dir <fresh-verification-directory> --execution-kind determinism_verification_only
