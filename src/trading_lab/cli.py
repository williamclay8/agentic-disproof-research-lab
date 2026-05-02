"""Command-line examples for local-only trading research reports."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
import sys
from typing import Sequence

from trading_lab.artifacts import (
    ResearchRunArtifact,
    read_run_artifact,
    write_run_artifact,
)
from trading_lab.dashboard import render_dashboard_html, render_snapshot_dashboard_html
from trading_lab.datahub import DataHub
from trading_lab.example import build_example_run
from trading_lab.gates import choose_verdict
from trading_lab.live_runtime import collect_live_data
from trading_lab.providers import FixtureProvider, KrakenTickerProvider, NullProvider
from trading_lab.registry import load_hypothesis
from trading_lab.reports import render_markdown_report
from trading_lab.runner import DisproofConfig, run_disproof
from trading_lab.snapshots import SnapshotStore, read_latest
from trading_lab.terminal import parse_terminal_input


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "run-example":
        return _run_example(args.output, args.json_output)
    if args.command == "run":
        return _run_registered(
            registry_path=args.registry,
            hypothesis_id=args.hypothesis,
            dataset_path=args.data,
            output_path=args.output,
            json_output_path=args.json_output,
        )
    if args.command == "dashboard":
        return _dashboard(args.output, args.runs)
    if args.command == "terminal":
        return _terminal(args.input)
    if args.command == "collect-live":
        return _collect_live(
            provider_name=args.provider,
            symbols=args.symbols,
            max_events=args.max_events,
            snapshot_path=args.snapshot,
        )
    if args.command == "snapshot-dashboard":
        return _snapshot_dashboard(args.snapshot, args.output)

    parser.error("missing command")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_lab",
        description="Local-only educational trading research examples.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_example = subparsers.add_parser(
        "run-example",
        help="Run the bundled toy moving-average crossover example.",
    )
    run_example.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path where the markdown report should be written.",
    )
    run_example.add_argument(
        "--json-output",
        type=Path,
        help="Optional path where the structured run artifact should be written.",
    )

    run = subparsers.add_parser(
        "run",
        help="Run a pre-registered local hypothesis into a JSON evidence artifact.",
    )
    run.add_argument("--registry", required=True, type=Path)
    run.add_argument("--hypothesis", required=True)
    run.add_argument("--data", required=True, type=Path)
    run.add_argument("--json-output", required=True, type=Path)
    run.add_argument("--output", type=Path)

    dashboard = subparsers.add_parser(
        "dashboard",
        help="Write a static HTML falsification dashboard for the bundled example.",
    )
    dashboard.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path where the HTML dashboard should be written.",
    )
    dashboard.add_argument(
        "--run",
        action="append",
        default=[],
        dest="runs",
        type=Path,
        help="Structured run artifact to include in the comparator.",
    )

    terminal = subparsers.add_parser(
        "terminal",
        help="Parse an offline terminal command or ticker-like research focus.",
    )
    terminal.add_argument("input", nargs="+")

    collect_live = subparsers.add_parser(
        "collect-live",
        help="Collect bounded research-only market observations into a local snapshot.",
    )
    collect_live.add_argument(
        "--provider",
        choices=("fixture", "kraken-public-rest", "null"),
        default="fixture",
    )
    collect_live.add_argument("--symbols", nargs="+", required=True)
    collect_live.add_argument("--max-events", type=int, default=10)
    collect_live.add_argument("--snapshot", required=True, type=Path)

    snapshot_dashboard = subparsers.add_parser(
        "snapshot-dashboard",
        help="Render a static dashboard from a local market observation snapshot.",
    )
    snapshot_dashboard.add_argument("--snapshot", required=True, type=Path)
    snapshot_dashboard.add_argument("--output", required=True, type=Path)

    return parser


def _run_example(output_path: Path, json_output_path: Path | None = None) -> int:
    run = build_example_run()
    verdict = choose_verdict(run.gate_results)

    markdown = render_markdown_report(
        hypothesis=run.hypothesis,
        manifest=run.manifest,
        spec=run.spec,
        result=run.result,
        gate_results=run.gate_results,
        limitations=run.limitations,
        next_tests=run.next_tests,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Verdict: {verdict}")

    if json_output_path is not None:
        write_run_artifact(json_output_path, _artifact_from_example_run(run))
        print(f"JSON: {json_output_path}")

    return 0


def _dashboard(output_path: Path, run_paths: list[Path]) -> int:
    artifacts = [read_run_artifact(path) for path in run_paths]
    if artifacts:
        primary = artifacts[0]
        hypothesis = primary.hypothesis
        manifest = primary.manifest
        spec = primary.spec
        result = primary.result
        gate_results = primary.gate_results
        limitations = primary.limitations
        next_tests = primary.next_tests
    else:
        run = build_example_run()
        hypothesis = run.hypothesis
        manifest = run.manifest
        spec = run.spec
        result = run.result
        gate_results = run.gate_results
        limitations = run.limitations
        next_tests = run.next_tests
    html = render_dashboard_html(
        hypothesis=hypothesis,
        manifest=manifest,
        spec=spec,
        result=result,
        gate_results=gate_results,
        limitations=limitations,
        next_tests=next_tests,
        run_artifacts=artifacts,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Dashboard: {output_path}")
    return 0


def _run_registered(
    *,
    registry_path: Path,
    hypothesis_id: str,
    dataset_path: Path,
    output_path: Path | None,
    json_output_path: Path,
) -> int:
    hypothesis = load_hypothesis(registry_path)
    if hypothesis.id != hypothesis_id:
        raise ValueError(f"unknown hypothesis id: {hypothesis_id}")

    artifact = run_disproof(
        hypothesis=hypothesis,
        dataset_path=dataset_path,
        config=DisproofConfig(short_window=2, long_window=3),
    )
    write_run_artifact(json_output_path, artifact)
    print(f"Verdict: {artifact.verdict}")
    print(f"JSON: {json_output_path}")

    if output_path is not None:
        markdown = render_markdown_report(
            hypothesis=artifact.hypothesis,
            manifest=artifact.manifest,
            spec=artifact.spec,
            result=artifact.result,
            gate_results=artifact.gate_results,
            limitations=artifact.limitations,
            next_tests=artifact.next_tests,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Report: {output_path}")

    return 0


def _terminal(parts: list[str]) -> int:
    parsed = parse_terminal_input(" ".join(parts))
    print(parsed.message)
    return 0 if parsed.kind != "unknown" else 2


def _collect_live(
    *,
    provider_name: str,
    symbols: list[str],
    max_events: int,
    snapshot_path: Path,
) -> int:
    if _live_collection_disabled():
        print(
            "collect-live disabled by safety switch. "
            "Unset TRADING_LAB_DISABLE_NETWORK/TRADING_LAB_DISABLE_REALTIME to collect observations.",
            file=sys.stderr,
        )
        return 2

    provider = _build_live_provider(provider_name, symbols)
    hub = DataHub()
    store = SnapshotStore(snapshot_path.parent, latest_name=snapshot_path.name)
    result = asyncio.run(
        collect_live_data(
            provider,
            hub,
            max_events=max_events,
            snapshot_store=store,
        )
    )
    print(
        f"Collected {result.events_collected} research data events from {result.provider}. "
        "No broker or execution actions are available."
    )
    print(f"Snapshot: {snapshot_path}")
    return 0


def _live_collection_disabled() -> bool:
    return os.environ.get("TRADING_LAB_DISABLE_NETWORK") == "1" or os.environ.get(
        "TRADING_LAB_DISABLE_REALTIME"
    ) == "1"


def _snapshot_dashboard(snapshot_path: Path, output_path: Path) -> int:
    snapshot = read_latest(snapshot_path)
    if snapshot is None:
        raise ValueError(f"snapshot not found: {snapshot_path}")
    html = render_snapshot_dashboard_html(snapshot)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Snapshot dashboard: {output_path}")
    return 0


def _build_live_provider(provider_name: str, symbols: list[str]):
    if provider_name == "null":
        return NullProvider()
    if provider_name == "kraken-public-rest":
        return KrakenTickerProvider(symbols=symbols)

    fixture_path = Path(__file__).resolve().parents[2] / "examples" / "live_fixture_quotes.jsonl"
    return _SymbolFilterProvider(FixtureProvider(fixture_path), symbols)


class _SymbolFilterProvider:
    def __init__(self, provider, symbols: list[str]) -> None:
        self.provider = provider
        self.symbols = {symbol.upper() for symbol in symbols}
        self.name = provider.name

    def stream(self):
        for envelope in self.provider.stream():
            if str(envelope.symbol).upper() in self.symbols:
                yield envelope


def _artifact_from_example_run(run) -> ResearchRunArtifact:
    return ResearchRunArtifact(
        run_id=run.hypothesis.id,
        verdict=choose_verdict(run.gate_results),
        hypothesis=run.hypothesis,
        manifest=run.manifest,
        spec=run.spec,
        result=run.result,
        gate_results=run.gate_results,
        limitations=run.limitations,
        next_tests=run.next_tests,
    )


if __name__ == "__main__":
    raise SystemExit(main())
