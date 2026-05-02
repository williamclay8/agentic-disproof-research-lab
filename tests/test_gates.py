from trading_lab.gates import (
    baseline_comparison_gate,
    chronology_gate,
    choose_verdict,
    cost_realism_gate,
    cost_grid_robustness_gate,
    cost_sensitivity_gate,
    lookahead_column_gate,
    parameter_sensitivity_gate,
    reproducibility_gate,
    schema_gate,
    walk_forward_robustness_gate,
)
from trading_lab.models import BacktestResult, BacktestSpec, GateResult


def _spec(transaction_cost_bps=1.0, slippage_bps=0.5):
    return BacktestSpec(
        hypothesis_id="hyp-1",
        dataset_hash="dataset-123",
        short_window=2,
        long_window=4,
        transaction_cost_bps=transaction_cost_bps,
        slippage_bps=slippage_bps,
        execution_delay_bars=1,
    )


def _result(
    strategy_cumulative_return=0.12,
    baseline_cumulative_return=0.05,
    total_cost=0.001,
    fingerprint="fingerprint-1",
):
    metrics = {
        "strategy_cumulative_return": strategy_cumulative_return,
        "baseline_cumulative_return": baseline_cumulative_return,
        "total_cost": total_cost,
    }
    if total_cost is None:
        metrics.pop("total_cost")
    return BacktestResult(
        metrics=metrics,
        trades=[],
        returns=[strategy_cumulative_return],
        positions=[1.0],
        warnings=[],
        fingerprint=fingerprint,
    )


def test_lookahead_column_gate_fails_critical_for_forbidden_column_names():
    result = lookahead_column_gate(["date", "Close", "one_day_forward_return"])

    assert result.status == "fail"
    assert result.severity == "critical"
    assert result.evidence["flagged_columns"] == ["one_day_forward_return"]


def test_lookahead_column_gate_passes_info_when_columns_are_safe():
    result = lookahead_column_gate(["date", "symbol", "close"])

    assert result.status == "pass"
    assert result.severity == "info"
    assert result.evidence["checked_columns"] == ["date", "symbol", "close"]


def test_schema_gate_reports_required_column_evidence():
    passing = schema_gate(["date", "symbol", "open", "high", "low", "close", "volume"])
    failing = schema_gate(["date", "symbol", "close"])

    assert passing.status == "pass"
    assert passing.severity == "info"
    assert failing.status == "fail"
    assert failing.severity == "critical"
    assert "volume" in failing.evidence["missing_columns"]


def test_chronology_gate_reports_sort_and_duplicate_evidence():
    passing = chronology_gate(
        [
            {"date": "2024-01-01", "symbol": "AAA"},
            {"date": "2024-01-01", "symbol": "BBB"},
            {"date": "2024-01-02", "symbol": "AAA"},
        ]
    )
    duplicate = chronology_gate(
        [
            {"date": "2024-01-01", "symbol": "AAA"},
            {"date": "2024-01-01", "symbol": "AAA"},
        ]
    )
    unsorted = chronology_gate(
        [
            {"date": "2024-01-02", "symbol": "AAA"},
            {"date": "2024-01-01", "symbol": "BBB"},
        ]
    )

    assert passing.status == "pass"
    assert duplicate.status == "fail"
    assert duplicate.severity == "critical"
    assert unsorted.status == "fail"
    assert unsorted.severity == "critical"


def test_cost_realism_gate_fails_critical_without_positive_costs_or_cost_metric():
    zero_cost_result = cost_realism_gate(_spec(0.0, 0.0), _result())
    missing_metric_result = cost_realism_gate(_spec(), _result(total_cost=None))

    assert zero_cost_result.status == "fail"
    assert zero_cost_result.severity == "critical"
    assert missing_metric_result.status == "fail"
    assert missing_metric_result.severity == "critical"


def test_cost_realism_gate_passes_with_positive_costs_and_total_cost_evidence():
    result = cost_realism_gate(_spec(), _result(total_cost=0.002))

    assert result.status == "pass"
    assert result.severity == "info"
    assert result.evidence["transaction_cost_bps"] == 1.0
    assert result.evidence["slippage_bps"] == 0.5
    assert result.evidence["total_cost"] == 0.002


def test_baseline_comparison_gate_warns_unless_strategy_beats_baseline():
    warning = baseline_comparison_gate(
        _result(strategy_cumulative_return=0.04, baseline_cumulative_return=0.04)
    )
    passing = baseline_comparison_gate(
        _result(strategy_cumulative_return=0.06, baseline_cumulative_return=0.04)
    )

    assert warning.status == "warn"
    assert warning.severity == "warning"
    assert passing.status == "pass"
    assert passing.severity == "info"


