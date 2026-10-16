# Git root-history audit

The repository root history was explicitly traced to the first commit during the 2026-10-16 recovery.

- Root commit: `1efa5bbaa89d6b747da414d1289eb641cc2856a4`
- Date: 2026-10-01
- Message: `Create lotto_data.csv`
- Parents: none
- Content change: creation of `lotto_data.csv` as an empty one-line file.

The next observed data-population commit `9058e4d963585f5fef6f124c09b54af979d1f4b0` modifies only `lotto_data.csv`.

The October 6 commit `46aa6c17d110b9bb1588d6a68d4c47c34b1c0f5e` adds the first preserved model/project-state document found in this lineage, and that document records the B-model definitions/results.

Therefore there is no earlier reachable Git commit before the B-era project state that can contain a historical A/C/contrarian source file: the repository itself begins on October 1 with only `lotto_data.csv`.

This does not prove that an A/C/contrarian implementation never existed outside GitHub. It establishes that the original Git history cannot recover it.
