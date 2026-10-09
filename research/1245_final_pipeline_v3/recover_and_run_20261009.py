"""Run the existing V3 candidate generator and selector using repository inputs.

This recovery runner deliberately reports that the original external prospective
seal and B-model artifacts are unavailable. It does not claim the sealed V3 gate
passed, and it writes a new dated output directory without replacing V3 artifacts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT_BASE = ROOT / "research" / "1245_final_pipeline_v3"
OUT = OUT_BASE / "recovery_run_20261009"
RAW = ROOT / "lotto_data.csv"
STUDY = ROOT / "research" / "expansion_framework_v1" / "studies" / "study_batch_001" / "run_batch.py"
FRAMEWORK = ROOT / "research" / "expansion_framework_v1"
V3 = HERE / "prepare_1245_final_three_lines_v3.py"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def validate_data():
    with RAW.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        expected = ["round", "date", "no1", "no2", "no3", "no4", "no5", "no6", "bonus"]
        if reader.fieldnames != expected:
            raise ValueError(f"header mismatch: {reader.fieldnames}")
        rows = list(reader)
    rounds, dates = [], []
    for row in rows:
        r = int(row["round"])
        nums = [int(row[f"no{i}"]) for i in range(1, 7)]
        bonus = int(row["bonus"])
        if len(set(nums)) != 6 or any(n < 1 or n > 45 for n in nums):
            raise ValueError(f"invalid main numbers at round {r}")
        if bonus < 1 or bonus > 45 or bonus in nums:
            raise ValueError(f"invalid/semi-duplicate bonus at round {r}")
        rounds.append(r)
        dates.append(row["date"])
    if rounds != list(range(1, len(rows) + 1)):
        raise ValueError("rounds are not unique and consecutive from 1")
    if not rows or rounds[-1] != 1244:
        raise ValueError(f"expected latest round 1244, found {rounds[-1] if rounds else 'none'}")
    return rows, dates[-1]


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="20261009",
                        help="unique output suffix (letters, numbers, hyphens, underscores)")
    run_id = parser.parse_args().run_id
    if not run_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in run_id):
        parser.error("--run-id may contain only letters, numbers, hyphens, and underscores")
    OUT = OUT_BASE / f"recovery_run_{run_id}"
    OUT.mkdir(parents=True, exist_ok=False)
    rows, latest_date = validate_data()
    sys.path.insert(0, str(FRAMEWORK))
    study = load_module("recovery_study_batch001", STUDY)
    study.DATA = RAW
    draws = study.load_draws_through(RAW, 1244)
    if [d.round for d in draws] != list(range(1, 1245)):
        raise ValueError("model loader did not return exactly rounds 1..1244")
    bank = study.candidate_bank()
    if len(bank) != 5000:
        raise ValueError(f"candidate bank size mismatch: {len(bank)}")
    study.BASE_PROFILES = {q: study.prof(q, ()) for q in bank}
    model_results = study.make_models(draws, bank)
    v3 = load_module("recovery_v3_selector", V3)

    model_rows = []
    for item in study.MODELS:
        model_id, name, family, description = item
        ticket, scores = model_results[name]
        ticket = tuple(sorted(map(int, ticket)))
        if len(ticket) != 6 or len(set(ticket)) != 6 or any(n < 1 or n > 45 for n in ticket):
            raise ValueError(f"invalid ticket from {model_id} {name}")
        model_rows.append({"model_id": model_id, "model": name, "family": family,
                           "candidate_numbers": " ".join(map(str, ticket)),
                           "generation_rule": description, "generated_from_rounds": "1-1244",
                           "candidate_ticket_only_not_backtest_result": "YES"})

    candidates = {}
    for model_id, name, family, _ in study.MODELS:
        ticket, scores = model_results[name]
        candidates[model_id] = {"model_name": name, "ticket": tuple(sorted(map(int, ticket))),
                                "scores": list(scores), "family": family}
    lines = v3.select_portfolio(candidates, study)
    if len(lines) != 3 or any(len(line["numbers"]) != 6 for line in lines):
        raise ValueError("selector did not return exactly three six-number lines")

    model_out = OUT / "model_candidates.csv"
    with model_out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(model_rows[0]))
        w.writeheader(); w.writerows(model_rows)

    final_rows = []
    for line in lines:
        final_rows.append({"line": line["line"], "numbers": " ".join(map(str, line["numbers"])),
                           "model_sources": line["model_sources"], "signal_sources": line["signal_sources"],
                           "selection_rule": line["rule"],
                           "validation_status": "RECOVERY_RUN_UNSEALED_EXTERNAL_PROSPECTIVE_ARTIFACTS_MISSING"})
    final_csv = OUT / "final_three_lines_1245_v3_recovery.csv"
    with final_csv.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(final_rows[0]))
        w.writeheader(); w.writerows(final_rows)

    pairwise = []
    for i in range(3):
        a = set(lines[i]["numbers"])
        for j in range(i + 1, 3):
            b = set(lines[j]["numbers"])
            pairwise.append({"line_a": i + 1, "line_b": j + 1,
                             "intersection": " ".join(map(str, sorted(a & b))),
                             "intersection_count": len(a & b), "jaccard": len(a & b) / len(a | b)})
    with (OUT / "portfolio_overlap.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(pairwise[0])); w.writeheader(); w.writerows(pairwise)

    issues = [
        "Original pipeline --check-only failed with 18 blocking errors in this environment.",
        "The original pinned baseline manifest and B-model backtest/recent/candidate artifacts are absent from the GitHub repository.",
        "The prospective protocol, registry, model manifest, and seal referenced by V3 are absent from the GitHub repository.",
        "The raw CSV shipped with the repository is available and validates as rounds 1..1244; its SHA differs from the historical V3 machine-specific SHA.",
        "The V3 generator source run_batch.py and selector are executed, but no missing seal/hash checks are represented as passed.",
        "A/B/C/contrarian unified validation and the old local B report's backtest rerun were not performed; only stored S001-S008 study summaries are available.",
        "All historical study summaries are post-hoc and do not establish predictive advantage; exact random baseline is mean 0.8 hits and P(2+) 17.5308% per ticket.",
    ]
    report = ["# 1245 recovery execution report", "", "Date: 2026-10-09 (Asia/Seoul)",
              "", "## Execution status", "", "- Candidate generator: executed from repository `run_batch.py` using rounds 1..1244.",
              "- V3 selector: executed; produced exactly three six-number lines.",
              "- Original sealed V3 gate: NOT PASSED (`--check-only` returned 18 blockers).",
              "- Interpretation: recoverable algorithm execution, explicitly unsealed due missing external artifacts.",
              "", "## Input validation", "", f"- Raw file: `{RAW.relative_to(ROOT).as_posix()}`",
              f"- SHA-256: `{sha256(RAW)}`", f"- Rows: {len(rows)}; rounds 1..{len(rows)} consecutive, unique; latest round 1244, date {latest_date}.",
              "- All six main numbers are unique and in 1..45; bonus is in range and separate.",
              "- Target result for 1245 was not read.", "", "## Final lines", "",
              "| Line | Numbers | Sources | Rule |", "|---:|---|---|---|"]
    for row in final_rows:
        report.append(f"| {row['line']} | {row['numbers']} | {row['model_sources']} | {row['selection_rule']} |")
    report += ["", "Selection reasons: line 1 is the equal-family-rank consensus across S001-S007, with S006/S007 averaged as one relationship family and S008 excluded as a duplicate hybrid vote. Lines 2–3 are distinct-family registered model tickets selected by the existing V3 selector for structure coverage, portfolio number coverage, overlap, and deterministic model-ID ties.",
               "", "## Model candidates", "", "The eight actual generated tickets and their registered rules are in `model_candidates.csv`. Model-level historical evidence is summarized in the already committed `research/expansion_framework_v1/studies/study_batch_001/model_metrics.csv` and `rolling300_metrics.csv`; these were read as stored research results, not recomputed during this recovery run. The study report marks the evidence post-hoc/validation-required. The separate B-model report is present, but its prediction/classification CSVs are not.",
               "", "## Blocking errors and outstanding verification", ""]
    report += [f"- {item}" for item in issues]
    report += ["", "## Re-run", "", "From the repository root run:", "", "```powershell",
               "& 'C:\\Users\\admin\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' research\\1245_final_pipeline_v3\\recover_and_run_20261009.py --run-id rerun1",
               "```", "", "This runner refuses to overwrite its output directory. Use a new `--run-id` for another run.", ""]
    (OUT / "EXECUTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    (OUT / "run_metadata.json").write_text(json.dumps({"raw_sha256": sha256(RAW), "raw_rows": len(rows),
        "latest_round": 1244, "model_count": len(model_rows), "final_line_count": len(final_rows),
        "generator": str(STUDY.relative_to(ROOT)), "selector": str(V3.relative_to(ROOT)),
        "gate_status": "NOT_PASSED_18_BLOCKERS", "result_round_1245_read": False}, indent=2), encoding="utf-8")
    print(f"RAW_VALIDATED rows={len(rows)} sha256={sha256(RAW)}")
    print(f"CANDIDATES_GENERATED={len(model_rows)}")
    for line in final_rows:
        print(f"LINE_{line['line']}={line['numbers']} SOURCES={line['model_sources']}")
    print(f"FINAL_LINES={len(final_rows)}; SEALED_V3_GATE=NOT_PASSED; OUTPUT={OUT}")


if __name__ == "__main__":
    main()
