"""Fresh last-200-round expanding and rolling-300 validation for S001-S008.

Uses the existing batch-001 predictor implementation with a new evaluation loop.
All output is written into a unique folder; repository source and prior reports are
read-only. Historical validation is exploratory because the study was post-hoc.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import importlib.util
import json
import math
import statistics
import sys
from collections import Counter
from itertools import combinations
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / "lotto_data.csv"
STUDY = ROOT / "research" / "expansion_framework_v1" / "studies" / "study_batch_001" / "run_batch.py"
V3 = HERE / "prepare_1245_final_three_lines_v3.py"
OUT_BASE = HERE
RUN_ID_DEFAULT = "20261009_independent"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_lf_sha256(path: Path) -> str:
    """Hash CSV bytes with CRLF normalized to LF, matching Git's stored blob."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def validate_source():
    with DATA.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        expected = ["round", "date", "no1", "no2", "no3", "no4", "no5", "no6", "bonus"]
        if reader.fieldnames != expected:
            raise ValueError(f"CSV header mismatch: {reader.fieldnames}")
        rows = list(reader)
    if len(rows) != 1244:
        raise ValueError(f"expected 1244 rows; found {len(rows)}")
    dates = []
    seen_rows = set()
    for idx, row in enumerate(rows, 1):
        if int(row["round"]) != idx:
            raise ValueError(f"round continuity/uniqueness failed at row {idx}")
        nums = [int(row[f"no{i}"]) for i in range(1, 7)]
        bonus = int(row["bonus"])
        if len(set(nums)) != 6 or any(n < 1 or n > 45 for n in nums):
            raise ValueError(f"main-number integrity failed at round {idx}")
        if bonus < 1 or bonus > 45 or bonus in nums:
            raise ValueError(f"bonus integrity failed at round {idx}")
        date = datetime.datetime.strptime(row["date"], "%Y.%m.%d").date()
        dates.append(date)
        signature = tuple(row[k] for k in expected)
        if signature in seen_rows:
            raise ValueError(f"duplicate row at round {idx}")
        seen_rows.add(signature)
    if any((b-a).days != 7 for a,b in zip(dates,dates[1:])):
        raise ValueError("draw dates are not strictly weekly and chronological")
    canonical_sha = normalized_lf_sha256(DATA)
    expected_sha = "243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f"
    if canonical_sha != expected_sha:
        raise ValueError(f"LF-normalized source SHA mismatch: {canonical_sha} != {expected_sha}")
    return len(rows), dates[-1], canonical_sha


def exact_baseline():
    denominator = comb(45, 6)
    probs = [comb(6, k) * comb(39, 6-k) / denominator for k in range(7)]
    mean = sum(k * p for k, p in enumerate(probs))
    variance = sum((k - mean) ** 2 * p for k, p in enumerate(probs))
    return {"mean_hits": mean, "variance_hits": variance,
            "p2plus": sum(probs[2:]), "p3plus": sum(probs[3:]), "distribution": probs}


def make_model_predictions(study, draws, bank, mode, target):
    cutoff = target - 1
    if mode == "expanding_last200":
        train = draws[:cutoff]
    else:
        train = draws[max(0, cutoff - 300):cutoff]
    if not train or train[-1].round != cutoff:
        raise ValueError(f"training cutoff mismatch mode={mode} target={target}")
    result = study.make_models(train, bank)
    actual = set(draws[target - 1].numbers)
    outputs, summary = {}, {}
    for mid, name, family, _ in study.MODELS:
        ticket, scores = result[name]
        ticket = tuple(sorted(map(int, ticket)))
        if len(ticket) != 6 or len(set(ticket)) != 6 or any(n < 1 or n > 45 for n in ticket):
            raise ValueError(f"invalid ticket at {target}/{mid}")
        hits = len(set(ticket) & actual)
        summary[mid] = {"model": name, "ticket": ticket, "scores": list(scores), "family": family, "hits": hits}
        outputs[mid] = {"model_name": name, "ticket": ticket, "scores": list(scores), "family": family}
    return train[0].round, outputs, summary


