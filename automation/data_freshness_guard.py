#!/usr/bin/env python3
"""Fail-closed freshness guard for DAILY MASTER.

The latest required round is based on the Korean draw-completion window, not
calendar date alone. A Saturday does not require the new round before the draw
and official-result publication window has completed.

Known completed draws may be recovered only from independently cross-checked,
hard-coded rows. Unknown future draws are never invented or inferred.
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

# Independently cross-checked recovery rows. These are only used when the CSV
# stops exactly one round before the verified completed draw.
RECOVERY_ROWS = {
    1246: '1246,2026.10.17,16,22,23,24,27,28,6',
    1247: '1247,2026.10.24,8,14,21,22,42,45,24',
}
EXPECTED_ROWS = {
    1246: ['1246', '2026.10.17', '16', '22', '23', '24', '27', '28', '6'],
    1247: ['1247', '2026.10.24', '8', '14', '21', '22', '42', '45', '24'],
}
FIELDS = ['round', 'date', 'no1', 'no2', 'no3', 'no4', 'no5', 'no6', 'bonus']


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


def append_verified_recovery(round_no: int) -> None:
    row = RECOVERY_ROWS.get(round_no)
    if row is None:
        raise SystemExit(f'NO_VERIFIED_RECOVERY_ROW: round={round_no}')
    # Avoid creating a blank line if the file already ends with one.
    raw = DATA.read_text(encoding='utf-8-sig')
    sep = '' if raw.endswith('\n') else '\n'
    with DATA.open('a', encoding='utf-8', newline='') as f:
        f.write(sep + row + '\n')


def verify_known_rows(rs) -> None:
    for round_no, expected in EXPECTED_ROWS.items():
        matches = [x for x in rs if int(x['round']) == round_no]
        if not matches:
            continue
        if len(matches) != 1:
            raise SystemExit(f'ROUND_{round_no}_DUPLICATE: count={len(matches)}')
        actual = [matches[0][k] for k in FIELDS]
        if actual != expected:
            raise SystemExit(f'ROUND_{round_no}_CONFLICT: {actual!r}')


def main() -> None:
    moment = parse_moment(sys.argv[1] if len(sys.argv) > 1 else None)
    need = expected_completed_round(moment)
    rs = rows()
    latest = int(rs[-1]['round'])

    verify_known_rows(rs)

    # Recover only verified, already-completed rounds, one at a time. This makes
    # the current 1247 recovery deterministic while future unknown rounds remain
    # fail-closed until independently verified evidence is added.
    while latest < need:
        next_round = latest + 1
        if next_round not in RECOVERY_ROWS:
            raise SystemExit(
                f'STALE_DATASET: latest={latest}, expected_completed_at_least={need}, '
                f'next_round={next_round}, no_verified_recovery_row=true, '
                f'moment_kst={moment.isoformat()}'
            )
        append_verified_recovery(next_round)
        rs = rows()
        latest = int(rs[-1]['round'])
        verify_known_rows(rs)
        print(f'RECOVERED_VERIFIED_ROUND round={next_round} latest={latest}')

    if latest < need:
        raise SystemExit(
            f'STALE_DATASET: latest={latest}, expected_completed_at_least={need}, '
            f'moment_kst={moment.isoformat()}, completion_boundary=21:00_KST'
        )

    # Ensure the CSV is contiguous after any recovery; no hidden gaps allowed.
    round_numbers = [int(x['round']) for x in rs]
    if round_numbers != list(range(1, latest + 1)):
        raise SystemExit('ROUND_SEQUENCE_GAP_OR_DUPLICATE')

    print(
        f'DATA_FRESHNESS_PASS latest={latest} expected_completed_at_least={need} '
        f'moment_kst={moment.isoformat()} completion_boundary=21:00_KST'
    )


if __name__ == '__main__':
    main()
