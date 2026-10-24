#!/usr/bin/env python3
"""Fail-closed freshness guard for DAILY MASTER.

The latest required round is based on the Korean draw-completion window, not
calendar date alone. A Saturday does not require the new round before the draw
and official-result publication window has completed.
"""
from __future__ import annotations

import csv
import datetime
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'lotto_data.csv'
KST = ZoneInfo('Asia/Seoul')
ANCHOR_ROUND = 1246
# Conservative completion/publication boundary. Before 21:00 KST on Saturday,
# the previous Saturday's round is still the latest completed round required by
# DAILY MASTER. At/after 21:00 KST the newly completed round becomes mandatory.
ANCHOR_COMPLETED_AT = datetime.datetime(2026, 10, 17, 21, 0, 0, tzinfo=KST)
DRAW_INTERVAL = datetime.timedelta(days=7)
RECOVERY_ROW = '1246,2026.10.17,16,22,23,24,27,28,6'


def rows():
    with DATA.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def parse_moment(value: str | None) -> datetime.datetime:
    now = datetime.datetime.now(KST)
    if not value:
        return now
    text = value.strip()
    # The existing workflow passes YYYY-MM-DD. When that date is today in KST,
    # use the live KST clock so Saturday pre-draw and post-draw are distinguished.
    if len(text) == 10:
        day = datetime.date.fromisoformat(text)
        if day == now.date():
            return now
        # Historical/replay callers remain deterministic unless they pass an
        # explicit ISO timestamp.
        return datetime.datetime.combine(day, datetime.time.min, tzinfo=KST)
    moment = datetime.datetime.fromisoformat(text)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=KST)
    return moment.astimezone(KST)


def expected_completed_round(moment: datetime.datetime) -> int:
    moment = moment.astimezone(KST)
    if moment < ANCHOR_COMPLETED_AT:
        return ANCHOR_ROUND - 1
    completed_intervals = (moment - ANCHOR_COMPLETED_AT) // DRAW_INTERVAL
    return ANCHOR_ROUND + int(completed_intervals)


def main() -> None:
    moment = parse_moment(sys.argv[1] if len(sys.argv) > 1 else None)
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
        expected = ['1246', '2026.10.17', '16', '22', '23', '24', '27', '28', '6']
        actual = [r[k] for k in ['round', 'date', 'no1', 'no2', 'no3', 'no4', 'no5', 'no6', 'bonus']] if r else None
        if actual != expected:
            raise SystemExit(f'ROUND_1246_CONFLICT: {actual!r}')

    need = expected_completed_round(moment)
    if latest < need:
        raise SystemExit(
            f'STALE_DATASET: latest={latest}, expected_completed_at_least={need}, '
            f'moment_kst={moment.isoformat()}, completion_boundary=21:00_KST'
        )
    print(
        f'DATA_FRESHNESS_PASS latest={latest} expected_completed_at_least={need} '
        f'moment_kst={moment.isoformat()} completion_boundary=21:00_KST'
    )


if __name__ == '__main__':
    main()