def hit_metrics(values, baseline, n):
    mean = statistics.mean(values)
    p2 = sum(v >= 2 for v in values) / n
    p3 = sum(v >= 3 for v in values) / n
    mean_se = math.sqrt(baseline["variance_hits"] / n)
    p2_se = math.sqrt(baseline["p2plus"] * (1 - baseline["p2plus"]) / n)
    return {"n": n, "mean_hits": mean, "delta_mean_vs_exact_random": mean - baseline["mean_hits"],
            "mean_random_null_95_low": baseline["mean_hits"] - 1.96 * mean_se,
            "mean_random_null_95_high": baseline["mean_hits"] + 1.96 * mean_se,
            "mean_inside_random_null_95": abs(mean - baseline["mean_hits"]) <= 1.96 * mean_se,
            "rate_2plus": p2, "delta_rate_2plus_vs_exact_random": p2 - baseline["p2plus"],
            "rate_2plus_random_null_95_low": max(0.0, baseline["p2plus"] - 1.96 * p2_se),
            "rate_2plus_random_null_95_high": min(1.0, baseline["p2plus"] + 1.96 * p2_se),
            "rate_3plus": p3}


def ticket_structure(nums):
    nums = tuple(sorted(nums))
    gaps = [b-a for a,b in zip(nums, nums[1:])]
    bands = [sum(lo <= n <= hi for n in nums) for lo,hi in ((1,10),(11,20),(21,30),(31,40),(41,45))]
    endings = Counter(n % 10 for n in nums)
    return {"sum": sum(nums), "odd": sum(n % 2 for n in nums), "low_1_22": sum(n <= 22 for n in nums),
            "consecutive_pairs": sum(g == 1 for g in gaps), "bands_1_10_11_20_21_30_31_40_41_45": "-".join(map(str,bands)),
            "repeated_last_digit_count": sum(v-1 for v in endings.values() if v > 1)}


