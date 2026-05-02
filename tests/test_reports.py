from trading_lab.gates import baseline_comparison_gate, cost_realism_gate
from trading_lab.models import BacktestResult, BacktestSpec, DatasetManifest, Hypothesis
from trading_lab.reports import render_markdown_report


def _hypothesis():
    return Hypothesis(
        id="hyp-1",
        thesis="A moving-average signal may outperform buy and hold.",
        null_hypothesis="The moving-average signal has no edge.",
        asset_universe=["AAA", "BBB"],
        time_horizon="daily bars over a toy sample",
        signal_definition="Long when short moving average exceeds long moving average.",
        expected_failure_modes=["lookahead bias", "cost sensitivity"],
        falsification_tests=["baseline comparison", "cost stress"],
        pre_registered_metrics=["strategy_cumulative_return"],
        acceptance_thresholds={"strategy_cumulative_return": "> baseline"},
        data_requirements=["date", "symbol", "close"],
        posthoc_edit_policy="No edits after seeing backtest results.",
    )


def _manifest():
    return DatasetManifest(
        source="examples/toy_prices.csv",
        symbols=["AAA", "BBB"],
        start_date="2024-01-01",
        end_date="2024-01-31",
        columns=["date", "symbol", "close"],
        content_hash="dataset-123",
        warnings=["toy dataset"],
    )


def _spec():
    return BacktestSpec(
        hypothesis_id="hyp-1",
        dataset_hash="dataset-123",
        short_window=2,
        long_window=4,
        transaction_cost_bps=1.0,
        slippage_bps=0.5,
        execution_delay_bars=1,
    )


def _result(strategy_cumulative_return=0.03, baseline_cumulative_return=0.05):
    return BacktestResult(
        metrics={
            "strategy_cumulative_return": strategy_cumulative_return,
            "baseline_cumulative_return": baseline_cumulative_return,
            "total_cost": 0.002,
        },
        trades=[{"symbol": "AAA", "cost": 0.001}],
        returns=[0.01, 0.02],
        positions=[0.0, 1.0],
        warnings=["insufficient rows for BBB"],
        fingerprint="result-123",
    )


def test_render_markdown_report_includes_required_sections_and_computed_verdict():
    spec = _spec()
    result = _result()
    gate_results = [
        cost_realism_gate(spec, result),
        baseline_comparison_gate(result),
    ]

    markdown = render_markdown_report(
        _hypothesis(),
        _manifest(),
        spec,
        result,
        gate_results,
        limitations=["Toy sample only."],
        next_tests=["Run a walk-forward split."],
    )

    assert "# Research Report" in markdown
    assert "## Verdict" in markdown
    assert "inconclusive" in markdown
    assert "## Hypothesis" in markdown
    assert "## Power Boundary" in markdown
    assert "This report can falsify" in markdown
    assert "This report cannot trade" in markdown
    assert "A moving-average signal may outperform buy and hold." in markdown
    assert "## Dataset" in markdown
    assert "examples/toy_prices.csv" in markdown
    assert "dataset-123" in markdown
    assert "## Backtest Metrics" in markdown
    assert "strategy_cumulative_return" in markdown
    assert "## Falsification Gates" in markdown
    assert "baseline comparison" in markdown
    assert "## Evidence Coverage" in markdown
    assert "schema columns: missing / missing" in markdown
    assert "## Research Action Queue" in markdown
    assert "Retest warning evidence" in markdown
    assert "## Limitations" in markdown
    assert "Toy sample only." in markdown
    assert "## Next Tests" in markdown
    assert "Run a walk-forward split." in markdown
    assert "## Safety Note" in markdown
    assert "not investment advice" in markdown
    assert "No live trading" in markdown
    assert "broker connection" in markdown


def test_render_markdown_report_never_describes_hypothesis_as_accepted():
    spec = _spec()
    result = _result(strategy_cumulative_return=0.08, baseline_cumulative_return=0.05)

    markdown = render_markdown_report(
        _hypothesis(),
        _manifest(),
        spec,
        result,
        [
            cost_realism_gate(spec, result),
            baseline_comparison_gate(result),
        ],
        limitations=[],
        next_tests=[],
    )

    assert "passed preliminary gates" in markdown
    assert "accepted" not in markdown.lower()
