"""Falsification gates for offline trading research artifacts."""

from __future__ import annotations

from typing import Any

from trading_lab.models import BacktestResult, BacktestSpec, GateResult, ReportVerdict


REQUIRED_PRICE_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume"]


def schema_gate(columns: list[str]) -> GateResult:
    missing_columns = [
        column for column in REQUIRED_PRICE_COLUMNS if column not in columns
    ]

    if missing_columns:
        return GateResult(
            gate_name="schema columns",
            status="fail",
            evidence={
                "required_columns": REQUIRED_PRICE_COLUMNS,
                "observed_columns": columns,
                "missing_columns": missing_columns,
            },
            threshold="all required OHLCV columns are present",
            remediation_hint="Missing local CSV columns recorded.",
            severity="critical",
        )

    return GateResult(
        gate_name="schema columns",
        status="pass",
        evidence={
            "required_columns": REQUIRED_PRICE_COLUMNS,
            "observed_columns": columns,
            "missing_columns": [],
        },
        threshold="all required OHLCV columns are present",
        remediation_hint="No evidence gap recorded.",
        severity="info",
    )


def chronology_gate(rows: list[dict[str, Any]]) -> GateResult:
    previous_key: tuple[str, str] | None = None
    seen_keys: set[tuple[str, str]] = set()

    for row in rows:
        key = (row["date"], row["symbol"])
        if key in seen_keys:
            return GateResult(
                gate_name="chronology",
                status="fail",
                evidence={"duplicate_key": key},
                threshold="rows are unique by date and symbol",
                remediation_hint="Duplicate date/symbol rows recorded.",
                severity="critical",
            )
        if previous_key is not None and key < previous_key:
            return GateResult(
                gate_name="chronology",
                status="fail",
                evidence={"previous_key": previous_key, "current_key": key},
                threshold="rows are sorted by date then symbol",
                remediation_hint="Out-of-order local CSV rows recorded.",
                severity="critical",
            )
        seen_keys.add(key)
        previous_key = key

    return GateResult(
        gate_name="chronology",
        status="pass",
        evidence={"rows_checked": len(rows)},
        threshold="rows are sorted and unique by date and symbol",
        remediation_hint="No evidence gap recorded.",
        severity="info",
    )


def lookahead_column_gate(columns: list[str]) -> GateResult:
    forbidden_terms = ("future", "target", "forward")
    flagged_columns = [
        column
        for column in columns
        if any(term in column.lower() for term in forbidden_terms)
    ]

    if flagged_columns:
        return GateResult(
            gate_name="lookahead columns",
            status="fail",
            evidence={"flagged_columns": flagged_columns},
            threshold="no lowercase column name contains future, target, or forward",
            remediation_hint="Forward-looking column labels recorded.",
            severity="critical",
        )

    return GateResult(
        gate_name="lookahead columns",
        status="pass",
        evidence={"checked_columns": columns},
        threshold="no lowercase column name contains future, target, or forward",
        remediation_hint="No evidence gap recorded.",
        severity="info",
    )


def cost_realism_gate(spec: BacktestSpec, result: BacktestResult) -> GateResult:
    total_bps = spec.transaction_cost_bps + spec.slippage_bps
    total_cost = result.metrics.get("total_cost")
    evidence = {
        "transaction_cost_bps": spec.transaction_cost_bps,
        "slippage_bps": spec.slippage_bps,
        "total_cost": total_cost,
    }

    if total_bps <= 0 or "total_cost" not in result.metrics:
        return GateResult(
            gate_name="cost realism",
            status="fail",
            evidence=evidence,
            threshold="transaction_cost_bps + slippage_bps > 0 and total_cost present",
            remediation_hint="Missing explicit cost evidence recorded.",
            severity="critical",
        )

    return GateResult(
        gate_name="cost realism",
        status="pass",
        evidence=evidence,
        threshold="transaction_cost_bps + slippage_bps > 0 and total_cost present",
        remediation_hint="No evidence gap recorded.",
        severity="info",
    )


def baseline_comparison_gate(result: BacktestResult) -> GateResult:
    missing_metrics = _missing_metrics(
        result,
        ["strategy_cumulative_return", "baseline_cumulative_return"],
    )
    if missing_metrics:
        return GateResult(
            gate_name="baseline comparison",
            status="fail",
            evidence={"missing_metrics": missing_metrics},
            threshold="strategy and baseline cumulative return metrics are present",
            remediation_hint="Missing strategy or comparator metric recorded.",
            severity="critical",
        )

    strategy_return = _metric(result, "strategy_cumulative_return")
    baseline_return = _metric(result, "baseline_cumulative_return")
    evidence = {
        "strategy_cumulative_return": strategy_return,
        "baseline_cumulative_return": baseline_return,
    }

    if strategy_return <= baseline_return:
        return GateResult(
            gate_name="baseline comparison",
            status="warn",
            evidence=evidence,
            threshold="strategy_cumulative_return > baseline_cumulative_return",
            remediation_hint="Comparator evidence weakened the claim.",
            severity="warning",
        )

    return GateResult(
        gate_name="baseline comparison",
        status="pass",
        evidence=evidence,
        threshold="strategy_cumulative_return > baseline_cumulative_return",
        remediation_hint="No evidence gap recorded.",
        severity="info",
    )


