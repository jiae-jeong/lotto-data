# Related source formulas and inspect-only findings

## Identity and provenance

`LOTTO_PROJECT_PROTOCOL.md` sections 3/5/6 prescribe separated A signals, C combinations of repeatedly verified signals, and research of atypical structures. They do not specify executable legacy A/C/contrarian formulas, weights or selection rules. Local/hash/history metadata are in SOURCE_EVIDENCE_CATALOG.csv. The old `C:\Users\user` folders do not exist on this PC. The current remote has only main. Accessible historical backtest predictions do not prove that recommendations were published at those times.

- A_MODEL_ORIGINAL = NOT FOUND. Original A walk-forward = NOT EXECUTED.
- C_MODEL_ORIGINAL = NOT FOUND. Original C walk-forward = NOT EXECUTED.
- CONTRARIAN_MODEL_ORIGINAL = NOT FOUND. Original contrarian purchase performance = NOT EXECUTED.
- Actual recommendation/error-note originals for rounds 1..1244 = SOURCE NOT FOUND. No missed-number reasons or purchase performance were invented.
- The `model_a` column in correlations denotes the first member of a pair of compared models. `V4_C` is a registered V4 ID. Neither is proof of legacy A/C identity.

## Related versions actually found (preserved, NOT executed in this task)

Study batch 001 `run_batch.py` registers S001..S008, using 1..t-1 for historical targets 201..1244; fixed rolling300 results cover 501..1244. These are post-hoc experiments; all eight surviving-model entries are NONE_PROMOTED. The original absolute source paths are on a missing old user profile.

- S001: equal average of standardized frequencies at windows 10/30/100/300, top-six score ordering with lower-number ties.
- S002: pooled age-regime termination/risk counters, Beta prior strength 20 and prior probability 6/45; top-six scores. Definition in source is preserved, not retuned.
- S003: hot/cold transitions from previous20 to current20; (historical transition hits +20*6/45)/(transition exposure+20).
- S004: next occurrence conditioned on trailing10 count; (hits+30*6/45)/(exposure+30).
- S005: bank seed 20261008, size5000; sum of eight Laplace-smoothed structure transition log probabilities; lexical tie-breaking. The bank is NOT generated today.
- S006: pair residual sums at each node; E=(5/6)*(45/44)*F_a*F_b/n; residual=(O-E)/sqrt(E).
- S007: triple residual sums; E=(5*4/6^2)*(45^2/(44*43))*F_a*F_b*F_c/n^2.
- S008: source computes six rank vectors (S001,S002,S003,S004,S006,S007), then appends **45 constant vectors** in a loop over numbers: each vector has every column 45 if that loop's number belongs to the S005 ticket, else every column 0. There are always six positive constant vectors. Therefore s8[i]=(sum of six ranks at i +270)/51. The structure contribution is constant across all number columns and cannot change their relative ordering. This is a VERIFIED algebraic/code-inspection finding, not a newly executed historical S008 backtest. No original file is fixed here.

V3 `select_portfolio` is a distinct related selector: frequency/gap/momentum/conditional/structure/relationship six-family rank consensus, averaging S006/S007 as one relationship family and excluding S008 as a duplicate hybrid; supplemental distinct-family tickets minimize the tuple (-structure_coverage,-union_coverage,total_overlap,left_id,right_id). This implementation is not relabelled as recovered legacy C. V3 gate remains SEALED V3 GATE NOT PASSED; V3 check-only was not run.

V4 formulas and sealed 1245 predictions remain unchanged; V4_C is not relabelled as the old C model. No 1245 result, candidate generation, purchase-line generation or automation change occurs in this research.
