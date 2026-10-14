# E044 real purchase intake

Submit a user supplied purchase record as `ROUND_<target_round>.json` in this directory before the registered draw time. `INTAKE_SCHEMA.json` defines the format. Each of the five line objects must include six distinct integers from 1 through 45, a source/model name, a version, and a training cutoff no later than `target_round - 1`. The top-level record must include `purchase: true`, timezone-aware `generated_at` and `submitted_at`, a `training_through_round` cutoff, and a rationale or source reference.

The prospective runner checks that the official endpoint explicitly reports the target as unpublished, the target is the next round after the canonical CSV, and no outcome event exists. It then creates `analysis/prospective_v1/purchases/ROUND_<target_round>.json` with per-line and bundle SHA-256 values using exclusive creation. It records the intake file SHA. After sealing, changing or removing the intake file is rejected. A late intake after official publication is rejected and never sealed. No sample purchase lines are included here.