def cost_sensitivity_gate(
    result: BacktestResult,
    stressed_result: BacktestResult,
) -> GateResult:
    missing_metrics = []
    if "strategy_cumulative_return" not in result.metrics:
        missing_metrics.append("original_strategy_cumulative_return")
    if "strategy_cumulative_return" not in stressed_result.metrics:
        missing_metrics.append("stressed_strategy_cumulative_return")
    if missing_metrics:
        return GateResult(
            gate_name="cost sensitivity",
            status="fail",
            evidence={"missing_metrics": missing_metrics},
            threshold="original and stressed strategy cumulative return metrics are present",
            remediation_hint="Missing original or stressed return evidence recorded.",
            severity="critical",
        )

    original_return = _metric(result, "strategy_cumulative_return")
    stressed_return = _metric(stressed_result, "strategy_cumulative_return")
    deterioration = original_return - stressed_return
    evidence = {
        "original_strategy_cumulative_return": original_return,
        "stressed_strategy_cumulative_return": stressed_return,
        "deterioration": deterioration,
    }

    if stressed_return <= 0 or deterioration > (original_return * 0.5):
        return GateResult(
            gate_name="cost sensitivity",
            status="warn",
            evidence=evidence,
            threshold=(
                "stressed strategy_cumulative_return > 0 and deterioration <= 50%"
            ),
            remediation_hint="Cost stress fragility recorded.",
            severity="warning",
        )

    return GateResult(
        gate_name="cost sensitivity",
        status="pass",
        evidence=evidence,
        threshold="stressed strategy_cumulative_return > 0 and deterioration <= 50%",
        remediation_hint="No evidence gap recorded.",
        severity="info",
    )


def reproducibility_gate(first: BacktestResult, second: BacktestResult) -> GateResult:
    evidence = {
        "first_fingerprint": first.fingerprint,
        "second_fingerprint": second.fingerprint,
    }

    if first.fingerprint != second.fingerprint:
        return GateResult(
            gate_name="reproducibility",
            status="fail",
            evidence=evidence,
            threshold="backtest fingerprints match",
            remediation_hint="Fingerprint mismatch recorded.",
            severity="critical",
        )

    return GateResult(
        gate_name="reproducibility",
        status="pass",
        evidence=evidence,
        threshold="backtest fingerprints match",
        remediation_hint="No evidence gap recorded.",
        severity="info",
    )


def walk_forward_robustness_gate(
    fold_metrics: list[dict[str, Any]],
    *,
    minimum_folds: int = 3,
    minimum_pass_ratio: float = 0.6,
) -> GateResult:
    missing = [
        fold.get("fold")
        for fold in fold_metrics
        if "strategy_cumulative_return" not in fold
        or "baseline_cumulative_return" not in fold
    ]
    if len(fold_metrics) < minimum_folds or missing:
        return GateResult(
            gate_name="walk-forward robustness",
            status="fail",
            evidence={
                "folds": len(fold_metrics),
                "minimum_folds": minimum_folds,
                "missing_metric_folds": missing,
            },
            threshold="walk-forward folds include required comparator metrics",
            remediation_hint="Record complete fold evidence before interpreting robustness.",
            severity="critical",
        )

    passing_folds = sum(
        1
        for fold in fold_metrics
        if fold["strategy_cumulative_return"]
        > fold["baseline_cumulative_return"]
    )
    pass_ratio = passing_folds / len(fold_metrics)
    strategy_returns = [fold["strategy_cumulative_return"] for fold in fold_metrics]
    baseline_returns = [fold["baseline_cumulative_return"] for fold in fold_metrics]
    evidence = {
        "folds": len(fold_metrics),
        "passing_folds": passing_folds,
        "pass_ratio": pass_ratio,
        "median_strategy_cumulative_return": _median(strategy_returns),
        "median_baseline_cumulative_return": _median(baseline_returns),
        "worst_fold_strategy_cumulative_return": min(strategy_returns),
        "fold_metrics": fold_metrics,
    }

    if (
        pass_ratio < minimum_pass_ratio
        or evidence["median_strategy_cumulative_return"]
        <= evidence["median_baseline_cumulative_return"]
    ):
        return GateResult(
            gate_name="walk-forward robustness",
            status="warn",
            evidence=evidence,
            threshold="majority of folds beat the comparator on the same offline bars",
            remediation_hint="Record more fold evidence or mark the claim as fold-fragile.",
            severity="warning",
        )

    return GateResult(
        gate_name="walk-forward robustness",
        status="pass",
        evidence=evidence,
        threshold="majority of folds beat the comparator on the same offline bars",
        remediation_hint="No evidence gap recorded.",
        severity="info",
    )


