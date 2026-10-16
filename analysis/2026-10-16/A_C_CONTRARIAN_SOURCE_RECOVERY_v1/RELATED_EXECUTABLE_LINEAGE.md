# Related executable lineage recovered during A/C/contrarian search

These are real surviving executable sources near the historical A/C/contrarian concepts. They are preserved as **related lineage only**, not renamed as the missing legacy models.

## S001–S008 study_batch_001

Authoritative surviving source:

`research/expansion_framework_v1/studies/study_batch_001/run_batch.py`

Recorded raw SHA-256 in the prior recovery package:

`974f5163b95e38389d857f6ec6a2cafdb1c4b847c869f33d49808902914e3eab`

Recovered fixed definitions:

- S001 multi-window frequency: standardized occurrence rates over windows 10/30/100/300, equal average, top six with lower-number tie break.
- S002 gap-regime hazard: age bins 0,1,2,3–5,6–10,11+, pooled historical interval termination/risk, Beta-style shrinkage strength 20 toward 6/45.
- S003 momentum transition: previous20 → recent20 hot/cold state transition, smoothed next-draw rate with strength 20 toward 6/45.
- S004 conditional probability: next occurrence conditional on count in trailing 10 draws, shrinkage strength 30 toward 6/45.
- S005 structure transition: candidate bank seed 20261008, size 5000; Laplace-smoothed log likelihood over eight structure categories; lexical tie break.
- S006 pair residual node: expected pair count `(5/6)*(45/44)*F_a*F_b/n`; standardized residual `(O-E)/sqrt(E)` summed at each number.
- S007 triple residual node: expected triple count `(5*4/6^2)*(45^2/(44*43))*F_a*F_b*F_c/n^2`; standardized residual summed at each number.
- S008 family-balanced hybrid: code attempts to blend S001–S007, but prior source inspection verified that its S005 contribution was implemented as constant vectors and therefore cannot alter relative number ranking. Do not treat S008 as a valid recovered structural blend.

The source itself labels this batch post-hoc and requires validation; it is not the historical A model.

## V3 select_portfolio

Authoritative surviving source:

`research/1245_final_pipeline_v3/prepare_1245_final_three_lines_v3.py`

Recorded raw SHA-256 in the prior recovery package:

`09d2cf7f3c9002db906669371d9e2b580d592053b035d891e6c1202e05704e46`

Recovered selector mechanics:

- number-level consensus uses six distinct families: frequency, gap/time, momentum, conditional, structure, relationship residual.
- relationship residual averages S006/S007 ranks as one family.
- S008 is excluded from the consensus to avoid double-counting the hybrid.
- equal-family rank consensus forms the central portfolio line.
- supplemental source tickets must come from distinct signal families and are selected by a deterministic tuple prioritizing structure coverage, union coverage, then lower overlap and lexical source IDs.

This is a later V3 portfolio selector. It is **not** relabelled as historical C.

## V4_C

`V4_C` exists as a later registered model identifier in the preserved V4 lineage. Its existence does not prove identity with the earlier historical Model C, and this recovery does not make that substitution.

## Recovery boundary

The executable lineage above can support future newly-versioned research because formulas and source provenance exist. It cannot fill missing historical A/C/contrarian implementation fields by assumption. Any successor built from these sources must receive a new model/version name and fresh walk-forward/random-baseline validation.
