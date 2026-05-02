import pytest

from trading_lab.backtest import run_moving_average_backtest
from trading_lab.models import BacktestResult, BacktestSpec


def spec(**overrides):
    values = {
        "hypothesis_id": "hyp-ma",
        "dataset_hash": "dataset-123",
        "short_window": 2,
        "long_window": 3,
        "transaction_cost_bps": 10.0,
        "slippage_bps": 5.0,
        "execution_delay_bars": 1,
    }
    values.update(overrides)
    return BacktestSpec(**values)


def row(date, symbol, close):
    return {
        "date": date,
        "symbol": symbol,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": 1000.0,
    }


def test_moving_average_backtest_applies_delay_costs_and_baseline_metrics():
    rows = [
        row("2024-01-01", "AAA", 10.0),
        row("2024-01-02", "AAA", 11.0),
        row("2024-01-03", "AAA", 12.0),
        row("2024-01-04", "AAA", 13.0),
        row("2024-01-05", "AAA", 12.0),
        row("2024-01-06", "AAA", 11.0),
    ]

    result = run_moving_average_backtest(rows, spec())

    assert isinstance(result, BacktestResult)
    assert result.positions == [0.0, 1.0, 1.0, 1.0]
    assert result.returns == pytest.approx(
        [
            0.0,
            (13.0 / 12.0) - 1 - 0.0015,
            (12.0 / 13.0) - 1,
            (11.0 / 12.0) - 1,
        ]
    )
    assert result.trades == [
        {
            "date": "2024-01-04",
            "symbol": "AAA",
            "from_position": 0.0,
            "to_position": 1.0,
            "position_change": 1.0,
            "cost": pytest.approx(0.0015),
        }
    ]
    expected_strategy_cumulative_return = 1.0
    for value in result.returns:
        expected_strategy_cumulative_return *= 1 + value
    expected_strategy_cumulative_return -= 1
    assert result.metrics["strategy_cumulative_return"] == pytest.approx(
        expected_strategy_cumulative_return
    )
    assert result.metrics["baseline_cumulative_return"] == pytest.approx((11.0 / 12.0) - 1)
    assert result.metrics["max_drawdown"] > 0
    assert result.metrics["turnover"] == pytest.approx(0.25)
    assert result.metrics["average_exposure"] == pytest.approx(0.75)
    assert result.metrics["total_cost"] == pytest.approx(0.0015)
    assert result.metrics["bars"] == 4
    assert result.metrics["symbols"] == ["AAA"]
    assert result.warnings == []
    assert result.fingerprint


def test_backtest_groups_by_symbol_and_fingerprint_is_deterministic():
    rows = [
        row("2024-01-01", "AAA", 10.0),
        row("2024-01-01", "BBB", 20.0),
        row("2024-01-02", "AAA", 11.0),
        row("2024-01-02", "BBB", 19.0),
        row("2024-01-03", "AAA", 12.0),
        row("2024-01-03", "BBB", 18.0),
        row("2024-01-04", "AAA", 13.0),
        row("2024-01-04", "BBB", 17.0),
        row("2024-01-05", "AAA", 14.0),
        row("2024-01-05", "BBB", 16.0),
    ]

    result = run_moving_average_backtest(rows, spec(transaction_cost_bps=0.0, slippage_bps=0.0))
    same_result = run_moving_average_backtest(
        list(reversed(rows)),
        spec(transaction_cost_bps=0.0, slippage_bps=0.0),
    )

    assert result.metrics["symbols"] == ["AAA", "BBB"]
    assert result.metrics["bars"] == 6
    assert len(result.returns) == 6
    assert len(result.positions) == 6
    assert result.fingerprint == same_result.fingerprint


def test_backtest_warns_and_skips_symbols_without_usable_rows():
    rows = [
        row("2024-01-01", "AAA", 10.0),
        row("2024-01-02", "AAA", 11.0),
    ]

    result = run_moving_average_backtest(rows, spec(long_window=3, short_window=1))

    assert result.metrics["bars"] == 0
    assert result.returns == []
    assert result.positions == []
    assert result.warnings == ["AAA: insufficient rows for long_window"]
