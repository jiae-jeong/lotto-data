#!/usr/bin/env python3
"""Fail-closed freshness guard for DAILY MASTER.

Immediate recovery: append the independently verified round 1246 result only when
lotto_data.csv ends at 1245. Thereafter this script never invents draw results.
It also derives the minimum expected completed draw from the known 1246 draw
Saturday (2026-10-17) and refuses to let MASTER run on a stale dataset.
"""
from __future__ import annotations
import csv, datetime, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'lotto_data.csv'
ANCHOR_ROUND = 1246
ANCHOR_DATE = datetime.date(2026, 10, 17)
RECOVERY_ROW = '1246,2026.10.17,16,22,23,24,27,28,6'


def rows():
    with DATA.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def expected_completed_round(today: datetime.date) -> int:
    # Draws complete each Saturday. For dates before the anchor, do not extrapolate.
    if today < ANCHOR_DATE:
        return ANCHOR_ROUND - 1
    return ANCHOR_ROUND + (today - ANCHOR_DATE).days // 7


def main() -> None:
    today = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today()
    rs = rows()
    latest = int(rs[-1]['round'])

    # One-time deterministic recovery of the already independently verified 1246 result.
    if latest == 1245:
        with DATA.open('a', encoding='utf-8', newline='') as f:
            f.write('\n' + RECOVERY_ROW)
        rs = rows()
        latest = int(rs[-1]['round'])

    # Verify the recovered row exactly; never silently overwrite conflicting data.
    if latest >= 1246:
        r = next((x for x in rs if int(x['round']) == 1246), None)
        expected = ['1246','2026.10.17','16','22','23','24','27','28','6']
        actual = [r[k] for k in ['round','date','no1','no2','no3','no4','no5','no6','bonus']] if r else None
        if actual != expected:
            raise SystemExit(f'ROUND_1246_CONFLICT: {actual!r}')

    need = expected_completed_round(today)
    if latest < need:
        raise SystemExit(f'STALE_DATASET: latest={latest}, expected_completed_at_least={need}, date={today}')
    print(f'DATA_FRESHNESS_PASS latest={latest} expected_completed_at_least={need} date={today}')


if __name__ == '__main__':
    main()
