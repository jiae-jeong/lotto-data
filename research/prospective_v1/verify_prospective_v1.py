#!/usr/bin/env python3
"""Read-only verification of the E043–E049 freeze and random5 pool."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path

from prepare_prospective_v1 import (CANONICAL_SHA256, E030, E030_PREDICTION_SHA256,
                                    OUT, ROOT, SINGLE_BASE_SEED, TARGET)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(require_e030: bool = False, require_canonical: bool = False) -> dict:
    protocol = OUT / "PROSPECTIVE_PROTOCOL.json"
    expected = (OUT / "PROSPECTIVE_PROTOCOL_SHA256.txt").read_text(encoding="utf-8").split()[0]
    if sha(protocol) != expected:
        raise ValueError("prospective protocol SHA mismatch")
    doc = json.loads(protocol.read_text(encoding="utf-8"))
    if doc["target_round"] != 1246 or doc["canonical_data"]["rounds"] != [1, 1245]:
        raise ValueError("unexpected target or cutoff")
    if doc["e030_immutable"]["sha256"] != E030_PREDICTION_SHA256:
        raise ValueError("E030 reference SHA mismatch")
    if E030.exists():
        if sha(E030) != E030_PREDICTION_SHA256:
            raise ValueError("E030 frozen prediction changed")
        frozen = json.loads(E030.read_text(encoding="utf-8"))
        if frozen["target_round"] != 1246 or frozen["training_through_round"] != 1245:
            raise ValueError("E030 frozen target/cutoff invalid")
    elif require_e030:
        raise FileNotFoundError(f"required E030 artifact missing: {E030}")
    canonical = ROOT / "analysis/2026-10-12/lotto_data_1_1245_snapshot.csv"
    canonical_sha = sha(canonical) if canonical.is_file() else None
    canonical_rows = 0
    if canonical.is_file():
        with canonical.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != 1245:
            raise ValueError(f"canonical snapshot must contain 1245 rows; found {len(rows)}")
        prior_date = None
        for expected_round, row in enumerate(rows, 1):
            if int(row["round"]) != expected_round:
                raise ValueError(f"canonical round discontinuity at row {expected_round}: {row['round']}")
            draw_date = datetime.strptime(row["date"], "%Y.%m.%d").date()
            if prior_date is not None and draw_date <= prior_date:
                raise ValueError(f"canonical draw date not increasing at round {expected_round}")
            prior_date = draw_date
            nums = [int(row[f"no{i}"]) for i in range(1,7)]
            bonus = int(row["bonus"])
            if len(set(nums)) != 6 or min(nums) < 1 or max(nums) > 45 or bonus < 1 or bonus > 45 or bonus in nums:
                raise ValueError(f"canonical number/bonus validation failed at round {expected_round}")
        canonical_rows = len(rows)
    elif require_canonical:
        raise FileNotFoundError(f"required canonical snapshot missing: {canonical}")
    if require_canonical and canonical_sha != CANONICAL_SHA256:
        raise ValueError(f"canonical 1..1245 snapshot SHA mismatch: {canonical_sha}")
    pool_doc = json.loads((OUT / "RANDOM5_BASELINE_1246.json").read_text(encoding="utf-8"))
    pool = ROOT / pool_doc["pool_path"]
    if sha(pool) != pool_doc["pool_sha256"] or pool_doc["seed"] != 20261014045 + 1246:
        raise ValueError("random5 frozen pool SHA/seed mismatch")
    count = 0
    with gzip.open(pool, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row["target_round"] != 1246 or row["portfolio_index"] != count + 1 or len(row["lines"]) != 5:
                raise ValueError(f"invalid random5 pool row {count+1}")
            if len({tuple(sorted(t)) for t in row["lines"]}) != 5:
                raise ValueError(f"duplicate lines in random5 portfolio {count+1}")
            for ticket in row["lines"]:
                if len(ticket) != 6 or len(set(ticket)) != 6 or min(ticket) < 1 or max(ticket) > 45:
                    raise ValueError(f"invalid ticket in random5 portfolio {count+1}")
            count += 1
    if count != 10_000:
        raise ValueError(f"expected 10000 random5 portfolios, got {count}")
    single_doc = json.loads((OUT / "SINGLE_TICKET_BASELINE_1246.json").read_text(encoding="utf-8"))
    single_path = ROOT / single_doc["pool_path"]
    if sha(single_path) != single_doc["pool_sha256"] or single_doc["seed"] != SINGLE_BASE_SEED + TARGET:
        raise ValueError("single-ticket random pool SHA/seed mismatch")
    single_count = 0
    with gzip.open(single_path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip(): continue
            row = json.loads(line); nums = row["numbers"]
            if row["target_round"] != TARGET or row["sample_index"] != single_count + 1 or len(nums) != 6 or len(set(nums)) != 6 or min(nums) < 1 or max(nums) > 45:
                raise ValueError(f"invalid single-ticket random row {single_count+1}")
            single_count += 1
    if single_count != 10_000:
        raise ValueError(f"expected 10000 single-ticket comparators, got {single_count}")
    for path in (OUT / "E046_SHADOW_LEDGER_1246.json", OUT / "E047_ANYTIME_VALID.json", OUT / "E048_POWER_AND_HORIZON.json", OUT / "E049_PROMOTION_GATE.json", OUT / "PURCHASE_LEDGER_SCHEMA.json"):
        json.loads(path.read_text(encoding="utf-8"))
    manifest_path = OUT / "SHA256_MANIFEST.csv"
    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    for row in manifest:
        path = (ROOT / row["path"]) if row["path"].startswith("analysis/") or row["path"].startswith("research/") else (OUT / row["path"])
        if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha(path) != row["sha256"]:
            raise ValueError(f"manifest mismatch: {row['path']}")
    return {"status": "PASS", "protocol_sha256": expected, "canonical_local_sha256": canonical_sha, "canonical_matches": canonical_sha == CANONICAL_SHA256, "canonical_rows_validated": canonical_rows,
            "random5_pool_sha256": pool_doc["pool_sha256"], "random5_portfolios": count, "single_ticket_pool_sha256": single_doc["pool_sha256"], "single_ticket_samples": single_count,
            "e030_present": E030.is_file(), "e030_sha256": E030_PREDICTION_SHA256 if E030.is_file() else None,
            "purchase_records": 0, "recommendation_lines_generated": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-e030", action="store_true")
    parser.add_argument("--require-canonical", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.require_e030, args.require_canonical), indent=2))
