#!/usr/bin/env python3
"""Run the generic daily engine with attempt-safe completion discovery."""
from __future__ import annotations

import argparse
from pathlib import Path

import daily_research_queue_preflight_v1 as preflight
import daily_research_v2 as daily


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output-root', type=Path)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--result-file', type=Path)
    parser.add_argument('--run-date')
    parser.add_argument('--min-successful-studies', type=int, default=2)
    parser.add_argument('--max-successful-studies', type=int, default=3)
    parser.add_argument('--required-empirical-studies', type=int, default=1)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()

    # The generic engine still uses its original strict validator for runnable work. Only completion
    # discovery is replaced so failed `.attempts` can never masquerade as immutable completions.
    daily.completed_tasks = preflight.verified_completed_tasks
    output_root = args.output_root or args.repository / 'analysis'
    output_root.mkdir(parents=True, exist_ok=True)
    return daily.run(
        args.repository, output_root, args.queue, args.result_file, args.run_date,
        args.min_successful_studies, args.max_successful_studies,
        args.required_empirical_studies, args.archive,
    )


if __name__ == '__main__':
    raise SystemExit(main())
