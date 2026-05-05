"""Local worker shell for Trading Lab jobs.

The worker is deliberately explicit: it runs one bounded job and exits. A real
queue can wrap these commands later without moving backtests into API requests.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trading-lab-worker")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("example-run")
    subparsers.add_parser("fixture-snapshot")
    args = parser.parse_args(argv)

    if args.command == "example-run":
        return _run(
            [
                sys.executable,
                "-m",
                "trading_lab.cli",
                "run",
                "--registry",
                "hypotheses/toy-moving-average-crossover.json",
                "--hypothesis",
                "toy-moving-average-crossover",
                "--data",
                "examples/toy_prices.csv",
                "--json-output",
                "runs/example-run.json",
                "--output",
                "reports/example.md",
            ]
        )
    if args.command == "fixture-snapshot":
        return _run(
            [
                sys.executable,
                "-m",
                "trading_lab.cli",
                "collect-live",
                "--provider",
                "fixture",
                "--symbols",
                "MSFT",
                "AAPL",
                "--max-events",
                "2",
                "--snapshot",
                "runs/live/latest.json",
            ]
        )
    return 2


def _run(command: list[str]) -> int:
    completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