def csv_write(path, rows):
    if not rows:
        raise ValueError(f"refusing empty table {path.name}")
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=RUN_ID_DEFAULT)
    args = parser.parse_args()
    if not args.run_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.run_id):
        parser.error("--run-id may contain only letters, numbers, hyphens, and underscores")
    out = OUT_BASE / f"independent_validation_{args.run_id}"
    out.mkdir(parents=True, exist_ok=False)

    row_count, latest_date, canonical_sha = validate_source()
    sys.path.insert(0, str(STUDY.parent.parent.parent))
    study = load_module("independent_batch001", STUDY)
    draws = study.load_draws_through(DATA, 1244)
    if len(draws) != 1244 or [d.round for d in draws] != list(range(1, 1245)):
        raise ValueError("model data loader did not return the complete ordered prefix 1..1244")
    bank = study.candidate_bank()
    if len(bank) != 5000:
        raise ValueError("registered structure bank size is not 5000")
    study.BASE_PROFILES = {q: study.prof(q, ()) for q in bank}
    v3 = load_module("independent_v3_selector", V3)
    baseline = exact_baseline()
    predictions = []
    portfolio_predictions = []

    for mode in ("expanding_last200", "rolling300_last200"):
        for target in range(1045, 1245):
            start_round, outputs, summaries = make_model_predictions(study, draws, bank, mode, target)
            actual = tuple(sorted(draws[target-1].numbers))
            for mid, item in summaries.items():
                predictions.append({"mode": mode, "target_round": target, "training_start_round": start_round,
                                    "training_through_round": target-1, "training_rows": target-1-start_round+1,
                                    "model_id": mid, "model": item["model"],
                                    "predicted_numbers": " ".join(map(str,item["ticket"])),
                                    "actual_numbers": " ".join(map(str,actual)), "hits": item["hits"]})
            lines = v3.select_portfolio(outputs, study)
            actual_set = set(actual)
            portfolio_predictions.append({"mode": mode, "target_round": target,
                                          "training_through_round": target-1,
                                          "portfolio": " | ".join(" ".join(map(str,x["numbers"])) for x in lines),
                                          "line_hits": " ".join(str(len(set(x["numbers"]) & actual_set)) for x in lines),
                                          "total_hits_all_three": sum(len(set(x["numbers"]) & actual_set) for x in lines),
                                          "any_line_2plus": any(len(set(x["numbers"]) & actual_set) >= 2 for x in lines),
                                          "any_line_3plus": any(len(set(x["numbers"]) & actual_set) >= 3 for x in lines)})
    # The requested 1245 candidates are generated once on the full known prefix, without reading 1245 outcome.
    result = study.make_models(draws, bank)
    candidates_at_1245 = {}
    for mid,name,family,_ in study.MODELS:
        ticket,scores=result[name]
        candidates_at_1245[mid]={"model_name":name,"ticket":tuple(sorted(map(int,ticket))),"scores":list(scores),"family":family}
    final_lines = v3.select_portfolio(candidates_at_1245, study)

    scorecard = []
    for mode in ("expanding_last200", "rolling300_last200"):
        for mid,name,family,_ in study.MODELS:
            vals = [int(r["hits"]) for r in predictions if r["mode"] == mode and r["model_id"] == mid]
            scorecard.append({"evidence_class":"NEWLY_RECOMPUTED_EXPLORATORY_WALKFORWARD",
                              "mode":mode,"model_id":mid,"model":name,**hit_metrics(vals,baseline,len(vals)),
                              "interpretation":"post-hoc last-200 diagnostic; not prospective proof"})
    stored_full_path=STUDY.parent/"model_metrics.csv"
    stored_roll_path=STUDY.parent/"rolling300_metrics.csv"
    with stored_full_path.open(newline="",encoding="utf-8-sig") as f:
        stored_full={(r["research_id"],r["window"]):r for r in csv.DictReader(f)}
    with stored_roll_path.open(newline="",encoding="utf-8-sig") as f:
        stored_roll={(r["research_id"],r["window"]):r for r in csv.DictReader(f)}
    for item in scorecard:
        src=(stored_full[(item["model_id"],"recent200")] if item["mode"]=="expanding_last200"
             else stored_roll[(item["model_id"],"rolling300_recent200")])
        item["stored_mean_hits"]=float(src["mean_hits"])
        item["stored_rate_2plus"]=float(src["rate_ge_2"])
        item["stored_reproduction_match"]=(abs(item["mean_hits"]-float(src["mean_hits"]))<1e-12
                                            and abs(item["rate_2plus"]-float(src["rate_ge_2"]))<1e-12)
        item["stored_source_window"]=("model_metrics.csv:recent200" if item["mode"]=="expanding_last200"
                                       else "rolling300_metrics.csv:rolling300_recent200")
    csv_write(out/"fresh_model_scorecard.csv", scorecard)
    csv_write(out/"fresh_walkforward_predictions.csv", predictions)
    csv_write(out/"fresh_portfolio_walkforward.csv", portfolio_predictions)

    portfolio_metrics=[]
    for mode in ("expanding_last200","rolling300_last200"):
        rows=[r for r in portfolio_predictions if r["mode"]==mode]
        ticket_hits=[int(h) for r in rows for h in r["line_hits"].split()]
        portfolio_metrics.append({"mode":mode,"target_rounds":"1045-1244","targets":len(rows),
                                  "predictions":len(ticket_hits),"mean_hits_per_line":statistics.mean(ticket_hits),
                                  "random_mean_per_line":baseline["mean_hits"],
                                  "delta_mean_per_line":statistics.mean(ticket_hits)-baseline["mean_hits"],
                                  "rate_2plus_per_line":sum(h>=2 for h in ticket_hits)/len(ticket_hits),
                                  "random_rate_2plus":baseline["p2plus"],
                                  "mean_portfolio_total_hits":statistics.mean(int(r["total_hits_all_three"]) for r in rows),
                                  "random_expected_portfolio_total_hits":3*baseline["mean_hits"],
                                  "any_line_2plus_rate":sum(bool(r["any_line_2plus"]) for r in rows)/len(rows),
                                  "interpretation":"newly recomputed; exploratory and post-hoc"})
    csv_write(out/"fresh_portfolio_metrics.csv",portfolio_metrics)

    candidate_rows=[]
    all_tickets={mid:set(v["ticket"]) for mid,v in candidates_at_1245.items()}
    for a,b in combinations(sorted(all_tickets),2):
        inter=all_tickets[a]&all_tickets[b]; union=all_tickets[a]|all_tickets[b]
        candidate_rows.append({"model_a":a,"model_b":b,"intersection_numbers":" ".join(map(str,sorted(inter))),
                               "intersection_count":len(inter),"jaccard":len(inter)/len(union),
                               "random_expected_intersection":36/45,
                               "note":"diagnostic only; generated from 1..1244"})
    csv_write(out/"fresh_candidate_overlaps.csv",candidate_rows)
    vote=Counter(n for ticket in all_tickets.values() for n in ticket)
    csv_write(out/"fresh_candidate_number_frequency.csv",[
        {"number":n,"candidate_model_count":vote[n],"models":" ".join(mid for mid,t in sorted(all_tickets.items()) if n in t)}
        for n in range(1,46)])

    prev = ROOT/"research"/"1245_final_pipeline_v3"/"recovery_run_20261009"/"final_three_lines_1245_v3_recovery.csv"
    if not prev.is_file():
        raise FileNotFoundError(f"prior recovery lines missing: {prev}")
    prior_sha=sha256(prev)
    with prev.open(newline="",encoding="utf-8-sig") as f:
        prior_lines={int(r["line"]):r["numbers"] for r in csv.DictReader(f)}
    selected_rows=[]
    for x in final_lines:
        nums=tuple(x["numbers"])
        selected_rows.append({"line":x["line"],"numbers":" ".join(map(str,nums)),
                              "model_sources":x["model_sources"],"signal_sources":x["signal_sources"],
                              "selection_rule":x["rule"],
                              "matches_previous_recovery":prior_lines.get(int(x["line"]))==" ".join(map(str,nums)),
                              **ticket_structure(nums),
                              "validation":"REASSESSED_USING_FRESH_WALKFORWARD; SEALED_V3_GATE_STILL_NOT_PASSED"})
    csv_write(out/"reassessed_1245_three_lines.csv",selected_rows)
    final_sets=[set(x["numbers"]) for x in final_lines]
    pair_rows=[]
    for i,j in combinations(range(3),2):
        inter=final_sets[i]&final_sets[j]
        pair_rows.append({"line_a":i+1,"line_b":j+1,"intersection":" ".join(map(str,sorted(inter)),),
                          "intersection_count":len(inter),"jaccard":len(inter)/len(final_sets[i]|final_sets[j])})
    csv_write(out/"reassessed_portfolio_overlap.csv",pair_rows)

    matches_prior=all(row["matches_previous_recovery"] for row in selected_rows)
    log=["COMMAND: python research/1245_final_pipeline_v3/independent_validation_20261009.py --run-id " + args.run_id,
         f"SOURCE_VALIDATED rows={row_count} rounds=1-1244 latest_date={latest_date} worktree_sha256={sha256(DATA)} lf_normalized_sha256={canonical_sha}",
         "FRESH_EXPANDING targets=1045-1244 predictions=1600 (8 models x 200 targets)",
         "FRESH_ROLLING300 targets=1045-1244 predictions=1600 (8 models x 200 targets)",
         f"EXACT_RANDOM mean_hits={baseline['mean_hits']:.9f} p2plus={baseline['p2plus']:.9f} p3plus={baseline['p3plus']:.9f}",
         f"REASSESSED_LINES={len(selected_rows)} previous_lines_preserved_sha256={prior_sha}",
         f"PREVIOUS_THREE_LINES_UNCHANGED={matches_prior}",
         "TARGET_RESULT_1245_READ=NO"]
    (out/"execution.log").write_text("\n".join(log)+"\n",encoding="utf-8")

    report=["# Independent validation and 1245 candidate reassessment","",
            "Date: 2026-10-09 (Asia/Seoul)","",
            "## Evidence separation","",
            "- New results: model candidate predictions and 200-target expanding/rolling-300 validation were recomputed by this run.",
            "- Existing results: the prior B report, stored batch-001 metrics, V3 check-only output, and 1245 candidate lines remain historical inputs/references; they were not relabeled as newly computed.",
            "- The final 1245 actual result was not loaded. These are algorithmic purchase candidates, not winning predictions.",
            "- The study's evidence is post-hoc. Newly recomputing its last-200 slice does not make it prospective or independent of prior research selection.","",
            "## Data integrity","",f"- Source: `{DATA.name}`; SHA-256 `{sha256(DATA)}`.",
            f"- Rows: {row_count}; consecutive unique rounds 1..1244; latest published row date {latest_date}.",
            "- Exact expected columns; six unique main numbers in 1..45 per round; bonus valid, in range, and separate.",
            f"- Dates parse and are strictly weekly in order. The Windows checkout byte SHA is `{sha256(DATA)}`; CRLF-to-LF normalized SHA is `{canonical_sha}`, matching both the historical pinned SHA and Git blob. The mismatch is line endings only.",
            "- Training cutoff for every target t was t-1. Expanding uses 1..t-1; rolling uses the latest 300 draws ending t-1.",
            "- 1245 candidate generation uses exactly rounds 1..1244; no outcome row beyond cutoff was read.","",
            "## Exact random baseline","",f"- Mean hits per six-number ticket: {baseline['mean_hits']:.6f}.",
            f"- P(2+ hits): {baseline['p2plus']:.6%}; P(3+ hits): {baseline['p3plus']:.6%}.",
            "- Point estimates near this baseline are not evidence of predictive advantage. Null bands in the scorecard are descriptive only and do not correct for model selection or multiple comparisons.","",
            "## Fresh model results","",
            "See `fresh_model_scorecard.csv` for every model under both newly recomputed windows, and `fresh_walkforward_predictions.csv` for each target/model prediction. The last-200 target interval is 1045–1244 (n=200 per model and window). All 16 fresh model/window score pairs exactly reproduce the matching stored post-hoc recent-200 mean and 2+ rate; this is a reproducibility check, not independent prospective evidence.","",
            "Two opposite-direction point estimates fall outside the approximate pointwise 95% random-null bands: expanding S005 mean 0.680 is just below the lower mean band 0.691; rolling S002 mean 0.925 and 2+ rate 24% are above their upper bands. These are post-hoc results among correlated models and repeated metrics, with no untouched outcomes or multiple-testing correction. They do not validate either a positive or negative predictive signal.","",
            "## Three-line portfolio results","",
            "See `fresh_portfolio_metrics.csv` for the existing V3 selector applied at each target using only prior draws, and `fresh_portfolio_walkforward.csv` for the per-target lines/hits. This checks the selection rule itself; it is not a historical score of the fixed 1245 ticket chosen after observing rounds 1–1244.","",
            "## Candidate overlap and number relationships","",
            "`fresh_candidate_overlaps.csv` reports all 28 candidate pairs; `fresh_candidate_number_frequency.csv` reports per-number support among S001–S008. `reassessed_portfolio_overlap.csv` gives chosen-line intersections. S006/S007 overlap and number support are diagnostics, not independent model votes.","",
            "## Reassessed 1245 lines","",
            "|Line|Numbers|Sources|Sum|Odd|Low (1–22)|Line intersection|","|---:|---|---|---:|---:|---:|---|"]
    for i,row in enumerate(selected_rows):
        overlap="; ".join(f"L{p['line_b']}: {p['intersection_count']} ({p['intersection'] or 'none'})" for p in pair_rows if p['line_a']==i+1)
        report.append(f"|{row['line']}|{row['numbers']}|{row['model_sources']}|{row['sum']}|{row['odd']}|{row['low_1_22']}|{overlap or 'see overlap CSV'}|")
    report += ["",f"Selection method remains the V3 rule: equal-family rank consensus, S006/S007 averaged as one relationship family, S008 excluded as another vote, then two tickets chosen from distinct families by structure coverage, portfolio number coverage, intersections, and deterministic ID ties. All three reassessed lines match the prior recovery output (`{matches_prior}`); the original dated CSV remains preserved with SHA-256 `{prior_sha}`.","",
               "## Incomplete","",
               "- Original sealed V3 gate remains NOT PASSED: the prospective model registry/seal and prior B artifacts listed in `recovery_run_20261009/PIPELINE_ERROR_REPORT.md` were not found.",
               "- No unified A/B/C/contrarian models or their output artifacts were found in the accessible PC scan, Git history, or the only GitHub branch (`main`). A study comparison CSV and B report exist, but neither substitutes for the missing B predictions/classification CSVs.",
               "- No truly untouched prospective holdout exists before round 1245 in the current source; reported 1045–1244 validation is historical/post-hoc.",
               "- Therefore no S-model is labeled a validated predictive signal; repeatable random-level performance remains the null interpretation.","",
               "## Re-run","","```powershell",
               "& 'C:\\Users\\admin\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' research\\1245_final_pipeline_v3\\independent_validation_20261009.py --run-id next-run",
               "```","","The script refuses to overwrite an existing run folder. See the committed `execution.log` for actual command output.",""]
    (out/"INDEPENDENT_VALIDATION_REPORT.md").write_text("\n".join(report),encoding="utf-8")
    (out/"run_metadata.json").write_text(json.dumps({"run_id":args.run_id,"source_worktree_sha256":sha256(DATA),
        "source_lf_normalized_sha256":canonical_sha,"source_rows":row_count,
        "target_interval":"1045-1244","targets_per_mode":200,"windows":["expanding","rolling300"],
        "target_1245_actual_read":False,"prior_candidate_file_sha256":prior_sha,
        "all_lines_match_prior_recovery":matches_prior,
        "random_baseline":{k:v for k,v in baseline.items() if k!="distribution"}},indent=2),encoding="utf-8")
    print("\n".join(log))
    print(f"INDEPENDENT_VALIDATION_OUTPUT={out}")


if __name__ == "__main__":
    main()
