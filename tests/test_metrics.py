import pytest

from trading_lab.metrics import (
    cumulative_return,
    exposure,
    max_drawdown,
    turnover,
)


def test_cumulative_return_compounds_period_returns():
    assert cumulative_return([0.1, -0.05]) == pytest.approx((1.1 * 0.95) - 1)


def test_max_drawdown_reports_largest_peak_to_trough_loss():
    assert max_drawdown([0.1, -0.2, 0.05]) == pytest.approx(0.2)


def test_turnover_averages_absolute_position_changes_from_zero():
    assert turnover([1, 1, 0, -0.5]) == pytest.approx((1 + 0 + 1 + 0.5) / 4)


def test_exposure_averages_absolute_positions():
    assert exposure([1, 0, -0.5]) == pytest.approx(0.5)


def test_empty_inputs_return_zero():
    assert cumulative_return([]) == 0.0
    assert max_drawdown([]) == 0.0
    assert turnover([]) == 0.0
    assert exposure([]) == 0.0
