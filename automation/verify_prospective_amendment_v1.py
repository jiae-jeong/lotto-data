#!/usr/bin/env python3
"""Verify the pre-outcome E048 amendment and its original-file anchors."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AMEND_DIR=ROOT/"analysis/2026-10-14/E048_PRE1246_AMENDMENT_v1"
AMEND=AMEND_DIR/"PROSPECTIVE_PROTOCOL_AMENDMENT_PRE1246_v1.json"
ORIGINAL=ROOT/"analysis/2026-10-14/E043_E049_PROSPECTIVE_EVIDENCE_v1"
EXPECTED_PROTOCOL_SHA="a1a7777dd5a1a01a91328b60695b5a6c7ebaa277dd5bafe2e1b8f826575e1abf"
EXPECTED_POWER_SHA="1eda3d67b486394e07310be72135d9657b327d87e04764a79ff5f0b20b8a9314"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> dict:
    amendment=json.loads(AMEND.read_text(encoding="utf-8"))
    if amendment["status"]!="FROZEN_PRE_TARGET_1246_OUTCOME":
        raise ValueError("amendment is not marked pre-outcome")
    if amendment["supersedes"]["protocol_sha256"]!=EXPECTED_PROTOCOL_SHA:
        raise ValueError("original protocol SHA anchor mismatch")
    if amendment["supersedes"]["power_sha256"]!=EXPECTED_POWER_SHA:
        raise ValueError("original E048 SHA anchor mismatch")
    if sha(ORIGINAL/"PROSPECTIVE_PROTOCOL.json")!=EXPECTED_PROTOCOL_SHA:
        raise ValueError("original prospective protocol changed")
    if sha(ORIGINAL/"E048_POWER_AND_HORIZON.json")!=EXPECTED_POWER_SHA:
        raise ValueError("original E048 power file changed")
    e047=json.loads((ORIGINAL/"E047_ANYTIME_VALID.json").read_text(encoding="utf-8"))
    if e047["familywise_alpha"]!=0.05 or e047["alpha_allocation"]!={"five_line_any3plus":0.02,"five_line_mean_max_hits":0.02,"shadow_single_ticket_mean_hits":0.01}:
        raise ValueError("E047 alpha or allocation changed")
    checkpoint=amendment["checkpoint"]
    if checkpoint!={"first_target":1246,"last_target":1445,"target_count":200,"status_name":"INTERIM_PROSPECTIVE_CHECKPOINT","confirmatory_horizon":False,"interpretation":"An interim evidence checkpoint; the 200-target point is not a claim that the registered effect sizes have adequate power."}:
        raise ValueError("amended checkpoint definition mismatch")
    if amendment["checkpoint_decision_rule"]["promotion_fail"]=="REJECTED":
        raise ValueError("failed checkpoint cannot default to REJECTED")
    sidecar=AMEND_DIR/"PROSPECTIVE_PROTOCOL_AMENDMENT_PRE1246_v1_SHA256.txt"
    expected=sidecar.read_text(encoding="utf-8").split()[0]
    if sha(AMEND)!=expected:
        raise ValueError("amendment SHA sidecar mismatch")
    manifest_path=AMEND_DIR/"SHA256_MANIFEST.csv"
    with manifest_path.open(encoding="utf-8-sig",newline="") as stream:
        manifest=list(csv.DictReader(stream))
    for row in manifest:
        path=ROOT/row["path"]
        if not path.is_file() or path.stat().st_size!=int(row["bytes"]) or sha(path)!=row["sha256"]:
            raise ValueError(f"amendment manifest mismatch: {row['path']}")
    return {"status":"PASS","amendment_sha256":expected,"original_protocol_sha256":EXPECTED_PROTOCOL_SHA,
            "original_e048_sha256":EXPECTED_POWER_SHA,"e047_alpha_unchanged":True,
            "checkpoint":"INTERIM_PROSPECTIVE_CHECKPOINT","pre_outcome":True}


if __name__=="__main__":
    print(json.dumps(verify(),indent=2))