def test_baseline_comparison_gate_fails_when_required_metrics_are_missing():
    result = BacktestResult(
        metrics={"strategy_cumulative_return": 0.01},
        trades=[],
        returns=[],
        positions=[],
        warnings=[],
        fingerprint="fingerprint-1",
    )

    gate = baseline_comparison_gate(result)

    assert gate.status == "fail"
    assert gate.severity == "critical"
    assert gate.evidence["missing_metrics"] == ["baseline_cumulative_return"]


def test_cost_sensitivity_gate_warns_for_negative_or_large_stressed_deterioration():
    negative = cost_sensitivity_gate(
        _result(strategy_cumulative_return=0.10),
        _result(strategy_cumulative_return=-0.01),
    )
    deteriorated = cost_sensitivity_gate(
        _result(strategy_cumulative_return=0.10),
        _result(strategy_cumulative_return=0.049),
    )
    passing = cost_sensitivity_gate(
        _result(strategy_cumulative_return=0.10),
        _result(strategy_cumulative_return=0.06),
    )

    assert negative.status == "warn"
    assert deteriorated.status == "warn"
    assert passing.status == "pass"


def test_cost_sensitivity_gate_fails_when_required_metrics_are_missing():
    missing = BacktestResult(
        metrics={},
        trades=[],
        returns=[],
        positions=[],
        warnings=[],
        fingerprint="fingerprint-1",
    )

    gate = cost_sensitivity_gate(_result(), missing)

    assert gate.status == "fail"
    assert gate.severity == "critical"
    assert gate.evidence["missing_metrics"] == [
        "stressed_strategy_cumulative_return"
    ]


def test_walk_forward_gate_warns_when_too_few_folds_pass():
    gate = walk_forward_robustness_gate(
        [
            {
                "fold": 1,
                "train_start": "2026-01-01",
                "test_start": "2026-01-04",
                "strategy_cumulative_return": 0.01,
                "baseline_cumulative_return": 0.02,
            },
            {
                "fold": 2,
                "train_start": "2026-01-02",
                "test_start": "2026-01-05",
                "strategy_cumulative_return": 0.03,
                "baseline_cumulative_return": 0.01,
            },
        ],
        minimum_folds=2,
        minimum_pass_ratio=0.75,
    )

    assert gate.status == "warn"
    assert gate.severity == "warning"
    assert gate.evidence["passing_folds"] == 1


def test_parameter_sensitivity_gate_warns_for_isolated_peak():
    gate = parameter_sensitivity_gate(
        selected_return=0.08,
        neighborhood_results=[
            {"short_window": 2, "long_window": 3, "strategy_cumulative_return": 0.08},
            {"short_window": 2, "long_window": 4, "strategy_cumulative_return": -0.01},
            {"short_window": 3, "long_window": 4, "strategy_cumulative_return": 0.0},
        ],
        minimum_positive_ratio=0.67,
    )

    assert gate.status == "warn"
    assert gate.evidence["positive_ratio"] < 0.67


def test_cost_grid_gate_warns_when_only_cheapest_scenarios_survive():
    gate = cost_grid_robustness_gate(
        [
            {"transaction_cost_bps": 0, "slippage_bps": 0, "execution_delay_bars": 1, "strategy_cumulative_return": 0.03},
            {"transaction_cost_bps": 10, "slippage_bps": 5, "execution_delay_bars": 1, "strategy_cumulative_return": -0.01},
            {"transaction_cost_bps": 30, "slippage_bps": 15, "execution_delay_bars": 2, "strategy_cumulative_return": -0.02},
        ],
        minimum_survival_ratio=0.5,
    )

    assert gate.status == "warn"
    assert gate.evidence["survival_ratio"] < 0.5


def test_reproducibility_gate_requires_matching_fingerprints():
    passing = reproducibility_gate(_result(), _result())
    failing = reproducibility_gate(_result(), _result(fingerprint="fingerprint-2"))

    assert passing.status == "pass"
    assert passing.severity == "info"
    assert failing.status == "fail"
    assert failing.severity == "critical"


def test_choose_verdict_prioritizes_critical_failures_then_noncritical_warnings():
    critical_fail = GateResult(
        gate_name="reproducibility",
        status="fail",
        evidence={},
        threshold="fingerprints match",
        remediation_hint="Rerun with fixed inputs.",
        severity="critical",
    )
    warning = GateResult(
        gate_name="baseline comparison",
        status="warn",
        evidence={},
        threshold="strategy return > baseline return",
        remediation_hint="Retest against a stronger baseline.",
        severity="warning",
    )
    passing = GateResult(
        gate_name="lookahead columns",
        status="pass",
        evidence={},
        threshold="no forbidden columns",
        remediation_hint="No action.",
        severity="info",
    )

    assert choose_verdict([passing, critical_fail, warning]) == "rejected"
    assert choose_verdict([passing, warning]) == "inconclusive"
    assert choose_verdict([passing]) == "passed preliminary gates"
