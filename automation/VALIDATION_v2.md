# Validated daily research v2 — 2026-10-12

Current-machine checks:

- Python 3.12.14 / NumPy 2.3.5; installation refresh and dependency check passed.
- Published regime-study verifier independently replayed 10,140 inner policies, 1,935 nested selections, 5,160 new-ticket hits and 128 metric rows on a separate copy; original 24 publication files were unchanged.
- Read-only readiness validated the 23 manifest-listed published content files and 1..1245 data-quality snapshot.
- Sixteen synthetic contract tests passed: altered hashes/source, zero-case completion, missing result/report, duplicate and renamed experiments, completed-study replay, path safety, protected existing result, independent-task fallback, prefix-only tail selection, overlap weighting, exact-binomial moments and explicit non-readiness on a wrong/missing dependency or missing empirical source.
- New E010 experiment actually executed three weighting policies x645 unique targets; all 7,740 control/policy records and 12 metric rows were independently checked. The three new policies' 36 multiplicity-adjusted comparisons produced no confirmed positive advantage; preserve the result rather than retune it after evaluation.
- Workflow YAML, scheduled timezone, Python syntax and embedded shell syntax passed. YAML command quoting was corrected before publication.
- All 376 pre-existing tracked files stayed byte-identical. This change adds files; it does not alter frozen studies, raw data, protocol, legacy workflow or candidate/recommendation records.

GitHub actually executed the nested-tail job on the marked publication push, validated 1,290 nested decisions/7,095 records, and committed its new files as `d3849b6af35504d22f7081579f8dd307d31d25c2`. The hosted workflow badge reported passing. The exact-power job remains separately registered and is not claimed as already executed. No future forecast was generated. A successful first hosted run does not prove every future run will succeed or start without delay. The deterministic queue is finite, and exhaustion must never become a fabricated new-study completion.

Dependency installation is optional only for the independent theory fallback: a missing/wrong NumPy or blocked empirical source is reported as EMPIRICAL_BLOCKED, never empirical readiness PASS; empirical bootstrap refuses an incorrect runtime, and the runner may advance to the stdlib-only power question. Unit/causality/completion gates are mandatory and not bypassed.

Cloud scripts/instructions are configuration drafts until the environment is published through the product. Git publication, current-machine validation and cloud-snapshot activation are distinct operations.
