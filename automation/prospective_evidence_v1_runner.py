#!/usr/bin/env python3
"""Advance the pre-registered prospective ledger after an independently checked draw.

The canonical CSV is changed only by appending exactly one verified official row.
Predictions, random pools and outcomes are separate create-once artifacts.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import urllib.error
import urllib.request
import io
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/prospective_v1"))
import ledger_v1 as ledger
import prepare_prospective_v1 as prospective
import prospective_checkpoint_v1 as checkpoint
from prospective_purchase_intake_v1 import IntakeRejected, seal_intake

CANONICAL = ROOT / "lotto_data.csv"
OFFICIAL_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
SECONDARY_URL = "https://645.live/api/lotto-draws/{}.json"
E030_ROOT = ROOT / "analysis/2026-10-14/gha_38512512127_1/E030_PROSPECTIVE_SIGNAL_FREEZE_v1"
E030_1246 = E030_ROOT / "FROZEN_SIGNALS_1246.json"
TRACKER = ROOT / "analysis/prospective_v1"
EXPECTED_BASELINE = "e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def fetch_json(url: str, opener=urllib.request.urlopen) -> dict | None:
    request = urllib.request.Request(url, headers={"User-Agent": "lotto-prospective-evidence/1.0"})
    try:
        with opener(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload if isinstance(payload, dict) else None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError, OSError):
        return None


def _number_list(payload: dict) -> list[int] | None:
    for key in ("numbers", "main_numbers", "winningNumbers", "winning_numbers", "drwNumbers", "drawNumbers"):
        val = payload.get(key)
        if isinstance(val, list) and len(val) == 6:
            return [int(x) for x in val]
    for prefix in ("drwtNo", "drwt_no", "num"):
        try:
            return [int(payload[f"{prefix}{i}"]) for i in range(1, 7)]
        except (KeyError, TypeError, ValueError):
            continue
    return None


def parse_official(payload: dict | None, target: int) -> dict | None:
    if not payload or payload.get("returnValue") != "success":
        return None
    if int(payload.get("drwNo", -1)) != target:
        raise ValueError("official source returned a different round")
    nums = _number_list(payload)
    bonus = payload.get("bnusNo", payload.get("bonus", payload.get("bonusNumber")))
    if nums is None or bonus is None:
        raise ValueError("official source response is missing winning numbers/bonus")
    return _validate_draw(target, payload.get("drwNoDate", payload.get("date")), nums, int(bonus),
                          "OFFICIAL_DONGHAENG_LOTTERY", OFFICIAL_URL.format(target))


def _find_secondary_record(value, target: int) -> dict | None:
    if isinstance(value, list):
        for item in value:
            found = _find_secondary_record(item, target)
            if found is not None: return found
    if not isinstance(value, dict): return None
    for key in ("draw", "data", "result", "item", "lottoDraw"):
        if key in value:
            found = _find_secondary_record(value[key], target)
            if found is not None: return found
    round_value = value.get("round", value.get("drwNo", value.get("drawNo", value.get("draw_number"))))
    if round_value is None or int(round_value) != target:
        return None
    return value


def parse_secondary(payload: dict | None, target: int) -> dict | None:
    if not payload or payload.get("error") or payload.get("status") == "error":
        return None
    record = _find_secondary_record(payload, target)
    if record is None: return None
    nums = _number_list(record)
    bonus = record.get("bonus", record.get("bonusNumber", record.get("bonus_number", record.get("bnusNo"))))
    draw_date = record.get("date", record.get("drawDate", record.get("draw_date", record.get("drwNoDate"))))
    if nums is None or bonus is None or draw_date is None:
        raise ValueError("secondary provider returned target round without full result fields")
    return _validate_draw(target, draw_date, nums, int(bonus), "INDEPENDENT_645_LIVE_SNAPSHOT", SECONDARY_URL.format(target))


def _validate_draw(target: int, draw_date, numbers: list[int], bonus: int, source_type: str, url: str) -> dict:
    if isinstance(draw_date, date):
        parsed_date = draw_date
    else:
        raw = str(draw_date)
        parsed_date = None
        for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
            try: parsed_date = datetime.strptime(raw, fmt).date(); break
            except ValueError: pass
        if parsed_date is None: raise ValueError(f"invalid date from {source_type}: {raw}")
    nums = sorted(int(n) for n in numbers)
    if len(nums) != 6 or len(set(nums)) != 6 or nums[0] < 1 or nums[-1] > 45 or not 1 <= bonus <= 45 or bonus in nums:
        raise ValueError(f"invalid numbers from {source_type} for round {target}")
    return {"round": target, "date": parsed_date.isoformat(), "numbers": nums, "bonus": bonus,
            "source_type": source_type, "url": url}


def load_draws(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows: raise ValueError("canonical lotto_data.csv is empty")
    draws = []
    prior_date = None
    for expected, row in enumerate(rows, 1):
        if int(row["round"]) != expected: raise ValueError(f"canonical discontinuity at row {expected}")
        draw = _validate_draw(expected, row["date"], [int(row[f"no{i}"]) for i in range(1,7)], int(row["bonus"]), "CANONICAL_CSV", str(path))
        dt = date.fromisoformat(draw["date"])
        if prior_date and dt <= prior_date: raise ValueError(f"canonical dates are not increasing at round {expected}")
        prior_date = dt
        draws.append(draw)
    return draws


def _sum_bin(total: int) -> int:
    return 0 if total < 120 else 1 if total < 145 else 2 if total < 170 else 3


def _season(month: int) -> int:
    return 0 if month in (12,1,2) else 1 if month in (3,4,5) else 2 if month in (6,7,8) else 3


def make_next_shadow(draws: list[dict], target: int, generated_at: str, data_sha: str) -> dict:
    if len(draws) != target - 1 or [x["round"] for x in draws] != list(range(1,target)):
        raise ValueError("next shadow prediction requires a complete 1..target-1 history")
    target_date = date.fromisoformat(draws[-1]["date"]) + timedelta(days=7)
    global_counts = [0] * 45; seasonal_counts = [0] * 45; conditioned_counts = [0] * 45
    season_n = 0; reg_n = 0; regime = _sum_bin(sum(draws[-1]["numbers"]))
    for i, draw in enumerate(draws):
        for n in draw["numbers"]: global_counts[n-1] += 1
        if _season(date.fromisoformat(draw["date"]).month) == _season(target_date.month):
            season_n += 1
            for n in draw["numbers"]: seasonal_counts[n-1] += 1
        if i > 0 and _sum_bin(sum(draws[i-1]["numbers"])) == regime:
            reg_n += 1
            for n in draw["numbers"]: conditioned_counts[n-1] += 1
    global_rate = [x/len(draws) for x in global_counts]
    season_score = [(seasonal_counts[i] + 30.0*global_rate[i])/(season_n+30.0) for i in range(45)]
    regime_score = [(conditioned_counts[i] + 20.0*global_rate[i])/(reg_n+20.0) for i in range(45)]
    signals=[]
    for name, scores in (("CALENDAR_SEASON_CONDITIONAL_v1",season_score),("PREVIOUS_SUM_REGIME_CONDITIONAL_v1",regime_score)):
        order=sorted(range(45),key=lambda i:(-scores[i],i))
        signals.append({"signal":name,"formula_version":"E025_FROZEN_v1","numbers":sorted(i+1 for i in order[:6]),"score_order":[i+1 for i in order]})
    return {"status":"FROZEN_PROSPECTIVE_SHADOW_ONLY","target_round":target,"training_through_round":target-1,
            "canonical_data_sha256":data_sha,"config_sha256":prospective.E030_CONFIG_SHA256,
            "code_sha256":sha_file(Path(__file__)),"generated_at_utc":generated_at,
            "target_draw_date_assumption":target_date.isoformat(),"signals":signals,
            "editing_policy":"immutable; corrections require new version and documented reason","purchase_recommendation":False}


def _write_once_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write("\n")


def _require_existing_identity(path: Path, expected: dict, identity_fields: tuple[str, ...]) -> dict:
    """Reuse an existing immutable event only when its recorded identity matches."""
    existing = json.loads(path.read_text(encoding="utf-8"))
    for field in identity_fields:
        if existing.get(field) != expected.get(field):
            raise ValueError(f"immutable event mismatch at {path}: {field}")
    return existing


def _ensure_outcome_event(root: Path, actual: dict) -> Path:
    path = root / "analysis/prospective_v1/outcomes" / f"ROUND_{actual['target_round']}.json"
    if path.exists():
        _require_existing_identity(path, {
            "target_round": actual["target_round"], "draw_date": actual["draw_date"],
            "main_numbers": sorted(actual["main_numbers"]), "bonus": actual["bonus"]
        }, ("target_round", "draw_date", "main_numbers", "bonus"))
        return path
    return ledger.write_outcome_event(root, actual)


def _ensure_evaluation(path: Path, identity: dict, fields: tuple[str, ...], create) -> dict:
    if path.exists():
        return _require_existing_identity(path, identity, fields)
    return create()


def _freeze_next_target(root: Path, draws: list[dict], target: int, generated_at: str,
                        data_sha: str) -> tuple[Path, dict]:
    """Recover or create the next target only after prior target evidence is recorded."""
    prior = target - 1
    outcomes = root / "analysis/prospective_v1/outcomes"
    for name in (f"ROUND_{prior}.json", f"E046_SHADOW_OUTCOME_{prior}.json", f"E045_RANDOM5_OUTCOME_{prior}.json"):
        if not (outcomes / name).is_file():
            raise FileNotFoundError(f"cannot freeze target {target}; prior-round evidence missing: {name}")
    round_dir = root / "analysis/prospective_v1/rounds" / str(target)
    pred_path = round_dir / f"FROZEN_SIGNALS_{target}.json"
    if pred_path.exists():
        prediction = json.loads(pred_path.read_text(encoding="utf-8"))
        if prediction.get("target_round") != target or prediction.get("training_through_round") != target - 1 or prediction.get("canonical_data_sha256") != data_sha:
            raise ValueError(f"existing next prediction has incorrect target/cutoff/data SHA: {pred_path}")
    else:
        snapshot_path = root / "analysis/prospective_v1/canonical_snapshots" / f"lotto_data_1_{target-1}.csv"
        canonical_bytes = (root / "lotto_data.csv").read_bytes()
        if snapshot_path.exists():
            if snapshot_path.read_bytes() != canonical_bytes:
                raise ValueError(f"existing canonical snapshot differs from current canonical file: {snapshot_path}")
        else:
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            with snapshot_path.open("xb") as stream: stream.write(canonical_bytes)
        prediction = make_next_shadow(draws, target, generated_at, data_sha)
        _write_once_json(pred_path, prediction)
    seal_path = round_dir / f"RANDOM_BASELINE_SEAL_{target}.json"
    if seal_path.exists():
        seal = json.loads(seal_path.read_text(encoding="utf-8"))
        ledger.read_random5_pool(root / seal["random5_path"], seal["random5_sha256"])
        if sha_file(root / seal["single_path"]) != seal["single_sha256"]:
            raise ValueError(f"existing single-ticket pool SHA mismatch for target {target}")
        return pred_path, seal
    # A crash may occur after the pool helper writes its date-stamped seal but
    # before this round-indexed pointer is saved. Reuse that exact pool.
    existing_seals = list((root / "analysis").rglob(f"RANDOM_BASELINE_SEAL_{target}.json"))
    if existing_seals:
        source = existing_seals[0]
        seal = json.loads(source.read_text(encoding="utf-8"))
        if int(seal.get("target_round", -1)) != target:
            raise ValueError("random baseline seal target mismatch")
        ledger.read_random5_pool(root / seal["random5_path"], seal["random5_sha256"])
        if sha_file(root / seal["single_path"]) != seal["single_sha256"]:
            raise ValueError("single-ticket random pool SHA mismatch")
    else:
        next_draw_at = f"{(date.fromisoformat(draws[-1]['date']) + timedelta(days=7)).isoformat()}T20:45:00+09:00"
        seal = ledger.freeze_random_pools(root, target, next_draw_at)
    _write_once_json(seal_path, seal)
    return pred_path, seal


def _csv_append_row(path: Path, draw: dict) -> str:
    before = path.read_bytes()
    prior_sha = sha_bytes(before)
    lines = before.splitlines()
    if not lines: raise ValueError("canonical CSV has no header")
    row = [draw["round"], draw["date"].replace("-", "."), *draw["numbers"], draw["bonus"]]
    text = ("\n" if not before.endswith((b"\n", b"\r")) else "") + ",".join(str(x) for x in row) + "\n"
    with path.open("ab") as stream:
        if sha_bytes(path.read_bytes()) != prior_sha: raise ValueError("canonical CSV changed during append guard")
        stream.write(text.encode("utf-8"))
    after = path.read_bytes()
    if not after.startswith(before): raise ValueError("canonical CSV prefix changed; append rejected")
    return sha_bytes(after)


def _write_cumulative_evidence(target: int) -> Path:
    shadow_files = sorted((TRACKER / "outcomes").glob("E046_SHADOW_OUTCOME_*.json"), key=lambda p:int(p.stem.split("_")[-1]))
    purchase_files = sorted((TRACKER / "outcomes").glob("E044_PURCHASE_OUTCOME_*.json"), key=lambda p:int(p.stem.split("_")[-1]))
    shadow_by_round={}; any3_by_round={}; max_by_round={}; any4_by_round={}
    for path in shadow_files:
        if int(json.loads(path.read_text(encoding="utf-8"))["target_round"])>target: continue
        row=json.loads(path.read_text(encoding="utf-8")); models=row["models"]
        if models:
            t=int(row["target_round"])
            shadow_by_round[t]=sum(x["model_hits"]-x["same_target_random_mean_hits"] for x in models)/len(models)
    purchase_map={int(json.loads(p.read_text(encoding="utf-8"))["target_round"]):json.loads(p.read_text(encoding="utf-8")) for p in purchase_files}
    for path in sorted((TRACKER / "outcomes").glob("E045_RANDOM5_OUTCOME_*.json"),key=lambda p:int(p.stem.split("_")[-1])):
        random_result=json.loads(path.read_text(encoding="utf-8")); t=int(random_result["target_round"])
        if t not in purchase_map or t>target: continue
        purchase=purchase_map[t]; rand=random_result["random5_metric_means"]
        any3_by_round[t]=float(purchase["any3plus"])-float(rand["any3plus"])
        max_by_round[t]=float(purchase["max_hits"])-float(rand["max_hits"])
        any4_by_round[t]=float(purchase["any4plus"])-float(rand["any4plus"])
    shadow_d=[shadow_by_round[t] for t in sorted(shadow_by_round)]
    any3_d=[any3_by_round[t] for t in sorted(any3_by_round)]
    max_d=[max_by_round[t] for t in sorted(max_by_round)]
    any4_d=[any4_by_round[t] for t in sorted(any4_by_round)]
    lambdas=[0.005,0.01,0.02,0.04,0.08,0.16,0.32]
    shadow_e=ledger.mixture_e_value(shadow_d,-6,6,[0.001,0.002,0.004,0.008,0.016,0.032,0.064])
    any3_e=ledger.mixture_e_value(any3_d,-1,1,lambdas)
    max_e=ledger.mixture_e_value(max_d,-6,6,lambdas)
    checkpoint_reached=target>=1445
    checkpoint_rounds=list(range(1246,1446)) if checkpoint_reached else []
    checkpoint_complete=(checkpoint_reached and all(t in shadow_by_round for t in checkpoint_rounds)
        and all(t in any3_by_round and t in max_by_round and t in any4_by_round for t in checkpoint_rounds))
    gate_result={"pass":False,"reason":"checkpoint_not_reached"}
    checkpoint_evalues={"any3plus":None,"max_hits":None,"shadow_mean_hits":None}
    if checkpoint_complete:
        cp_any3=[any3_by_round[t] for t in checkpoint_rounds]
        cp_max=[max_by_round[t] for t in checkpoint_rounds]
        cp_any4=[any4_by_round[t] for t in checkpoint_rounds]
        cp_shadow=[shadow_by_round[t] for t in checkpoint_rounds]
        checkpoint_evalues={"any3plus":ledger.mixture_e_value(cp_any3,-1,1,lambdas),
            "max_hits":ledger.mixture_e_value(cp_max,-6,6,lambdas),
            "shadow_mean_hits":ledger.mixture_e_value(cp_shadow,-6,6,[0.001,0.002,0.004,0.008,0.016,0.032,0.064])}
        gate_result=checkpoint.promotion_gates(
            cp_any3,cp_max,cp_any4,cp_shadow,checkpoint_evalues["any3plus"],
            checkpoint_evalues["max_hits"],shadow_e_value=checkpoint_evalues["shadow_mean_hits"])
    promotion_status=checkpoint.checkpoint_status(200 if checkpoint_reached else target-1245,
        bool(gate_result.get("pass")),futility_registered=False,futility_met=False)
    integrity_failures=0
    if checkpoint_reached:
        for t in checkpoint_rounds:
            shadow_path=TRACKER/"outcomes"/f"E046_SHADOW_OUTCOME_{t}.json"
            shadow_record=json.loads(shadow_path.read_text(encoding="utf-8")) if shadow_path.exists() else {}
            if (not shadow_record or int(shadow_record.get("prediction_provenance",{}).get("training_cutoff",-1))!=t-1
                    or int(shadow_record.get("prediction_provenance",{}).get("leakage_failures",-1))!=0):
                integrity_failures+=1
                continue
            if t==1246:
                expected_prediction_sha=prospective.E030_PREDICTION_SHA256
            else:
                seal_path=ROOT/"analysis/prospective_v1/rounds"/str(t)/f"SHADOW_PREDICTION_SEAL_{t}.json"
                if not seal_path.is_file():
                    integrity_failures+=1
                    continue
                expected_prediction_sha=json.loads(seal_path.read_text(encoding="utf-8"))["prediction_sha256"]
            if shadow_record.get("prediction_file_sha256")!=expected_prediction_sha:
                integrity_failures+=1
        if integrity_failures:
            promotion_status="PROSPECTIVE_INSUFFICIENT_EVIDENCE"
    result={"study_id":"E047_E049_CUMULATIVE_EVIDENCE_v1","through_target":target,
            "shadow_model_mean_hit_differences":shadow_d,"shadow_mean_hit_e_value":shadow_e,
            "actual_five_line_any3plus_differences":any3_d,"actual_five_line_any3plus_e_value":any3_e,
            "actual_five_line_max_hit_differences":max_d,"actual_five_line_max_hit_e_value":max_e,
            "actual_five_line_any4plus_differences":any4_d,
            "targets_with_verified_purchase":len(any3_d),"prospective_targets_with_shadow":len(shadow_d),
            "checkpoint_status":"INTERIM_PROSPECTIVE_CHECKPOINT" if checkpoint_reached else "PROSPECTIVE_PENDING",
            "checkpoint_target_count":max(0,target-1245),"checkpoint_e_values":checkpoint_evalues,
            "checkpoint_promotion_gates":gate_result,
            "checkpoint_integrity_failures":integrity_failures,"promotion_status":promotion_status,
            "rejection_enabled":False,"rejection_reason":"no pre-registered numeric futility/equivalence boundary",
            "formal_promotion_before_200_targets":False}
    out=TRACKER/"evidence"/f"EVIDENCE_THROUGH_{target}.json"
    _write_once_json(out,result)
    return out


def _write_round_audit(root: Path, target: int, prediction_path: Path, prediction_sha: str,
                       random5_path: Path, random5_sha: str, single_path: Path,
                       single_sha: str, data_sha: str, purchase_present: bool) -> Path:
    """Create a per-target completion record and hash manifest, write-once."""
    folder=root/"analysis/prospective_v1/rounds"/str(target)
    folder.mkdir(parents=True,exist_ok=True)
    verification_path=folder/"VERIFICATION.json"
    verification={"study_id":"PROSPECTIVE_ROUND_EVALUATION_v1","status":"PASS",
        "target_round":target,"training_cutoff":target-1,"feature_max_round":target-1,
        "prediction_path":prediction_path.relative_to(root).as_posix(),"prediction_sha256":prediction_sha,
        "random5_pool_sha256":random5_sha,"single_ticket_pool_sha256":single_sha,
        "canonical_after_append_sha256":data_sha,"leakage_failures":0,"future_predictions":0,
        "purchase_record_present":purchase_present,"recommendation_lines_generated":0}
    if verification_path.exists():
        _require_existing_identity(verification_path,verification,("target_round","training_cutoff","prediction_sha256","random5_pool_sha256","single_ticket_pool_sha256","canonical_after_append_sha256"))
    else:
        _write_once_json(verification_path,verification)
    completion_path=folder/"COMPLETION.json"
    completion={"study_id":"PROSPECTIVE_ROUND_EVALUATION_v1","status":"OUTCOME_EVALUATED_AND_NEXT_TARGET_FROZEN",
        "target_round":target,"created_at_utc":datetime.now(timezone.utc).isoformat(),
        "recommendation_lines_generated":0,"purchase_record_present":purchase_present}
    if completion_path.exists():
        _require_existing_identity(completion_path,completion,("target_round","status","recommendation_lines_generated","purchase_record_present"))
    else:
        _write_once_json(completion_path,completion)
    report_path=folder/"REPORT.md"
    report=(f"# Prospective target {target} evaluation\n\n"
        f"Status: `OUTCOME_EVALUATED_AND_NEXT_TARGET_FROZEN`. Training cutoff: {target-1}. "
        f"Prediction SHA-256: `{prediction_sha}`. Random five-line pool SHA-256: `{random5_sha}`. "
        f"Single-ticket pool SHA-256: `{single_sha}`. Canonical data SHA-256 after append: `{data_sha}`.\n\n"
        f"Leakage failures: 0. Future predictions: 0. Verified purchase record present: `{str(purchase_present).lower()}`. "
        "No purchase recommendations or number sets were generated. Outcome data is stored separately from the frozen prediction.\n")
    if report_path.exists():
        if report_path.read_text(encoding="utf-8")!=report: raise ValueError(f"immutable round report mismatch: {report_path}")
    else:
        report_path.write_text(report,encoding="utf-8",newline="\n")
    manifest_path=folder/"SHA256_MANIFEST.csv"
    manifest_rows=[]
    for path in (prediction_path,random5_path,single_path,
                 root/"analysis/prospective_v1/outcomes"/f"ROUND_{target}.json",
                 root/"analysis/prospective_v1/outcomes"/f"E046_SHADOW_OUTCOME_{target}.json",
                 root/"analysis/prospective_v1/outcomes"/f"E045_RANDOM5_OUTCOME_{target}.json",
                 root/"analysis/prospective_v1/evidence"/f"EVIDENCE_THROUGH_{target}.json",
                 root/"lotto_data.csv",verification_path,completion_path,report_path):
        if not path.is_file(): raise FileNotFoundError(f"round manifest input missing: {path}")
        manifest_rows.append((path.relative_to(root).as_posix(),path.stat().st_size,sha_file(path)))
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8-sig",newline="") as stream:
            existing=list(csv.DictReader(stream))
        expected=[{"path":p,"bytes":str(size),"sha256":digest} for p,size,digest in manifest_rows]
        if existing!=expected: raise ValueError(f"immutable round manifest mismatch: {manifest_path}")
    else:
        buf=io.StringIO(newline="")
        writer=csv.writer(buf);writer.writerow(("path","bytes","sha256"));writer.writerows(manifest_rows)
        manifest_path.write_text(buf.getvalue(),encoding="utf-8",newline="")
    return verification_path


def run(root: Path = ROOT, opener=urllib.request.urlopen) -> dict:
    root=root.resolve()
    data=root/"lotto_data.csv"
    draws=load_draws(data)
    target=len(draws)+1
    if target == 1246:
        prediction_path=root/E030_1246.relative_to(ROOT)
    else:
        prediction_path=root/"analysis/prospective_v1/rounds"/str(target)/f"FROZEN_SIGNALS_{target}.json"
    if not prediction_path.is_file():
        # Recover the narrow crash window after the verified draw row was
        # appended but before the next prediction and comparator pools froze.
        prior = target - 1
        prior_event = root / "analysis/prospective_v1/outcomes" / f"ROUND_{prior}.json"
        if target > 1246 and prior_event.is_file():
            prior_doc = json.loads(prior_event.read_text(encoding="utf-8"))
            latest = draws[-1]
            if (int(prior_doc.get("target_round", -1)) != prior
                    or prior_doc.get("draw_date") != latest["date"].isoformat()
                    or sorted(prior_doc.get("main_numbers", [])) != sorted(latest["numbers"])
                    or int(prior_doc.get("bonus", -1)) != latest["bonus"]):
                raise ValueError("canonical latest row does not match prior immutable outcome event")
            previous_prediction = root / "analysis/prospective_v1/rounds" / str(prior) / f"FROZEN_SIGNALS_{prior}.json"
            if prior == 1246:
                previous_prediction = root / E030_1246.relative_to(ROOT)
            if not previous_prediction.is_file():
                raise FileNotFoundError(f"cannot recover next target; prior prediction missing: {previous_prediction}")
            prior_sha = sha_file(previous_prediction)
            if prior == 1246:
                prior_sha = prospective.E030_PREDICTION_SHA256
            ledger.validate_frozen_prediction(root, previous_prediction, prior, prior_sha, allow_outcome=True)
            evidence_path=TRACKER/"evidence"/f"EVIDENCE_THROUGH_{prior}.json"
            if evidence_path.exists():
                _require_existing_identity(evidence_path,{"through_target":prior},("through_target",))
            else:
                _write_cumulative_evidence(prior)
            if prior==1246:
                baseline_doc=json.loads((root/"analysis/2026-10-14/E043_E049_PROSPECTIVE_EVIDENCE_v1/RANDOM5_BASELINE_1246.json").read_text(encoding="utf-8"))
                single_doc=json.loads((root/"analysis/2026-10-14/E043_E049_PROSPECTIVE_EVIDENCE_v1/SINGLE_TICKET_BASELINE_1246.json").read_text(encoding="utf-8"))
                prior_random5=root/baseline_doc["pool_path"];prior_random5_sha=baseline_doc["pool_sha256"]
                prior_single=root/single_doc["pool_path"];prior_single_sha=single_doc["pool_sha256"]
            else:
                prior_seal=json.loads((root/"analysis/prospective_v1/rounds"/str(prior)/f"RANDOM_BASELINE_SEAL_{prior}.json").read_text(encoding="utf-8"))
                prior_random5=root/prior_seal["random5_path"];prior_random5_sha=prior_seal["random5_sha256"]
                prior_single=root/prior_seal["single_path"];prior_single_sha=prior_seal["single_sha256"]
            prior_purchase=(root/"analysis/prospective_v1/purchases"/f"ROUND_{prior}.json").is_file()
            _write_round_audit(root,prior,previous_prediction,prior_sha,prior_random5,prior_random5_sha,
                               prior_single,prior_single_sha,sha_file(data),prior_purchase)
            recovered_path, recovered_seal = _freeze_next_target(root, draws, target,
                datetime.now(timezone.utc).isoformat(), sha_file(data))
            return {"status":"NEXT_TARGET_RECOVERED_AFTER_PRIOR_APPEND", "target_round":prior,
                    "next_target":target, "next_prediction_path":recovered_path.relative_to(root).as_posix(),
                    "next_prediction_sha256":sha_file(recovered_path), "next_random5_pool_sha256":recovered_seal["random5_sha256"],
                    "next_single_pool_sha256":recovered_seal["single_sha256"], "recommendation_generated":False}
        raise FileNotFoundError(f"pre-draw frozen shadow prediction required for round {target}")
    prediction=json.loads(prediction_path.read_text(encoding="utf-8"))
    prediction_sha=sha_file(prediction_path)
    if target == 1246:
        expected=prospective.E030_PREDICTION_SHA256
    else:
        expected=prediction_sha
    ledger.validate_frozen_prediction(root,prediction_path,target,expected)
    if target > 1246:
        # Complete a partially written prior-run freeze before checking whether
        # this target's draw is available. This only reuses or creates pre-draw
        # artifacts and never recalculates an existing prediction.
        _freeze_next_target(root,draws,target,
            prediction.get("generated_at_utc",datetime.now(timezone.utc).isoformat()),sha_file(data))
        prior=target-1
        prior_prediction=root/E030_1246.relative_to(ROOT) if prior==1246 else root/"analysis/prospective_v1/rounds"/str(prior)/f"FROZEN_SIGNALS_{prior}.json"
        prior_sha=prospective.E030_PREDICTION_SHA256 if prior==1246 else sha_file(prior_prediction)
        if prior==1246:
            prior_random_doc=json.loads((root/"analysis/2026-10-14/E043_E049_PROSPECTIVE_EVIDENCE_v1/RANDOM5_BASELINE_1246.json").read_text(encoding="utf-8"))
            prior_single_doc=json.loads((root/"analysis/2026-10-14/E043_E049_PROSPECTIVE_EVIDENCE_v1/SINGLE_TICKET_BASELINE_1246.json").read_text(encoding="utf-8"))
            prior_random5=root/prior_random_doc["pool_path"];prior_random5_sha=prior_random_doc["pool_sha256"]
            prior_single=root/prior_single_doc["pool_path"];prior_single_sha=prior_single_doc["pool_sha256"]
        else:
            prior_seal=json.loads((root/"analysis/prospective_v1/rounds"/str(prior)/f"RANDOM_BASELINE_SEAL_{prior}.json").read_text(encoding="utf-8"))
            prior_random5=root/prior_seal["random5_path"];prior_random5_sha=prior_seal["random5_sha256"]
            prior_single=root/prior_seal["single_path"];prior_single_sha=prior_seal["single_sha256"]
        if (root/"analysis/prospective_v1/outcomes"/f"ROUND_{prior}.json").is_file():
            _write_round_audit(root,prior,prior_prediction,prior_sha,prior_random5,prior_random5_sha,
                               prior_single,prior_single_sha,sha_file(data),
                               (root/"analysis/prospective_v1/purchases"/f"ROUND_{prior}.json").is_file())
    try:
        intake_status=seal_intake(root,target,opener=opener)
    except IntakeRejected as error:
        # A late or edited intake must not prevent processing an already-published
        # official outcome in this same scheduled run.
        intake_status={"status":"REJECTED","target_round":target,"reason":str(error)}
    primary=parse_official(fetch_json(OFFICIAL_URL.format(target),opener),target)
    secondary=parse_secondary(fetch_json(SECONDARY_URL.format(target),opener),target)
    if primary is None or secondary is None:
        return {"status":"PENDING_INDEPENDENT_SOURCE_CONFIRMATION","target_round":target,
                "official_available":primary is not None,"secondary_available":secondary is not None,
                "data_changed":False,"prediction_sha256":prediction_sha,"purchase_intake":intake_status}
    if (primary["date"],primary["numbers"],primary["bonus"]) != (secondary["date"],secondary["numbers"],secondary["bonus"]):
        raise ValueError(f"official and independent sources disagree for round {target}; no files changed")
    actual={"target_round":target,"draw_date":primary["date"],"draw_at_utc":f"{primary['date']}T20:45:00+09:00",
            "main_numbers":primary["numbers"],"bonus":primary["bonus"],
            "source_evidence":[{"source_type":primary["source_type"],"url":primary["url"]},
                               {"source_type":secondary["source_type"],"url":secondary["url"]}]}
    # Check all pre-draw artifacts before touching canonical raw data.
    if target==1246:
        base= root/"analysis/2026-10-14/E043_E049_PROSPECTIVE_EVIDENCE_v1/RANDOM5_BASELINE_1246.json"
        single_doc=root/"analysis/2026-10-14/E043_E049_PROSPECTIVE_EVIDENCE_v1/SINGLE_TICKET_BASELINE_1246.json"
        random5_doc=json.loads(base.read_text(encoding="utf-8")); single=json.loads(single_doc.read_text(encoding="utf-8"))
        random5_path=root/random5_doc["pool_path"]; random5_sha=random5_doc["pool_sha256"]
        single_path=root/single["pool_path"]; single_sha=single["pool_sha256"]
    else:
        round_dir=root/"analysis/prospective_v1/rounds"/str(target)
        seal=json.loads((round_dir/f"RANDOM_BASELINE_SEAL_{target}.json").read_text(encoding="utf-8"))
        random5_path=root/seal["random5_path"]; random5_sha=seal["random5_sha256"]
        single_path=root/seal["single_path"]; single_sha=seal["single_sha256"]
    ledger.read_random5_pool(random5_path,random5_sha)
    if sha_file(single_path)!=single_sha: raise ValueError("single-ticket baseline pool SHA mismatch")
    # Cross-source evidence is now complete. Write immutable outcome artifacts
    # before appending canonical data so a partial run can be resumed safely.
    event_path=_ensure_outcome_event(root,actual)
    outcome_dir=TRACKER/"outcomes"
    shadow_outcome=outcome_dir/f"E046_SHADOW_OUTCOME_{target}.json"
    ledger.evaluate_shadow_prediction(root,prediction_path,prediction_sha,single_path,single_sha,actual,shadow_outcome) if not shadow_outcome.exists() else _require_existing_identity(shadow_outcome,{"target_round":target,"prediction_file_sha256":prediction_sha,"official_main_numbers":sorted(primary["numbers"]),"random_single_pool_sha256":single_sha},("target_round","prediction_file_sha256","official_main_numbers","random_single_pool_sha256"))
    random_outcome=outcome_dir/f"E045_RANDOM5_OUTCOME_{target}.json"
    ledger.evaluate_random5_pool(random5_path,random5_sha,actual,random_outcome) if not random_outcome.exists() else _require_existing_identity(random_outcome,{"target_round":target,"pool_sha256":random5_sha},("target_round","pool_sha256"))
    purchase_path=TRACKER/"purchases"/f"ROUND_{target}.json"
    if purchase_path.is_file():
        purchase=ledger.verify_purchase_bundle(purchase_path)
        purchase_outcome=outcome_dir/f"E044_PURCHASE_OUTCOME_{target}.json"
        ledger.evaluate_purchase(purchase_path,actual,purchase_outcome) if not purchase_outcome.exists() else _require_existing_identity(purchase_outcome,{"target_round":target,"purchase_file_sha256":sha_file(purchase_path),"official_main_numbers":sorted(primary["numbers"])},("target_round","purchase_file_sha256","official_main_numbers"))
    # Append-only canonical update occurs only after all outcome artifacts exist.
    if len(draws) != target - 1:
        raise ValueError("canonical cutoff changed while processing the verified draw")
    new_data_sha=_csv_append_row(data,primary)
    draws.append({"round":target,"date":primary["date"],"numbers":primary["numbers"],"bonus":primary["bonus"]})
    evidence_path=_write_cumulative_evidence(target)
    next_target=target+1
    timestamp=datetime.now(timezone.utc).isoformat()
    pred_path,baseline_seal=_freeze_next_target(root,draws,next_target,timestamp,new_data_sha)
    seal_path=root/"analysis/prospective_v1/rounds"/str(next_target)/f"SHADOW_PREDICTION_SEAL_{next_target}.json"
    if not seal_path.exists():
        _write_once_json(seal_path,{"target_round":next_target,"training_cutoff":next_target-1,"prediction_path":pred_path.relative_to(root).as_posix(),
                               "prediction_sha256":sha_file(pred_path),"code_sha256":sha_file(Path(__file__)),"canonical_data_sha256":new_data_sha,
                               "random5_pool_sha256":baseline_seal["random5_sha256"],"single_ticket_pool_sha256":baseline_seal["single_sha256"],
                               "generated_at_utc":timestamp,"prediction_recommendation":False})
    else:
        _require_existing_identity(seal_path,{"target_round":next_target,"training_cutoff":next_target-1,"prediction_sha256":sha_file(pred_path),"canonical_data_sha256":new_data_sha},("target_round","training_cutoff","prediction_sha256","canonical_data_sha256"))
    _write_round_audit(root,target,prediction_path,prediction_sha,random5_path,random5_sha,
                       single_path,single_sha,new_data_sha,purchase_path.is_file())
    return {"status":"ROUND_RECORDED_AND_NEXT_SHADOW_FROZEN","target_round":target,"prediction_sha256":prediction_sha,
            "official_outcome_path":event_path.relative_to(root).as_posix(),"canonical_new_sha256":new_data_sha,
            "next_target":next_target,"next_prediction_path":pred_path.relative_to(root).as_posix(),
            "next_prediction_sha256":sha_file(pred_path),"next_random5_pool_sha256":baseline_seal["random5_sha256"],
            "next_single_pool_sha256":baseline_seal["single_sha256"],"cumulative_evidence_path":evidence_path.relative_to(root).as_posix(),
            "purchase_record_present":purchase_path.is_file(),"purchase_intake":intake_status,"recommendation_generated":False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(run(args.root),ensure_ascii=False,indent=2))

