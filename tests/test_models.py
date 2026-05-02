import pytest

from trading_lab.models import (
    BacktestResult,
    BacktestSpec,
    DatasetManifest,
    GateResult,
    Hypothesis,
    ResearchReport,
)


def test_hypothesis_requires_core_fields():
    required = {
        "id": "hyp-1",
        "thesis": "Momentum may persist in the toy universe.",
        "null_hypothesis": "Momentum has no predictive value.",
        "asset_universe": ["AAA", "BBB"],
        "time_horizon": "daily over one year",
        "signal_definition": "long when short MA is above long MA",
    }

    for field, value in required.items():
        invalid = dict(required)
        invalid[field] = [] if field == "asset_universe" else ""

        with pytest.raises(ValueError, match=field):
            Hypothesis(**invalid)

    hypothesis = Hypothesis(
        **required,
        expected_failure_modes=["lookahead bias"],
        falsification_tests=["shuffle labels"],
        pre_registered_metrics=["sharpe"],
        acceptance_thresholds={"max_drawdown": "< 0.2"},
        data_requirements=["adjusted close"],
        posthoc_edit_policy="No changes after backtest.",
    )

    assert hypothesis.expected_failure_modes == ["lookahead bias"]
    assert hypothesis.falsification_tests == ["shuffle labels"]
    assert hypothesis.pre_registered_metrics == ["sharpe"]
    assert hypothesis.acceptance_thresholds == {"max_drawdown": "< 0.2"}
    assert hypothesis.data_requirements == ["adjusted close"]
    assert hypothesis.posthoc_edit_policy == "No changes after backtest."


def test_dataset_manifest_requires_symbols_and_hash():
    with pytest.raises(ValueError, match="symbols"):
        DatasetManifest(
            source="local.csv",
            symbols=[],
            start_date="2024-01-01",
            end_date="2024-01-31",
            columns=["date", "close"],
            content_hash="abc123",
        )

    with pytest.raises(ValueError, match="content_hash"):
        DatasetManifest(
            source="local.csv",
            symbols=["AAA"],
            start_date="2024-01-01",
            end_date="2024-01-31",
            columns=["date", "close"],
            content_hash="",
        )

    manifest = DatasetManifest(
        source="local.csv",
        symbols=["AAA"],
        start_date="2024-01-01",
        end_date="2024-01-31",
        columns=["date", "close"],
        content_hash="abc123",
        warnings=["missing volume"],
    )

    assert manifest.warnings == ["missing volume"]


def test_backtest_spec_validates_window_and_cost_bounds():
    valid = {
        "hypothesis_id": "hyp-1",
        "dataset_hash": "abc123",
        "short_window": 5,
        "long_window": 20,
        "transaction_cost_bps": 1.0,
        "slippage_bps": 0.5,
        "execution_delay_bars": 1,
    }

    invalid_cases = [
        ("short_window", 0, "short_window"),
        ("long_window", 0, "long_window"),
        ("long_window", 5, "long_window"),
        ("transaction_cost_bps", -0.1, "transaction_cost_bps"),
        ("slippage_bps", -0.1, "slippage_bps"),
        ("execution_delay_bars", 0, "execution_delay_bars"),
    ]

    for field, value, message in invalid_cases:
        invalid = dict(valid)
        invalid[field] = value
        with pytest.raises(ValueError, match=message):
            BacktestSpec(**invalid)

    spec = BacktestSpec(**valid)

    assert spec.short_window == 5
    assert spec.long_window == 20
    assert spec.transaction_cost_bps == 1.0
    assert spec.slippage_bps == 0.5
    assert spec.execution_delay_bars == 1


def test_result_and_report_models_store_research_artifacts():
    result = BacktestResult(
        metrics={"sharpe": 0.8},
        trades=[{"symbol": "AAA", "side": "buy"}],
        returns=[0.01, -0.02],
        positions=[1, 0],
        warnings=["short history"],
        fingerprint="result-123",
    )

    gate = GateResult(
        gate_name="cost sensitivity",
        status="warn",
        evidence={"net_return": 0.03},
        threshold="net_return > 0",
        remediation_hint="Retest with wider costs.",
        severity="warning",
    )

    report = ResearchReport(
        verdict="inconclusive",
        summary="Signal needs more falsification.",
        gate_results=[gate],
        metrics=result.metrics,
        limitations=["toy data"],
        next_tests=["walk-forward split"],
    )

    assert result.fingerprint == "result-123"
    assert gate.status == "warn"
    assert gate.severity == "warning"
    assert report.verdict == "inconclusive"
    assert report.gate_results == [gate]


def test_gate_and_report_reject_unknown_status_values():
    with pytest.raises(ValueError, match="status"):
        GateResult(
            gate_name="lookahead",
            status="skip",
            evidence={},
            threshold="no lookahead columns",
            remediation_hint="Remove invalid fields.",
            severity="critical",
        )

    with pytest.raises(ValueError, match="severity"):
        GateResult(
            gate_name="lookahead",
            status="fail",
            evidence={},
            threshold="no lookahead columns",
            remediation_hint="Remove invalid fields.",
            severity="urgent",
        )

    with pytest.raises(ValueError, match="verdict"):
        ResearchReport(
            verdict="approved",
            summary="Unsupported verdict.",
            gate_results=[],
            metrics={},
            limitations=[],
            next_tests=[],
        )
