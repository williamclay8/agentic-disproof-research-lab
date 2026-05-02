"""Artifact-first orchestration for offline disproof runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading_lab.artifacts import ResearchRunArtifact
from trading_lab.backtest import run_moving_average_backtest
from trading_lab.data import build_manifest, load_price_csv
from trading_lab.gates import (
    baseline_comparison_gate,
    chronology_gate,
    choose_verdict,
    cost_grid_robustness_gate,
    cost_realism_gate,
    cost_sensitivity_gate,
    lookahead_column_gate,
    parameter_sensitivity_gate,
    reproducibility_gate,
    schema_gate,
    walk_forward_robustness_gate,
)
from trading_lab.models import BacktestSpec, GateResult, Hypothesis


@dataclass(frozen=True)
class DisproofConfig:
    short_window: int
    long_window: int
    transaction_cost_bps: float = 10
    slippage_bps: float = 5
    execution_delay_bars: int = 1
    stress_transaction_cost_bps: float = 30
    stress_slippage_bps: float = 15
    stress_execution_delay_bars: int = 1
    walk_forward_train_bars: int = 3
    walk_forward_test_bars: int = 1
    walk_forward_step_bars: int = 1


def run_disproof(
    hypothesis: Hypothesis,
    dataset_path: str | Path,
    config: DisproofConfig,
) -> ResearchRunArtifact:
    path = Path(dataset_path)
    rows = load_price_csv(path)
    manifest = build_manifest(path, rows)
    spec = _build_spec(hypothesis, manifest.content_hash, config)
    result = run_moving_average_backtest(rows, spec)

    stressed_spec = BacktestSpec(
        hypothesis_id=hypothesis.id,
        dataset_hash=manifest.content_hash,
        short_window=config.short_window,
        long_window=config.long_window,
        transaction_cost_bps=config.stress_transaction_cost_bps,
        slippage_bps=config.stress_slippage_bps,
        execution_delay_bars=config.stress_execution_delay_bars,
    )
    stressed_result = run_moving_average_backtest(rows, stressed_spec)
    rerun_result = run_moving_average_backtest(rows, spec)

    gate_results = run_gates(
        rows=rows,
        manifest_columns=manifest.columns,
        spec=spec,
        result=result,
        stressed_result=stressed_result,
        rerun_result=rerun_result,
        config=config,
    )

    limitations = [
        "Offline local CSV only; no live data, broker APIs, or order routes were used.",
        "Toy research configuration; robustness gates record evidence gaps.",
    ]
    next_tests = [
        "Record additional offline walk-forward folds.",
        "Record wider parameter and cost grids.",
        "Record stronger comparator families before interpreting the claim.",
    ]

    return ResearchRunArtifact(
        run_id=f"{hypothesis.id}-{manifest.content_hash[:8]}",
        verdict=choose_verdict(gate_results),
        hypothesis=hypothesis,
        manifest=manifest,
        spec=spec,
        result=result,
        gate_results=gate_results,
        limitations=limitations,
        next_tests=next_tests,
    )


def run_gates(
    *,
    rows: list[dict[str, Any]],
    manifest_columns: list[str],
    spec: BacktestSpec,
    result,
    stressed_result,
    rerun_result,
    config: DisproofConfig,
) -> list[GateResult]:
    return [
        schema_gate(manifest_columns),
        chronology_gate(rows),
        lookahead_column_gate(manifest_columns),
        cost_realism_gate(spec, result),
        baseline_comparison_gate(result),
        cost_sensitivity_gate(result, stressed_result),
        reproducibility_gate(result, rerun_result),
        walk_forward_robustness_gate(
            _walk_forward_metrics(rows, spec, config),
            minimum_folds=2,
        ),
        parameter_sensitivity_gate(
            result.metrics.get("strategy_cumulative_return", 0.0),
            _parameter_sweep_metrics(rows, spec),
            minimum_positive_ratio=0.5,
        ),
        cost_grid_robustness_gate(
            _cost_grid_metrics(rows, spec),
            minimum_survival_ratio=0.5,
        ),
    ]


def _build_spec(
    hypothesis: Hypothesis,
    dataset_hash: str,
    config: DisproofConfig,
) -> BacktestSpec:
    return BacktestSpec(
        hypothesis_id=hypothesis.id,
        dataset_hash=dataset_hash,
        short_window=config.short_window,
        long_window=config.long_window,
        transaction_cost_bps=config.transaction_cost_bps,
        slippage_bps=config.slippage_bps,
        execution_delay_bars=config.execution_delay_bars,
    )


def _walk_forward_metrics(
    rows: list[dict[str, Any]],
    spec: BacktestSpec,
    config: DisproofConfig,
) -> list[dict[str, Any]]:
    dates = sorted({row["date"] for row in rows})
    metrics: list[dict[str, Any]] = []
    fold = 1
    start = 0
    while (
        start + config.walk_forward_train_bars + config.walk_forward_test_bars
        <= len(dates)
    ):
        train_dates = dates[start : start + config.walk_forward_train_bars]
        test_dates = dates[
            start
            + config.walk_forward_train_bars : start
            + config.walk_forward_train_bars
            + config.walk_forward_test_bars
        ]
        allowed_dates = set(train_dates + test_dates)
        fold_rows = [row for row in rows if row["date"] in allowed_dates]
        fold_result = run_moving_average_backtest(fold_rows, spec)
        metrics.append(
            {
                "fold": fold,
                "train_start": train_dates[0],
                "train_end": train_dates[-1],
                "test_start": test_dates[0],
                "test_end": test_dates[-1],
                "strategy_cumulative_return": fold_result.metrics[
                    "strategy_cumulative_return"
                ],
                "baseline_cumulative_return": fold_result.metrics[
                    "baseline_cumulative_return"
                ],
            }
        )
        fold += 1
        start += config.walk_forward_step_bars
    return metrics


def _parameter_sweep_metrics(
    rows: list[dict[str, Any]],
    spec: BacktestSpec,
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    short_windows = sorted({max(1, spec.short_window - 1), spec.short_window, spec.short_window + 1})
    long_windows = sorted({spec.long_window, spec.long_window + 1, spec.long_window + 2})
    for short_window in short_windows:
        for long_window in long_windows:
            if long_window <= short_window:
                continue
            cell_spec = BacktestSpec(
                hypothesis_id=spec.hypothesis_id,
                dataset_hash=spec.dataset_hash,
                short_window=short_window,
                long_window=long_window,
                transaction_cost_bps=spec.transaction_cost_bps,
                slippage_bps=spec.slippage_bps,
                execution_delay_bars=spec.execution_delay_bars,
            )
            cell_result = run_moving_average_backtest(rows, cell_spec)
            cells.append(
                {
                    "short_window": short_window,
                    "long_window": long_window,
                    "strategy_cumulative_return": cell_result.metrics[
                        "strategy_cumulative_return"
                    ],
                }
            )
    return cells


def _cost_grid_metrics(
    rows: list[dict[str, Any]],
    spec: BacktestSpec,
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for transaction_cost_bps, slippage_bps, delay in [
        (0, 0, spec.execution_delay_bars),
        (spec.transaction_cost_bps, spec.slippage_bps, spec.execution_delay_bars),
        (30, 15, spec.execution_delay_bars),
        (30, 15, spec.execution_delay_bars + 1),
    ]:
        cell_spec = BacktestSpec(
            hypothesis_id=spec.hypothesis_id,
            dataset_hash=spec.dataset_hash,
            short_window=spec.short_window,
            long_window=spec.long_window,
            transaction_cost_bps=transaction_cost_bps,
            slippage_bps=slippage_bps,
            execution_delay_bars=delay,
        )
        cell_result = run_moving_average_backtest(rows, cell_spec)
        cells.append(
            {
                "transaction_cost_bps": transaction_cost_bps,
                "slippage_bps": slippage_bps,
                "execution_delay_bars": delay,
                "strategy_cumulative_return": cell_result.metrics[
                    "strategy_cumulative_return"
                ],
            }
        )
    return cells
