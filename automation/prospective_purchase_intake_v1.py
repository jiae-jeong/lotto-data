#!/usr/bin/env python3
"""Validate and seal user-supplied real purchase lines before a draw."""
from __future__ import annotations

import csv
import hashlib
import json
import urllib.error
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

API = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
LEDGER_DIR = Path("analysis/prospective_v1/purchases")
INTAKE_DIR = LEDGER_DIR / "intake"


class IntakeRejected(ValueError):
    """The intake is invalid, late, changed, or cannot be proven pre-outcome."""


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def _read_rounds(path: Path) -> tuple[int, date]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        last = int(rows[-1]["round"])
        draw_date = datetime.strptime(rows[-1]["date"], "%Y.%m.%d").date()
        if [int(row["round"]) for row in rows] != list(range(1, last + 1)):
            raise IntakeRejected("canonical round sequence is not contiguous")
        return last, draw_date
    except (OSError, ValueError, KeyError, IndexError) as error:
        if isinstance(error, IntakeRejected):
            raise
        raise IntakeRejected(f"cannot verify canonical cutoff: {error}") from error


def _official_status(target: int, opener=urllib.request.urlopen) -> str:
    request = urllib.request.Request(API.format(target), headers={"User-Agent": "lotto-purchase-intake/1.0"})
    try:
        with opener(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError, OSError) as error:
        raise IntakeRejected("official source could not confirm that the target outcome is unpublished") from error
    if not isinstance(payload, dict):
        raise IntakeRejected("official source returned an unexpected response")
    if payload.get("returnValue") == "success":
        if int(payload.get("drwNo", -1)) == target:
            return "PUBLISHED"
        raise IntakeRejected("official source returned success for an unexpected round")
    if payload.get("returnValue") == "fail":
        return "UNPUBLISHED"
    raise IntakeRejected("official source did not provide an explicit unpublished status")


