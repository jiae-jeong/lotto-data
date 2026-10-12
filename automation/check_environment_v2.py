#!/usr/bin/env python3
"""Read-only environment and published-study check, safe on repeated invocation."""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

def main(root):
    if sys.version_info[:2] != (3, 12): raise SystemExit('Python 3.12 required')
    import numpy
    if numpy.__version__ != '2.3.5': raise SystemExit('NumPy 2.3.5 required')
    root = Path(root).resolve()
    prefix = root / 'analysis/2026-10-12/REGIME_DYNAMIC_NESTED_v1'
    with (prefix / 'FINAL_SHA256_MANIFEST.csv').open(encoding='utf-8-sig', newline='') as f:
        manifest = list(csv.DictReader(f))
    if len(manifest) != 23: raise SystemExit('Published manifest count mismatch')
    for row in manifest:
        path = prefix / row['file']
        if path.parent != prefix or not path.is_file(): raise SystemExit('Invalid published file path')
        if path.stat().st_size != int(row['bytes']) or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise SystemExit('Published research integrity failure')
    cp = subprocess.run([sys.executable, '-B', str(root / 'research/expansion_framework_v1/data_quality.py'),
        '--data', str(root / 'analysis/2026-10-12/lotto_data_1_1245_snapshot.csv'), '--through-round', '1245'], cwd=root, capture_output=True, text=True)
    if cp.returncode: print(cp.stderr); raise SystemExit(cp.returncode)
    result = {'environment': 'PASS', 'python': sys.version.split()[0], 'numpy': numpy.__version__,
              'published_content_hashes': 23, 'validated_snapshot_rounds': 1245,
              'snapshot_freshness': 'VERIFIED_REPOSITORY_SNAPSHOT; not a new external source check',
              'check_kind': 'MAINTENANCE/RECHECK', 'new_study_claimed': False}
    print(json.dumps(result)); return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--repository', type=Path, default=Path(__file__).resolve().parents[1])
    raise SystemExit(main(parser.parse_args().repository))
