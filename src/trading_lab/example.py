"""Bundled local-only example research run."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from trading_lab.models import (
    BacktestResult,
    BacktestSpec,
    DatasetManifest,
    GateResult,
    Hypothesis,
)
from trading_lab.runner import DisproofConfig, run_disproof


@dataclass(frozen=True)
class ExampleRun:
    hypothesis: Hypothesis
    manifest: DatasetManifest
    spec: BacktestSpec
    result: BacktestResult
    gate_results: list[GateResult]
    limitations: list[str]
    next_tests: list[str]


def build_example_run() -> ExampleRun:
    hypothesis = build_example_hypothesis()
    artifact = run_disproof(
        hypothesis=hypothesis,
        dataset_path=resolve_toy_prices_path(),
        config=DisproofConfig(short_window=2, long_window=3),
    )

    return ExampleRun(
        hypothesis=artifact.hypothesis,
        manifest=artifact.manifest,
        spec=artifact.spec,
        result=artifact.result,
        gate_results=artifact.gate_results,
        limitations=artifact.limitations,
        next_tests=artifact.next_tests,
    )


def resolve_toy_prices_path() -> Path:
    candidates = [
        Path.cwd() / "examples" / "toy_prices.csv",
        Path(__file__).resolve().parents[2] / "examples" / "toy_prices.csv",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError("could not find examples/toy_prices.csv")


def build_example_hypothesis() -> Hypothesis:
    return Hypothesis(
        id="toy-moving-average-crossover",
        thesis=(
            "A toy moving-average crossover may outperform a buy-and-hold "
            "baseline on the bundled offline sample."
        ),
        null_hypothesis=(
            "The toy moving-average crossover has no edge after costs, "
            "slippage, and one-bar execution delay."
        ),
        asset_universe=["AAA", "BBB"],
        time_horizon="daily bars over a tiny educational sample",
        signal_definition=(
            "Long when the 2-bar moving average is above the 3-bar moving "
            "average; flat otherwise."
        ),
        expected_failure_modes=[
            "lookahead leakage",
            "cost sensitivity",
            "failure to beat buy-and-hold baseline",
            "non-reproducible run outputs",
        ],
        falsification_tests=[
            "lookahead column scan",
            "explicit cost realism check",
            "baseline comparison",
            "higher-cost stress run",
            "deterministic rerun fingerprint check",
        ],
        pre_registered_metrics=[
            "strategy_cumulative_return",
            "baseline_cumulative_return",
            "max_drawdown",
            "turnover",
            "total_cost",
        ],
        acceptance_thresholds={
            "baseline_comparison": "strategy_cumulative_return > baseline",
            "cost_sensitivity": "stressed return remains positive",
            "reproducibility": "rerun fingerprints match",
        },
        data_requirements=[
            "local CSV only",
            "date, symbol, OHLCV columns",
            "rows sorted by date then symbol",
        ],
        posthoc_edit_policy=(
            "Do not change the hypothesis or thresholds after observing results."
        ),
    )
