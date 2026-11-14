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
from datetime import date, datetime, timedelta, timezone, time as dt_time
from zoneinfo import ZoneInfo
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis/2026-10-12/lotto_data_1_1245_snapshot.csv"
TRACKER = ROOT / "analysis/prospective/E030"
CROSSCHECK_DIR = Path("research/prospective_v1/source_crosschecks")
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
    source_type = "DONGHAENG_LOTTERY_OFFICIAL_JSON_ENDPOINT"
    return {
        "round": round_no, "date": draw_date, "numbers": nums, "bonus": bonus,
        "source_type": source_type,
        "source_evidence": {"source_type": source_type, "url": API.format(round_no)},
    }


def fetch_repository_verified(round_no: int, root: Path) -> dict | None:
    """Use an append-only repository snapshot only with a pinned prefix hash and two matching secondary sources."""
    import csv

    crosscheck_path = root / CROSSCHECK_DIR / f"ROUND_{round_no}.json"
    if not crosscheck_path.is_file():
        return None
    evidence = json.loads(crosscheck_path.read_text(encoding="utf-8"))
    if int(evidence.get("target_round", -1)) != round_no:
        raise ValueError(f"crosscheck target mismatch for round {round_no}")

    expected_date = date.fromisoformat(evidence["draw_date"])
    expected_numbers = tuple(sorted(int(n) for n in evidence["main_numbers"]))
    expected_bonus = int(evidence["bonus"])
    if len(expected_numbers) != 6 or len(set(expected_numbers)) != 6 or min(expected_numbers) < 1 or max(expected_numbers) > 45:
        raise ValueError(f"invalid crosscheck main numbers for round {round_no}")
    if not 1 <= expected_bonus <= 45 or expected_bonus in expected_numbers:
        raise ValueError(f"invalid crosscheck bonus for round {round_no}")

    sources = evidence.get("fallback_sources", [])
    domains = {str(source.get("domain", "")).lower() for source in sources if source.get("domain")}
    if len(sources) < 2 or len(domains) < 2:
        raise ValueError(f"round {round_no} fallback requires two separately hosted sources")
    for source in sources:
        if (int(source["round"]) != round_no
                or date.fromisoformat(source["draw_date"]) != expected_date
                or tuple(sorted(int(n) for n in source["main_numbers"])) != expected_numbers
                or int(source["bonus"]) != expected_bonus):
            raise ValueError(f"secondary source disagreement for round {round_no}: {source.get('domain')}")

    data_path = root / "lotto_data.csv"
    raw = data_path.read_bytes().replace(b"\r\n", b"\n")
    prefix_parts = []
    found_target = False
    for line in raw.splitlines(keepends=True):
        prefix_parts.append(line)
        if not line.strip():
            continue
        first = line.split(b",", 1)[0].strip()
        if first.isdigit() and int(first) == round_no:
            found_target = True
            break
    if not found_target:
        raise ValueError(f"repository data does not contain round {round_no}")
    prefix_sha = hashlib.sha256(b"".join(prefix_parts)).hexdigest()
    expected_prefix_sha = evidence["repository_snapshot"]["prefix_through_target_sha256"]
    if prefix_sha != expected_prefix_sha:
        raise ValueError(f"repository data prefix SHA mismatch for round {round_no}")

    with data_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = [row for row in csv.DictReader(stream) if row and row.get("round")]
    rounds = [int(row["round"]) for row in rows]
    if not rounds or rounds != list(range(1, rounds[-1] + 1)):
        raise ValueError("repository snapshot round sequence is not contiguous")
    matching = [row for row in rows if int(row["round"]) == round_no]
    if len(matching) != 1:
        raise ValueError(f"repository snapshot has {len(matching)} rows for round {round_no}")
    row = matching[0]
    numbers = tuple(sorted(int(row[f"no{i}"]) for i in range(1, 7)))
    bonus = int(row["bonus"])
    draw_date = datetime.strptime(row["date"], "%Y.%m.%d").date()
    if (draw_date != expected_date or numbers != expected_numbers or bonus != expected_bonus
            or len(set(numbers)) != 6 or min(numbers) < 1 or max(numbers) > 45
            or not 1 <= bonus <= 45 or bonus in numbers):
        raise ValueError(f"repository row and crosscheck disagree for round {round_no}")

    source_type = "REPOSITORY_SNAPSHOT_CROSSCHECKED_BY_TWO_SECONDARY_SOURCES"
    source_evidence = {
        "source_type": source_type,
        "repository_data_path": "lotto_data.csv",
        "repository_data_cutoff": rounds[-1],
        "repository_data_sha256": hashlib.sha256(raw).hexdigest(),
        "repository_data_prefix_sha256_through_target": prefix_sha,
        "crosscheck_path": crosscheck_path.relative_to(root).as_posix(),
        "crosscheck_sha256": hashlib.sha256(crosscheck_path.read_bytes()).hexdigest(),
        "fallback_sources": sources,
        "official_api_attempt": "NO_SUCCESS_PAYLOAD; repository fallback used",
    }
    return {
        "round": round_no, "date": draw_date, "numbers": numbers, "bonus": bonus,
        "source_type": source_type, "source_evidence": source_evidence,
    }


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
        scored.append({"signal": signal["signal"], "model_version": signal.get("model_version", signal.get("formula_version", "unknown")),
            "prediction_numbers": signal["numbers"], "main_hits": hits,
            "bonus_included": actual["bonus"] in signal["numbers"],
            "official_main_numbers": sorted(actual["numbers"]), "official_bonus": actual["bonus"]})
    source_type = actual.get("source_type", "DONGHAENG_LOTTERY_OFFICIAL_JSON_ENDPOINT")
    source_evidence = actual.get("source_evidence") or {
        "source_type": source_type, "url": API.format(actual["round"])
    }
    official_url = source_evidence.get("url") if source_type == "DONGHAENG_LOTTERY_OFFICIAL_JSON_ENDPOINT" else None
    return {"status": "OUTCOME_RECORDED", "target_round": actual["round"],
        "official_draw_date": actual["date"].isoformat(),
        "prediction_file": prediction_path.relative_to(repository_root).as_posix() if repository_root else prediction_path.as_posix(),
        "prediction_sha256": digest(prediction_path), "official_source_url": official_url,
        "source_type": source_type, "source_evidence": source_evidence,
        "fetched_at_utc": fetched_at, "signals": scored, "purchase_recommendation": False}


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