def _parse_timestamp(value, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as error:
        raise IntakeRejected(f"{label} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise IntakeRejected(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def validate_intake(payload: dict, target_round: int, now: datetime,
                    draw_at: datetime) -> tuple[list[list[int]], list[dict], datetime, datetime]:
    if not isinstance(payload, dict) or type(payload.get("target_round")) is not int or payload["target_round"] != target_round:
        raise IntakeRejected("target_round does not match the next prospective target")
    if payload.get("purchase") is not True:
        raise IntakeRejected("purchase must be true for the real-purchase ledger")
    global_cutoff = payload.get("training_through_round")
    if type(global_cutoff) is not int or global_cutoff < 0 or global_cutoff > target_round - 1:
        raise IntakeRejected("training_through_round must be an integer <= target_round - 1")
    if not (isinstance(payload.get("rationale"), str) and payload["rationale"].strip()) and not (
            isinstance(payload.get("source_reference"), str) and payload["source_reference"].strip()):
        raise IntakeRejected("rationale or source_reference is required")
    generated = _parse_timestamp(payload.get("generated_at"), "generated_at")
    submitted = _parse_timestamp(payload.get("submitted_at"), "submitted_at")
    if generated > submitted:
        raise IntakeRejected("generated_at must not be later than submitted_at")
    if submitted > now.astimezone(timezone.utc):
        raise IntakeRejected("submitted_at cannot be in the future")
    if now.astimezone(timezone.utc) >= draw_at.astimezone(timezone.utc) or submitted >= draw_at.astimezone(timezone.utc):
        raise IntakeRejected("purchase intake must be submitted before the registered draw time")
    raw_lines = payload.get("lines")
    if not isinstance(raw_lines, list) or len(raw_lines) != 5:
        raise IntakeRejected("exactly five line records are required")
    lines: list[list[int]] = []
    provenance: list[dict] = []
    for index, item in enumerate(raw_lines, 1):
        if not isinstance(item, dict):
            raise IntakeRejected(f"line {index} must be an object with provenance")
        raw_numbers = item.get("numbers")
        if not isinstance(raw_numbers, list) or len(raw_numbers) != 6 or any(type(x) is not int for x in raw_numbers):
            raise IntakeRejected(f"line {index} must contain six integer numbers")
        numbers = sorted(raw_numbers)
        if len(set(numbers)) != 6 or numbers[0] < 1 or numbers[-1] > 45:
            raise IntakeRejected(f"line {index} must contain six distinct numbers in 1..45")
        model = item.get("source_model", item.get("source"))
        version = item.get("model_version", item.get("version"))
        if not isinstance(model, str) or not model.strip() or not isinstance(version, str) or not version.strip():
            raise IntakeRejected(f"line {index} requires source_model and model_version")
        cutoff = item.get("training_through_round", payload.get("training_through_round"))
        if type(cutoff) is not int or cutoff < 0 or cutoff > target_round - 1:
            raise IntakeRejected(f"line {index} training_through_round must be <= target_round - 1")
        line_generated = _parse_timestamp(item.get("generated_at", payload["generated_at"]), f"line {index} generated_at")
        line_submitted = _parse_timestamp(item.get("submitted_at", payload["submitted_at"]), f"line {index} submitted_at")
        if line_generated > line_submitted or line_submitted > now.astimezone(timezone.utc) or line_submitted >= draw_at.astimezone(timezone.utc):
            raise IntakeRejected(f"line {index} timestamps are not pre-draw and ordered")
        rationale = item.get("rationale", payload.get("rationale"))
        source_reference = item.get("source_reference", payload.get("source_reference"))
        if not (isinstance(rationale, str) and rationale.strip()) and not (isinstance(source_reference, str) and source_reference.strip()):
            raise IntakeRejected(f"line {index} requires rationale or source_reference")
        lines.append(numbers)
        provenance.append({"source_model": model.strip(), "model_version": version.strip(),
            "training_through_round": cutoff, "generated_at": line_generated.isoformat(),
            "submitted_at": line_submitted.isoformat(), "rationale": rationale,
            "source_reference": source_reference})
    if len({tuple(line) for line in lines}) != 5:
        raise IntakeRejected("duplicate lines are not allowed")
    return lines, provenance, generated, submitted


def seal_intake(root: Path, target_round: int, opener=urllib.request.urlopen,
                now: datetime | None = None) -> dict:
    """Seal a user intake once, rejecting any late or post-seal source edits."""
    root = root.resolve()
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    intake_path = root / INTAKE_DIR / f"ROUND_{target_round}.json"
    ledger_path = root / LEDGER_DIR / f"ROUND_{target_round}.json"
    if not intake_path.is_file():
        if ledger_path.is_file():
            raise IntakeRejected("sealed ledger exists but its original intake file is missing")
        return {"status": "NO_INTAKE", "target_round": target_round}
    intake_bytes = intake_path.read_bytes()
    intake_sha = sha_bytes(intake_bytes)
    if ledger_path.is_file():
        sealed = json.loads(ledger_path.read_text(encoding="utf-8"))
        if sealed.get("intake_sha256") != intake_sha:
            raise IntakeRejected("intake changed after immutable purchase ledger was sealed")
        return {"status": "ALREADY_SEALED", "target_round": target_round,
                "ledger_path": ledger_path.relative_to(root).as_posix(),
                "bundle_sha256": sealed["bundle_sha256"]}
    canonical = root / "lotto_data.csv"
    last_round, last_date = _read_rounds(canonical)
    if target_round != last_round + 1:
        raise IntakeRejected("intake target is not the next round after canonical data")
    event = root / "analysis/prospective_v1/outcomes" / f"ROUND_{target_round}.json"
    shadow_event = root / "analysis/prospective_v1/outcomes" / f"E046_SHADOW_OUTCOME_{target_round}.json"
    random5_event = root / "analysis/prospective_v1/outcomes" / f"E045_RANDOM5_OUTCOME_{target_round}.json"
    if event.exists() or shadow_event.exists() or random5_event.exists():
        raise IntakeRejected("target outcome is already recorded")
    target_day = last_date + timedelta(days=7)
    draw_at = datetime.combine(target_day, time(20, 45), tzinfo=timezone(timedelta(hours=9)))
    if now >= draw_at.astimezone(timezone.utc):
        raise IntakeRejected("registered draw time has passed")
    if _official_status(target_round, opener) != "UNPUBLISHED":
        raise IntakeRejected("target outcome is already officially published")
    try:
        payload = json.loads(intake_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IntakeRejected(f"intake is not valid UTF-8 JSON: {error}") from error
    lines, provenance, generated, submitted = validate_intake(payload, target_round, now, draw_at)
    line_hashes = [sha_bytes(json.dumps(line, separators=(",", ":")).encode("ascii")) for line in lines]
    for index, record in enumerate(provenance):
        record["line_sha256"] = line_hashes[index]
    bundle = {"study_id": "E044_REAL_PURCHASE_FIVE_LINE_LEDGER_v1", "target_round": target_round,
        "purchase_timestamp_utc": submitted.isoformat(), "generated_at": generated.isoformat(),
        "submitted_at": submitted.isoformat(), "training_through_round": payload.get("training_through_round"),
        "lines": lines, "line_provenance": provenance, "line_sha256": line_hashes,
        "intake_path": intake_path.relative_to(root).as_posix(), "intake_sha256": intake_sha,
        "canonical_cutoff_round": last_round, "canonical_data_sha256": sha_file(canonical),
        "bundle_sha256": "computed_over_bundle_without_this_field", "purchase": True,
        "sealed_before_draw": True, "draw_at_utc": draw_at.astimezone(timezone.utc).isoformat(),
        "source_evidence": [{"source_type": "USER_PURCHASE_INTAKE", "path": intake_path.relative_to(root).as_posix(), "sha256": intake_sha},
                            {"source_type": "OFFICIAL_UNPUBLISHED_CHECK", "url": API.format(target_round), "checked_at_utc": now.isoformat()}]}
    canonical_bundle = dict(bundle)
    canonical_bundle.pop("bundle_sha256")
    bundle["bundle_sha256"] = sha_bytes(json.dumps(canonical_bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(bundle, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return {"status": "SEALED", "target_round": target_round,
            "ledger_path": ledger_path.relative_to(root).as_posix(),
            "intake_sha256": intake_sha, "bundle_sha256": bundle["bundle_sha256"],
            "line_sha256": line_hashes}
