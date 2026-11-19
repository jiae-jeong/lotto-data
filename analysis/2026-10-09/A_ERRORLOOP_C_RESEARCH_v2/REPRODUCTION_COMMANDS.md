# Actual commands and safe reproduction

Actual invocations are recorded in ACTUAL_EXECUTION_RESULT.json, EXTENSION_EXECUTION_RESULT.json and execution logs. The compiled source search ran `python work/search_a_sources_20261009.py`; scope/metadata are in SOURCE_SEARCH_EXECUTION_RECORD.json.

Scientific engine takes `--repo PATH --out NEW_EMPTY_VERSION_DIR`. Copy the pinned code/config/protocol, START_STATE/source-search evidence and corresponding execution plan seal to a fresh version directory first; it uses exclusive file creation and refuses to overwrite existing outputs. The --repo input must have the exact raw hash and frozen B/MC references. No A/B/C model code is executed by the engine.

Do not invoke it with this completed directory as --out. The preserved extension/verifier scripts record their actual original paths; adapt paths only in a new version before freezing/running it. Do not label a new source search as recovered originals without exact provenance. No V3 check-only, new tickets or 1245 outcomes are needed.

Git publication uses the existing authenticated local Git CLI and per-command OpenSSL, exact new paths, byte-preserving staged-blob checks, normal fast-forward push and independent raw GitHub HTTPS downloads. User Git global config is unchanged.