def run(root: Path = ROOT, opener=urllib.request.urlopen, now: datetime | None = None) -> dict:
    root = root.resolve()
    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    tracker = root / "analysis/prospective/E030"
    draws = _extend_from_result_events(load_draws(), tracker)
    frozen_files = _read_frozen_files(root)
    if not frozen_files:
        raise FileNotFoundError("No immutable E030 frozen prediction found")
    frozen_files.sort(key=lambda p: int(json.loads(p.read_text(encoding="utf-8"))["target_round"]))
    frozen_path = frozen_files[-1]
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    target = int(frozen["target_round"])
    if int(frozen["training_through_round"]) != target - 1:
        raise ValueError(f"frozen prediction cutoff mismatch for target {target}")

    result_path = tracker / f"RESULT_{target}.json"
    actual = fetch_official(target, opener=opener)
    if actual is None:
        actual = fetch_repository_verified(target, root)
    if actual is None and result_path.is_file():
        prior = json.loads(result_path.read_text(encoding="utf-8"))
        first = prior["signals"][0]
        actual = {
            "round": target,
            "date": date.fromisoformat(prior["official_draw_date"]),
            "numbers": tuple(sorted(int(n) for n in first["official_main_numbers"])),
            "bonus": int(first["official_bonus"]),
            "source_type": prior.get("source_type", "RECORDED_RESULT_EVENT"),
            "source_evidence": prior.get("source_evidence", {}),
        }

    created_result = False
    if actual is not None and not result_path.exists():
        tracker.mkdir(parents=True, exist_ok=True)
        record = result_artifact(frozen, frozen_path, actual, now_utc.isoformat(), repository_root=root)
        with result_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        created_result = True
    elif actual is not None and result_path.exists():
        prior = json.loads(result_path.read_text(encoding="utf-8"))
        first = prior["signals"][0]
        prior_numbers = tuple(sorted(int(n) for n in first["official_main_numbers"]))
        if (prior_numbers != tuple(sorted(actual["numbers"]))
                or int(first["official_bonus"]) != int(actual["bonus"])
                or prior["official_draw_date"] != actual["date"].isoformat()):
            raise ValueError(f"recorded outcome conflicts with verified result for round {target}")
        # Preserve the first write-once source provenance and result bytes.
        actual = {
            "round": target, "date": date.fromisoformat(prior["official_draw_date"]),
            "numbers": prior_numbers, "bonus": int(first["official_bonus"]),
            "source_type": prior.get("source_type", "RECORDED_RESULT_EVENT"),
            "source_evidence": prior.get("source_evidence", {}),
        }

    generated_prediction = None
    next_prediction_status = "PENDING_OFFICIAL_DRAW"
    status_path = None
    if actual is not None:
        if target == len(draws) + 1:
            draws.append(actual)
        elif target <= len(draws):
            existing = draws[target - 1]
            if (existing["date"] != actual["date"] or existing["numbers"] != tuple(sorted(actual["numbers"]))
                    or existing["bonus"] != int(actual["bonus"])):
                raise ValueError(f"recorded event conflicts with canonical event at round {target}")
        else:
            raise ValueError(f"cannot extend contiguous prospective rounds: target {target}, next {len(draws)+1}")

        next_target = target + 1
        next_date = actual["date"] + timedelta(days=7)
        next_draw_at = datetime.combine(next_date, dt_time(20, 35), tzinfo=ZoneInfo("Asia/Seoul")).astimezone(timezone.utc)
        if now_utc < next_draw_at:
            next_frozen = make_frozen_prediction(draws, now_utc.isoformat())
            next_path = tracker / f"FROZEN_SIGNALS_{next_target}.json"
            if next_path.exists():
                prior_next = json.loads(next_path.read_text(encoding="utf-8"))
                if (int(prior_next["target_round"]) != next_target
                        or int(prior_next["training_through_round"]) != next_target - 1):
                    raise ValueError(f"existing immutable prediction cutoff mismatch for target {next_target}")
                generated_prediction = str(next_path.relative_to(root))
                next_prediction_status = "EXISTING_IMMUTABLE_PREDICTION_PRESERVED"
            else:
                tracker.mkdir(parents=True, exist_ok=True)
                with next_path.open("x", encoding="utf-8", newline="\n") as stream:
                    json.dump(next_frozen, stream, ensure_ascii=False, indent=2)
                    stream.write("\n")
                generated_prediction = str(next_path.relative_to(root))
                next_prediction_status = "FROZEN_BEFORE_TARGET_DRAW"
        else:
            next_prediction_status = "NEXT_TARGET_DRAW_ALREADY_PASSED_NO_RETROSPECTIVE_FREEZE"
            status_path = tracker / f"UPDATE_STATUS_{target}.json"
            source_cutoff = (actual.get("source_evidence") or {}).get("repository_data_cutoff")
            gap_targets = list(range(next_target, int(source_cutoff) + 1)) if source_cutoff and int(source_cutoff) >= next_target else []
            status_record = {
                "status": next_prediction_status,
                "target_round": target,
                "next_target_round": next_target,
                "next_target_draw_date": next_date.isoformat(),
                "next_target_draw_at_utc": next_draw_at.isoformat(),
                "next_prediction_created": False,
                "latest_verified_repository_cutoff": source_cutoff,
                "historical_targets_without_pre_draw_freeze": gap_targets,
                "prospective_horizon_status": "INCOMPLETE_GAP_AFTER_LAST_FROZEN_TARGET",
                "reason": "The next target draw had already occurred before a pre-draw forecast could be frozen. No retrospective prediction was generated.",
            }
            if status_path.exists():
                prior_status = json.loads(status_path.read_text(encoding="utf-8"))
                if prior_status != status_record:
                    raise ValueError(f"existing immutable update status differs: {status_path}")
            else:
                tracker.mkdir(parents=True, exist_ok=True)
                with status_path.open("x", encoding="utf-8", newline="\n") as stream:
                    json.dump(status_record, stream, ensure_ascii=False, indent=2)
                    stream.write("\n")

    status = "OUTCOME_RECORDED" if actual is not None else "PENDING_OFFICIAL_DRAW"
    return {
        "status": status,
        "target_round": target,
        "result_created": created_result,
        "result_path": str(result_path.relative_to(root)) if actual is not None else None,
        "next_prediction_created": generated_prediction is not None and next_prediction_status == "FROZEN_BEFORE_TARGET_DRAW",
        "next_prediction_path": generated_prediction,
        "next_prediction_status": next_prediction_status,
        "status_path": str(status_path.relative_to(root)) if status_path else None,
        "purchase_recommendation": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(run(args.root), ensure_ascii=False, indent=2))