def parameter_sensitivity_gate(
    selected_return: float,
    neighborhood_results: list[dict[str, Any]],
    *,
    minimum_positive_ratio: float = 0.6,
) -> GateResult:
    missing = [
        (cell.get("short_window"), cell.get("long_window"))
        for cell in neighborhood_results
        if "strategy_cumulative_return" not in cell
    ]
    if len(neighborhood_results) < 2 or missing:
        return GateResult(
            gate_name="parameter sensitivity",
            status="fail",
            evidence={
                "cells": len(neighborhood_results),
                "missing_metric_cells": missing,
            },
            threshold="parameter sweep cells include strategy cumulative return",
            remediation_hint="Record complete parameter sweep evidence.",
            severity="critical",
        )

    returns = [cell["strategy_cumulative_return"] for cell in neighborhood_results]
    positive_cells = sum(1 for value in returns if value > 0)
    positive_ratio = positive_cells / len(returns)
    selected_is_isolated_peak = (
        selected_return == max(returns)
        and sum(1 for value in returns if value > 0) == 1
    )
    evidence = {
        "cells": neighborhood_results,
        "selected_strategy_cumulative_return": selected_return,
        "positive_cells": positive_cells,
        "positive_ratio": positive_ratio,
        "median_strategy_cumulative_return": _median(returns),
        "selected_is_isolated_peak": selected_is_isolated_peak,
    }

    if positive_ratio < minimum_positive_ratio or selected_is_isolated_peak:
        return GateResult(
            gate_name="parameter sensitivity",
            status="warn",
            evidence=evidence,
            threshold="nearby parameter cells show broad non-negative evidence",
            remediation_hint="Record the claim as parameter-fragile.",
            severity="warning",
        )

    return GateResult(
        gate_name="parameter sensitivity",
        status="pass",
        evidence=evidence,
        threshold="nearby parameter cells show broad non-negative evidence",
        remediation_hint="No evidence gap recorded.",
        severity="info",
    )


def cost_grid_robustness_gate(
    grid_results: list[dict[str, Any]],
    *,
    minimum_survival_ratio: float = 0.5,
) -> GateResult:
    missing = [
        index
        for index, cell in enumerate(grid_results)
        if "strategy_cumulative_return" not in cell
    ]
    if len(grid_results) < 2 or missing:
        return GateResult(
            gate_name="cost grid robustness",
            status="fail",
            evidence={"cells": len(grid_results), "missing_metric_cells": missing},
            threshold="cost grid cells include strategy cumulative return",
            remediation_hint="Record complete cost grid evidence.",
            severity="critical",
        )

    surviving_cells = sum(
        1 for cell in grid_results if cell["strategy_cumulative_return"] > 0
    )
    survival_ratio = surviving_cells / len(grid_results)
    returns = [cell["strategy_cumulative_return"] for cell in grid_results]
    evidence = {
        "cells": grid_results,
        "surviving_cells": surviving_cells,
        "survival_ratio": survival_ratio,
        "worst_strategy_cumulative_return": min(returns),
        "highest_cost_strategy_cumulative_return": returns[-1],
    }

    if survival_ratio < minimum_survival_ratio or returns[-1] <= 0:
        return GateResult(
            gate_name="cost grid robustness",
            status="warn",
            evidence=evidence,
            threshold="returns remain positive across at least half of cost grid cells",
            remediation_hint="Record the claim as cost-fragile across the grid.",
            severity="warning",
        )

    return GateResult(
        gate_name="cost grid robustness",
        status="pass",
        evidence=evidence,
        threshold="returns remain positive across at least half of cost grid cells",
        remediation_hint="No evidence gap recorded.",
        severity="info",
    )


def choose_verdict(gates: list[GateResult]) -> ReportVerdict:
    if any(gate.status == "fail" and gate.severity == "critical" for gate in gates):
        return "rejected"
    if any(gate.status in ("warn", "fail") for gate in gates):
        return "inconclusive"
    return "passed preliminary gates"


def _metric(result: BacktestResult, name: str) -> Any:
    return result.metrics.get(name, 0.0)


def _missing_metrics(result: BacktestResult, names: list[str]) -> list[str]:
    return [name for name in names if name not in result.metrics]


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2
