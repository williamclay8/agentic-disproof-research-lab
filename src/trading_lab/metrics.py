"""Offline performance metrics for deterministic backtests."""

from __future__ import annotations


def cumulative_return(returns: list[float]) -> float:
    equity = 1.0
    for period_return in returns:
        equity *= 1.0 + period_return
    return equity - 1.0


def max_drawdown(returns: list[float]) -> float:
    equity = 1.0
    peak = 1.0
    largest_drawdown = 0.0

    for period_return in returns:
        equity *= 1.0 + period_return
        peak = max(peak, equity)
        if peak:
            largest_drawdown = max(largest_drawdown, (peak - equity) / peak)

    return largest_drawdown


def turnover(positions: list[float]) -> float:
    if not positions:
        return 0.0

    previous_position = 0.0
    total_change = 0.0
    for position in positions:
        total_change += abs(position - previous_position)
        previous_position = position

    return total_change / len(positions)


def exposure(positions: list[float]) -> float:
    if not positions:
        return 0.0

    return sum(abs(position) for position in positions) / len(positions)
