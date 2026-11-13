#!/usr/bin/env python3
"""E046: design-only prospective sample-size planning for the fixed 3-line gate."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research/weekly_purchase/1251/THREE_LINE_PROSPECTIVE_POWER_PREREG_E046_20261114.json"
E045_REL = "analysis/2026-11-14/gha_43499702588_1/E045_THREE_LINE_DISJOINT_PORTFOLIO_WALKFORWARD_v1"
METRICS = ("max_hits", "any2", "any3", "winning_union_coverage")
EFFECT_SIZES = (0.25, 0.5, 0.75, 1.0)
TARGET_COUNTS = (100, 125, 150, 175, 200, 250, 300, 400, 500, 600, 800, 1000)
BLOCK_SIZE = 50
ALPHA_PER_METRIC = 0.0125
BLOCK_SHARE_MIN = 0.65
NORMAL = NormalDist()


def block_lengths(n: int, block_size: int = BLOCK_SIZE) -> list[int]:
    if n <= 0:
        raise ValueError("target count must be positive")
    full, remainder = divmod(n, block_size)
    lengths = [block_size] * full
    if remainder:
        lengths.append(remainder)
    return lengths


def effective_block_count(lengths: list[int]) -> float:
    total = sum(lengths)
    if total <= 0:
        raise ValueError("empty block design")
    return 1.0 / sum((length / total) ** 2 for length in lengths)


def binomial_tail(n: int, p: float, minimum_successes: int) -> float:
    if n <= 0 or not 0 <= p <= 1:
        raise ValueError("invalid binomial parameters")
    return sum(math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
               for k in range(minimum_successes, n + 1))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_e045_source(root: Path):
    folder = root / E045_REL
    manifest_path = folder / "SHA256_MANIFEST.csv"
    verification_path = folder / "VERIFICATION.json"
    prediction_path = folder / "PREDICTIONS.csv"
    random_path = folder / "RANDOM_BASELINE.csv"
    required = (manifest_path, verification_path, prediction_path, random_path)
    if not all(path.is_file() for path in required):
        raise FileNotFoundError("E045 frozen source evidence is incomplete")
    manifest = list(csv.DictReader(manifest_path.open(encoding="utf-8-sig", newline="")))
    if len(manifest) != 8 or len({row["path"] for row in manifest}) != 8:
        raise ValueError("E045 manifest count/uniqueness mismatch")
    expected = {p.name for p in folder.iterdir() if p.is_file() and p.name != manifest_path.name}
    if {row["path"] for row in manifest} != expected:
        raise ValueError("E045 manifest coverage mismatch")
    for row in manifest:
        path = folder / row["path"]
        raw = path.read_bytes()
        if len(raw) != int(row["bytes"]) or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"E045 source artifact hash mismatch: {path.name}")
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    if verification.get("status") != "PASS" or verification.get("data_cutoff") != 1249:
        raise ValueError("E045 verification status/cutoff mismatch")
    if verification.get("no_future_leakage") is not True or verification.get("leakage_failures") != 0:
        raise ValueError("E045 leakage evidence is not clean")
    if verification.get("historical_strict_gate_pass") is not False or verification.get("strict_pass_ready") is not False:
        raise ValueError("E045 historical strict-fail state changed")
    runner_path = root / "automation/three_line_research_1251_v1.py"
    spec = importlib.util.spec_from_file_location("e045_runner_for_e046", runner_path)
    if spec is None or spec.loader is None:
        raise ValueError("E045 frozen runner cannot be loaded")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    _, prefix_sha, _, _ = runner.load_frozen_draw_prefix(
        int(verification["data_cutoff"]),
        verification["data_prefix_sha256"],
        verification["data_sha256"],
    )
    return folder, verification, prefix_sha, len(manifest)


def load_paired_differences(folder: Path):
    predictions = list(csv.DictReader((folder / "PREDICTIONS.csv").open(encoding="utf-8-sig", newline="")))
    random_rows = list(csv.DictReader((folder / "RANDOM_BASELINE.csv").open(encoding="utf-8-sig", newline="")))
    if len(predictions) != 849 or len(random_rows) != 849:
        raise ValueError("E045 prediction/random target count mismatch")
    differences = {metric: [] for metric in METRICS}
    block_records = []
    for pred, rand in zip(predictions, random_rows):
        target = int(pred["target_round"])
        if target != int(rand["target_round"]) or int(pred["training_through_round"]) != target - 1:
            raise ValueError(f"E045 target/cutoff join mismatch at {target}")
        if int(rand["random_bundles"]) != 120 or int(rand["geometry_violations"]) != 0:
            raise ValueError(f"E045 random comparator integrity failure at {target}")
        pairs = {
            "max_hits": (float(pred["max_hits"]), float(rand["exact_null_mean_max_hit"])),
            "any2": (float(pred["any2"]), float(rand["exact_null_p_any2"])),
            "any3": (float(pred["any3"]), float(rand["exact_null_p_any3"])),
            "winning_union_coverage": (float(pred["winning_union_coverage"]), float(rand["exact_null_expected_union_coverage"])),
        }
        row = {"target_round": target}
        for metric, (observed, null_value) in pairs.items():
            delta = observed - null_value
            differences[metric].append(delta)
            row[metric] = delta
        block_records.append(row)
    if [int(row["target_round"]) for row in block_records] != list(range(401, 1250)):
        raise ValueError("E045 target sequence is not 401..1249")
    return differences, block_records


def block_summaries(block_records):
    output = []
    metrics = {metric: [] for metric in METRICS}
    for start in range(0, len(block_records), BLOCK_SIZE):
        chunk = block_records[start:start + BLOCK_SIZE]
        for metric in METRICS:
            values = [float(row[metric]) for row in chunk]
            mean = statistics.mean(values)
            metrics[metric].append(mean)
            output.append({
                "metric": metric,
                "block_index": start // BLOCK_SIZE + 1,
                "target_start": chunk[0]["target_round"],
                "target_end": chunk[-1]["target_round"],
                "block_length": len(chunk),
                "mean_paired_difference": mean,
            })
    return metrics, output


def design_grid(block_sd: dict[str, float]):
    zcrit = NORMAL.inv_cdf(1 - ALPHA_PER_METRIC / 2)
    rows = []
    for n in TARGET_COUNTS:
        lengths = block_lengths(n)
        m_eff = effective_block_count(lengths)
        block_count = len(lengths)
        required_positive = math.ceil(BLOCK_SHARE_MIN * block_count)
        remainder = lengths[-1] if lengths[-1] < BLOCK_SIZE else 0
        for d in EFFECT_SIZES:
            metric_powers = {}
            for metric in METRICS:
                noncentrality = d * math.sqrt(m_eff)
                metric_powers[metric] = NORMAL.cdf(noncentrality - zcrit)
            p_positive_block = NORMAL.cdf(d)
            block_power = binomial_tail(block_count, p_positive_block, required_positive)
            independence_joint = math.prod(metric_powers.values()) * block_power
            conservative_joint = max(
                0.0,
                1.0 - sum(1.0 - value for value in metric_powers.values()) - (1.0 - block_power),
            )
            rows.append({
                "prospective_target_count": n,
                "block_size": BLOCK_SIZE,
                "block_count_including_remainder": block_count,
                "final_remainder_length": remainder,
                "effective_block_count": m_eff,
                "standardized_effect_size_d": d,
                "max_hits_ci_power_approx": metric_powers["max_hits"],
                "any2_ci_power_approx": metric_powers["any2"],
                "any3_ci_power_approx": metric_powers["any3"],
                "winning_union_coverage_ci_power_approx": metric_powers["winning_union_coverage"],
                "any2_positive_block_probability": p_positive_block,
                "any2_block_share_gate_probability": block_power,
                "joint_power_independence_approx": independence_joint,
                "joint_power_conservative_union_lower": conservative_joint,
                "ci_z_critical": zcrit,
                "max_hits_block_sd_historical": block_sd["max_hits"],
                "any2_block_sd_historical": block_sd["any2"],
                "any3_block_sd_historical": block_sd["any3"],
                "coverage_block_sd_historical": block_sd["winning_union_coverage"],
            })
    return rows


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        raise ValueError(f"no rows to write: {path}")
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(date_kst: str, run_id: str):
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    if prereg.get("study_id") != "E046_THREE_LINE_PROSPECTIVE_POWER_PLANNING_v1":
        raise ValueError("E046 preregistration ID mismatch")
    folder, source_verification, prefix_sha, manifest_entries = verify_e045_source(ROOT)
    differences, block_records = load_paired_differences(folder)
    block_means, block_rows = block_summaries(block_records)
    block_sd = {metric: statistics.stdev(block_means[metric]) for metric in METRICS}
    if any(value <= 0 for value in block_sd.values()):
        raise ValueError("a historical block-level standard deviation is not positive")
    design_rows = design_grid(block_sd)

    outdir = ROOT / "analysis" / date_kst / run_id / prereg["study_id"]
    outdir.mkdir(parents=True, exist_ok=False)
    write_csv(outdir / "BLOCK_SUMMARIES.csv", block_rows)
    write_csv(outdir / "DESIGN_GRID.csv", design_rows)

    minimums = {}
    for d in EFFECT_SIZES:
        subset = [row for row in design_rows if row["standardized_effect_size_d"] == d]
        independence = next((row["prospective_target_count"] for row in subset if row["joint_power_independence_approx"] >= 0.80), None)
        conservative = next((row["prospective_target_count"] for row in subset if row["joint_power_conservative_union_lower"] >= 0.80), None)
        minimums[str(d)] = {
            "first_target_count_independence_approx_at_least_80pct": independence,
            "first_target_count_conservative_union_lower_at_least_80pct": conservative,
        }

    observed_means = {metric: statistics.mean(differences[metric]) for metric in METRICS}
    verification = {
        "study_id": prereg["study_id"],
        "status": "PASS",
        "study_classification": "DESIGN_ONLY_NOT_MODEL_EVIDENCE",
        "source_study_id": source_verification["study_id"],
        "source_data_cutoff": int(source_verification["data_cutoff"]),
        "source_data_sha256": source_verification["data_sha256"],
        "source_prefix_sha256_rechecked": prefix_sha,
        "source_manifest_entries_verified": manifest_entries,
        "source_targets": len(block_records),
        "target_range": [401, 1249],
        "random_bundles_per_target": 120,
        "random_geometry_violations": 0,
        "training_cutoff_violations": 0,
        "future_predictions": 0,
        "no_future_leakage": True,
        "historical_paired_difference_means_diagnostic_only": observed_means,
        "historical_block_standard_deviations": block_sd,
        "effect_size_grid": list(EFFECT_SIZES),
        "prospective_target_count_grid": list(TARGET_COUNTS),
        "block_size": BLOCK_SIZE,
        "final_remainder_retained": True,
        "alpha_per_metric": ALPHA_PER_METRIC,
        "strict_gate_thresholds_changed": False,
        "model_or_number_search_performed": False,
        "purchase_lines_generated": False,
        "strict_portfolio_pass": False,
        "strict_pass_ready": False,
        "minimum_counts_for_80pct_approximate_power": minimums,
        "limitations": [
            "This is a normal-theory planning approximation using historical block-level variance, not the operational moving-block bootstrap.",
            "Effect sizes are hypothetical standardized shifts, not observed predictive advantages.",
            "The independence product is only a reference approximation; metric dependence is not assumed away in the conservative union-bound lower estimate.",
            "No prospective minimum count or completion rule is adopted by this study."
        ]
    }
    (outdir / "VERIFICATION.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = [
        "# E046 — Three-line prospective confirmation design planning",
        "",
        "**Classification: DESIGN ONLY — NOT MODEL EVIDENCE, NOT STRICT PASS.**",
        "",
        f"- Frozen source: E045, cutoff {source_verification['data_cutoff']}, targets 401–1249 ({len(block_records)} targets)",
        f"- E045 manifest entries independently verified: {manifest_entries}/8",
        f"- Historical source prefix SHA256 rechecked: {prefix_sha}",
        "- No future outcomes, model tuning, ticket generation, or threshold changes.",
        "",
        "## Historical block-level variance used for planning",
        "",
        "| Metric | Historical paired-difference mean (diagnostic only) | SD of 50-target block means |",
        "|---|---:|---:|"
    ]
    for metric in METRICS:
        report.append(f"| {metric} | {observed_means[metric]:.6f} | {block_sd[metric]:.6f} |")
    report += [
        "",
        "## Prospective design grid",
        "",
        "The grid applies hypothetical positive shifts of 0.25, 0.5, 0.75, and 1.0 historical block SD. It uses the frozen 0.0125 per-metric alpha, a normal-theory lower-CI approximation, 50-target blocks, and retains a final remainder block.",
        "",
        "| Targets | Blocks (incl. remainder) | Effect d | Any2 block-share gate probability | Joint power (independence approx.) | Conservative joint lower bound |",
        "|---:|---:|---:|---:|---:|---:|"
    ]
    for row in design_rows:
        report.append(
            f"| {row['prospective_target_count']} | {row['block_count_including_remainder']} "
            f"({row['final_remainder_length'] or 50}) | {row['standardized_effect_size_d']:.2f} "
            f"| {row['any2_block_share_gate_probability']:.4f} "
            f"| {row['joint_power_independence_approx']:.4f} "
            f"| {row['joint_power_conservative_union_lower']:.4f} |"
        )
    report += [
        "",
        "## First grid point reaching 80%",
        "",
        "| Standardized effect d | Independence approximation | Conservative union-bound lower estimate |",
        "|---:|---:|---:|"
    ]
    for d in EFFECT_SIZES:
        m = minimums[str(d)]
        report.append(
            f"| {d:.2f} | {m['first_target_count_independence_approx_at_least_80pct'] or 'Not reached in grid'} "
            f"| {m['first_target_count_conservative_union_lower_at_least_80pct'] or 'Not reached in grid'} |"
        )
    report += [
        "",
        "## Interpretation and limits",
        "",
        "This analysis quantifies how demanding the fixed prospective confirmation gate may be under hypothetical standardized effects. It does not identify a model, prove a predictive edge, satisfy prospective confirmation, create STRICT_PASS_READY, or alter the policy. The operational gate still requires the actual preregistered moving-block bootstrap and all four lower bounds strictly above zero plus the 0.65 block-stability threshold.",
        "",
        "The prospective minimum target count and completion rule remain unspecified in the governing policy. This report is evidence for a later protocol decision only; it does not adopt a new rule.",
        ""
    ]
    (outdir / "REPORT.md").write_text("\n".join(report), encoding="utf-8")

    completion = {
        "study_id": prereg["study_id"],
        "status": "COMPLETE",
        "study_classification": "DESIGN_ONLY_NOT_MODEL_EVIDENCE",
        "data_cutoff": int(source_verification["data_cutoff"]),
        "target_count": len(block_records),
        "no_future_leakage": True,
        "strict_portfolio_pass": False,
        "strict_pass_ready": False,
        "purchase_lines_generated": False,
        "outputs": ["REPORT.md", "DESIGN_GRID.csv", "BLOCK_SUMMARIES.csv", "VERIFICATION.json"]
    }
    (outdir / "COMPLETION.json").write_text(json.dumps(completion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    files = sorted((path for path in outdir.iterdir() if path.is_file() and path.name != "SHA256_MANIFEST.csv"), key=lambda path: path.name)
    manifest = [{"path": path.name, "sha256": sha256(path), "bytes": path.stat().st_size} for path in files]
    write_csv(outdir / "SHA256_MANIFEST.csv", manifest)
    checked = list(csv.DictReader((outdir / "SHA256_MANIFEST.csv").open(encoding="utf-8-sig", newline="")))
    if {row["path"] for row in checked} != {path.name for path in files}:
        raise ValueError("E046 manifest coverage mismatch")
    for row in checked:
        path = outdir / row["path"]
        if path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
            raise ValueError(f"E046 output manifest mismatch: {path.name}")
    return {
        "status": "COMPLETE",
        "study_id": prereg["study_id"],
        "data_cutoff": int(source_verification["data_cutoff"]),
        "target_count": len(block_records),
        "design_rows": len(design_rows),
        "manifest_entries": len(checked),
        "strict_portfolio_pass": False,
        "strict_pass_ready": False,
        "output_dir": str(outdir.relative_to(ROOT)),
        "verification_sha256": sha256(outdir / "VERIFICATION.json"),
        "manifest_sha256": sha256(outdir / "SHA256_MANIFEST.csv")
    }


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: three_line_prospective_power_planning_v1.py DATE_KST RUN_ID")
    result = run(sys.argv[1], sys.argv[2])
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
