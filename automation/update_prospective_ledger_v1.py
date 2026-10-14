#!/usr/bin/env python3
"""Record official outcomes for immutable E030 shadow forecasts and freeze the next one.

No purchase recommendations are created. Existing forecast/result artifacts are never edited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis/2026-10-12/lotto_data_1_1245_snapshot.csv"
TRACKER = ROOT / "analysis/prospective/E030"
API = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"


def digest(path: Path) -> str:
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def load_draws() -> list[dict]:
    import csv
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 1245:
        raise ValueError(f"canonical snapshot row count {len(rows)} != 1245")
    draws = []
    for expected, row in enumerate(rows, 1):
        numbers = tuple(sorted(int(row[f"no{i}"]) for i in range(1, 7)))
        bonus = int(row["bonus"])
        draw_date = datetime.strptime(row["date"], "%Y.%m.%d").date()
        if int(row["round"]) != expected or len(set(numbers)) != 6 or min(numbers) < 1 or max(numbers) > 45:
            raise ValueError(f"invalid canonical draw row {expected}")
        if not 1 <= bonus <= 45 or bonus in numbers:
            raise ValueError(f"invalid bonus at round {expected}")
        draws.append({"round": expected, "date": draw_date, "numbers": numbers, "bonus": bonus})
    return draws


def fetch_official(round_no: int, opener=urllib.request.urlopen) -> dict | None:
    request = urllib.request.Request(API.format(round_no), headers={"User-Agent": "lotto-research-shadow/1.0"})
    try:
        with opener(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if payload.get("returnValue") != "success":
        return None
    returned_round = int(payload["drwNo"])
    if returned_round != round_no:
        raise ValueError(f"official API returned round {returned_round}, requested {round_no}")
    nums = tuple(sorted(int(payload[f"drwtNo{i}"]) for i in range(1, 7)))
    bonus = int(payload["bnusNo"])
    draw_date = datetime.strptime(payload["drwNoDate"], "%Y-%m-%d").date()
    if len(set(nums)) != 6 or min(nums) < 1 or max(nums) > 45 or not 1 <= bonus <= 45 or bonus in nums:
        raise ValueError(f"official API returned invalid numbers for round {round_no}")
    return {"round": round_no, "date": draw_date, "numbers": nums, "bonus": bonus}


def _season(month: int) -> int:
    return 0 if month in (12, 1, 2) else 1 if month in (3, 4, 5) else 2 if month in (6, 7, 8) else 3


def _sum_bin(total: int) -> int:
    return 0 if total < 120 else 1 if total < 145 else 2 if total < 170 else 3


def make_frozen_prediction(draws: list[dict], generated_at: str) -> dict:
    """Exact E025 seasonal/sum-regime formulas, no tuning and train cutoff = target-1."""
    target = len(draws) + 1
    target_date = draws[-1]["date"] + timedelta(days=7)
    global_counts = np.zeros(45); seasonal_counts = np.zeros(45); regime_counts = np.zeros(45)
    season_n = 0; regime_n = 0
    for i, d in enumerate(draws):
        for n in d["numbers"]: global_counts[n - 1] += 1
        if _season(d["date"].month) == _season(target_date.month):
            season_n += 1
            for n in d["numbers"]: seasonal_counts[n - 1] += 1
        if i > 0 and _sum_bin(sum(draws[i - 1]["numbers"])) == _sum_bin(sum(draws[-1]["numbers"])):
            regime_n += 1
            for n in d["numbers"]: regime_counts[n - 1] += 1
    global_rate = global_counts / len(draws)
    season_score = (seasonal_counts + 30.0 * global_rate) / (season_n + 30.0)
    regime_score = (regime_counts + 20.0 * global_rate) / (regime_n + 20.0)
    def make(signal: str, scores: np.ndarray) -> dict:
        order = (np.argsort(-scores, kind="stable") + 1).tolist()
        return {"signal": signal, "model_version": "E025_FROZEN_v1",
                "numbers": sorted(order[:6]), "score_order": order}
    return {"status": "FROZEN_PROSPECTIVE_SHADOW_ONLY", "target_round": target,
        "training_through_round": target - 1, "target_draw_date_assumption": target_date.isoformat(),
        "canonical_snapshot_sha256": digest(DATA), "generated_at_utc": generated_at,
        "signals": [make("CALENDAR_SEASON_CONDITIONAL_v1", season_score),
                    make("PREVIOUS_SUM_REGIME_CONDITIONAL_v1", regime_score)],
        "formula_source": "automation/independent_signal_five_line_v1.py E025 frozen formulas",
        "purchase_recommendation": False,
        "editing_policy": "immutable; corrections require a new artifact and documented reason"}


def result_artifact(frozen: dict, prediction_path: Path, actual: dict, fetched_at: str,
                    repository_root: Path | None = None) -> dict:
    outcome = set(actual["numbers"])
    scored = []
    for signal in frozen["signals"]:
        hits = len(set(signal["numbers"]) & outcome)
        scored.append({"signal": signal["signal"], "model_version": signal["model_version"],
            "prediction_numbers": signal["numbers"], "main_hits": hits,
            "bonus_included": actual["bonus"] in signal["numbers"],
            "official_main_numbers": sorted(actual["numbers"]), "official_bonus": actual["bonus"]})
    return {"status": "OFFICIAL_OUTCOME_RECORDED", "target_round": actual["round"],
        "official_draw_date": actual["date"].isoformat(),
        "prediction_file": prediction_path.relative_to(repository_root).as_posix() if repository_root else prediction_path.as_posix(),
        "prediction_sha256": digest(prediction_path), "official_source_url": API.format(actual["round"]),
        "source_type": "DONGHAENG_LOTTERY_OFFICIAL_JSON_ENDPOINT", "fetched_at_utc": fetched_at,
        "signals": scored, "purchase_recommendation": False}


def _read_frozen_files(root: Path) -> list[Path]:
    return sorted(p for p in (root / "analysis").rglob("FROZEN_SIGNALS_*.json")
                  if ".attempts" not in p.parts and p.parent.name.startswith("E030"))


def _extend_from_result_events(draws: list[dict], tracker: Path) -> list[dict]:
    """Load only contiguous, previously recorded official result events."""
    result_files = sorted(tracker.glob("RESULT_*.json"), key=lambda p: int(p.stem.split("_")[-1]))
    for path in result_files:
        record = json.loads(path.read_text(encoding="utf-8"))
        round_no = int(record["target_round"])
        if round_no <= len(draws):
            continue
        if round_no != len(draws) + 1:
            raise ValueError(f"non-contiguous prospective result sequence at {path.name}")
        first = record["signals"][0]
        numbers = tuple(sorted(int(n) for n in first["official_main_numbers"]))
        bonus = int(first["official_bonus"])
        if len(numbers) != 6 or len(set(numbers)) != 6 or min(numbers) < 1 or max(numbers) > 45 or bonus not in range(1, 46) or bonus in numbers:
            raise ValueError(f"invalid recorded official outcome in {path}")
        draws.append({"round": round_no, "date": datetime.strptime(record["official_draw_date"], "%Y-%m-%d").date(),
                      "numbers": numbers, "bonus": bonus})
    return draws


def run(root: Path = ROOT, opener=urllib.request.urlopen) -> dict:
    root = root.resolve(); draws = _extend_from_result_events(load_draws(), TRACKER)
    frozen_files = _read_frozen_files(root)
    if not frozen_files:
        raise FileNotFoundError("No immutable E030 frozen prediction found")
    frozen_files.sort(key=lambda p: int(json.loads(p.read_text(encoding="utf-8"))["target_round"]))
    # A prospective result event is created only once. Existing prediction bytes remain untouched.
    frozen = json.loads(frozen_files[-1].read_text(encoding="utf-8"))
    target = int(frozen["target_round"])
    if int(frozen["training_through_round"]) != target - 1:
        raise ValueError(f"frozen prediction cutoff mismatch for target {target}")
    actual = fetch_official(target, opener=opener)
    result_path = TRACKER / f"RESULT_{target}.json"
    created_result = False
    if actual is not None and not result_path.exists():
        TRACKER.mkdir(parents=True, exist_ok=True)
        record = result_artifact(frozen, frozen_files[-1], actual,
                                 datetime.now(timezone.utc).isoformat(), repository_root=root)
        with result_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2); stream.write("\n")
        created_result = True
    elif actual is not None and result_path.exists():
        prior = json.loads(result_path.read_text(encoding="utf-8"))
        prior_nums = tuple(prior["signals"][0]["official_main_numbers"])
        if prior_nums != tuple(sorted(actual["numbers"])) or prior["signals"][0]["official_bonus"] != actual["bonus"]:
            raise ValueError(f"official result revision detected for {target}; preserving prior and requiring review")
    generated_prediction = None
    if actual is not None:
        # The snapshot is read-only; official outcomes are held in memory for subsequent cutoffs.
        if target != len(draws) + 1:
            raise ValueError(f"cannot extend contiguous canonical rounds: target {target}, next {len(draws)+1}")
        draws.append(actual)
        next_frozen = make_frozen_prediction(draws, datetime.now(timezone.utc).isoformat())
        TRACKER.mkdir(parents=True, exist_ok=True)
        next_path = TRACKER / f"FROZEN_SIGNALS_{next_frozen['target_round']}.json"
        if not next_path.exists():
            with next_path.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(next_frozen, stream, ensure_ascii=False, indent=2); stream.write("\n")
        generated_prediction = str(next_path.relative_to(root))
    return {"status": "UPDATED" if actual else "PENDING_OFFICIAL_DRAW",
            "target_round": target, "result_created": created_result,
            "next_prediction_created": generated_prediction is not None,
            "result_path": str(result_path.relative_to(root)) if created_result else None,
            "next_prediction_path": generated_prediction,
            "purchase_recommendation": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(run(args.root), ensure_ascii=False, indent=2))
