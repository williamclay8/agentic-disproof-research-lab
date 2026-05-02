"""Deterministic offline moving-average backtest engine."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import asdict
from typing import Any

from trading_lab.metrics import (
    cumulative_return,
    exposure,
    max_drawdown,
    turnover,
)
from trading_lab.models import BacktestResult, BacktestSpec


def run_moving_average_backtest(
    rows: list[dict[str, Any]],
    spec: BacktestSpec,
) -> BacktestResult:
    grouped_rows = _group_rows_by_symbol(rows)
    cost_rate = (spec.transaction_cost_bps + spec.slippage_bps) / 10000.0

    returns: list[float] = []
    positions: list[float] = []
    trades: list[dict[str, Any]] = []
    warnings: list[str] = []
    baseline_returns: list[float] = []
    symbols_with_bars: list[str] = []
    total_cost = 0.0

    for symbol in sorted(grouped_rows):
        symbol_rows = grouped_rows[symbol]
        if len(symbol_rows) < spec.long_window:
            warnings.append(f"{symbol}: insufficient rows for long_window")
            continue

        signals = _moving_average_signals(symbol_rows, spec)
        previous_position = 0.0
        symbol_had_bars = False
        first_usable_index = spec.long_window - 1

        for index in range(first_usable_index, len(symbol_rows)):
            delayed_signal_index = index - spec.execution_delay_bars
            position = (
                signals[delayed_signal_index]
                if delayed_signal_index >= 0
                else 0.0
            )
            position_change = position - previous_position
            cost = cost_rate * abs(position_change)
            close_return = (
                (symbol_rows[index]["close"] / symbol_rows[index - 1]["close"]) - 1.0
                if index > 0
                else 0.0
            )

            returns.append((position * close_return) - cost)
            positions.append(position)
            baseline_returns.append(
                0.0 if index == first_usable_index else close_return
            )
            total_cost += cost
            symbol_had_bars = True

            if position_change != 0:
                trades.append(
                    {
                        "date": symbol_rows[index]["date"],
                        "symbol": symbol,
                        "from_position": previous_position,
                        "to_position": position,
                        "position_change": position_change,
                        "cost": cost,
                    }
                )

            previous_position = position

        if symbol_had_bars:
            symbols_with_bars.append(symbol)

    metrics = {
        "strategy_cumulative_return": cumulative_return(returns),
        "baseline_cumulative_return": cumulative_return(baseline_returns),
        "max_drawdown": max_drawdown(returns),
        "turnover": turnover(positions),
        "average_exposure": exposure(positions),
        "total_cost": total_cost,
        "bars": len(returns),
        "symbols": symbols_with_bars,
    }

    return BacktestResult(
        metrics=metrics,
        trades=trades,
        returns=returns,
        positions=positions,
        warnings=warnings,
        fingerprint=_fingerprint(rows, spec),
    )


def _group_rows_by_symbol(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["symbol"]].append(row)

    return {
        symbol: sorted(symbol_rows, key=lambda row: row["date"])
        for symbol, symbol_rows in grouped.items()
    }


def _moving_average_signals(
    rows: list[dict[str, Any]],
    spec: BacktestSpec,
) -> list[float]:
    signals: list[float] = []
    closes = [row["close"] for row in rows]

    for index in range(len(rows)):
        if index + 1 < spec.long_window:
            signals.append(0.0)
            continue

        short_average = _mean(closes[index + 1 - spec.short_window : index + 1])
        long_average = _mean(closes[index + 1 - spec.long_window : index + 1])
        signals.append(1.0 if short_average > long_average else 0.0)

    return signals


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _fingerprint(rows: list[dict[str, Any]], spec: BacktestSpec) -> str:
    payload = {
        "spec": asdict(spec),
        "rows": sorted(
            rows,
            key=lambda row: (
                row.get("symbol", ""),
                row.get("date", ""),
                row.get("open", 0.0),
                row.get("high", 0.0),
                row.get("low", 0.0),
                row.get("close", 0.0),
                row.get("volume", 0.0),
            ),
        ),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
