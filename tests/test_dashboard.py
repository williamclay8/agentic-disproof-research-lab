from __future__ import annotations

from trading_lab.dashboard import render_dashboard_html
from trading_lab.artifacts import ResearchRunArtifact
from trading_lab.models import (
    BacktestResult,
    BacktestSpec,
    DatasetManifest,
    GateResult,
    Hypothesis,
)


def test_render_dashboard_html_builds_offline_falsification_cockpit():
    html = render_dashboard_html(
        hypothesis=_hypothesis(),
        manifest=_manifest(),
        spec=_spec(),
        result=_result(),
        gate_results=_gates(),
        limitations=["Toy dataset only."],
        next_tests=["Run a walk-forward split."],
    )

    assert html.startswith("<!doctype html>")
    assert "Falsification cockpit" in html
    assert "inconclusive" in html
    assert "hyp-1" in html
    assert "The signal has no edge after costs." in html
    assert "schema columns" in html
    assert "baseline comparison" in html
    assert "strategy_cumulative_return" in html
    assert "dataset-hash" in html
    assert "fingerprint-1" in html
    assert "offline research artifact" in html
    assert "not investment advice" in html
    assert "No broker APIs" in html
    assert "Agentic Disproof Loop" in html
    assert "Treat missing evidence as a critical failure" in html
    assert "Evidence Docket" in html
    assert "Research Training Maturity" in html
    assert "Mistake Taxonomy" in html
    assert "Experiment Ledger" in html
    assert "Outcome Flow" in html
    assert "Commercial Readiness" in html
    assert "100-Round Training Roadmap" in html
    assert "100 offline review rounds" in html
    assert "What it means" in html
    assert "Why it matters" in html
    assert "Inspect next" in html
    assert "The claim was written before evidence review." in html
    assert "Open the walk-forward gate evidence." in html
    assert "Reader Guide" in html
    assert "Start with Outcome Flow" in html
    assert "0 fail" in html
    assert "warning gates remain" in html
    assert "strategy 1.00% vs baseline 2.00%" in html
    assert "Current Loop Position" in html
    assert "Matching fingerprints indicate" in html
    assert "Registered before run" in html
    assert "accepted" not in html.lower()
    assert "http://" not in html
    assert "https://" not in html
    assert "cdn" not in html.lower()


def test_render_dashboard_html_compares_multiple_run_artifacts():
    weaker = _artifact("run-weaker", _gates())
    harsher = _artifact(
        "run-harsher",
        [
            GateResult(
                gate_name="lookahead columns",
                status="fail",
                evidence={"flagged_columns": ["future_return"]},
                threshold="no forward-looking columns",
                remediation_hint="Remove leakage fields.",
                severity="critical",
            ),
            *_gates(),
        ],
    )

    html = render_dashboard_html(
        hypothesis=_hypothesis(),
        manifest=_manifest(),
        spec=_spec(),
        result=_result(),
        gate_results=_gates(),
        limitations=["Toy dataset only."],
        next_tests=["Run a walk-forward split."],
        run_artifacts=[weaker, harsher],
    )

    assert "Runner Evidence" in html
    assert "run-harsher" in html
    assert "run-weaker" in html
    assert html.index("run-harsher") < html.index("run-weaker")
    assert "Disproof score" in html
    assert "Sorted by disproof score" in html


def test_render_dashboard_html_escapes_dynamic_content():
    hypothesis = Hypothesis(
        id="hyp-<script>",
        thesis="<script>alert(1)</script>",
        null_hypothesis="Null <b>bold</b>",
        asset_universe=["AAA"],
        time_horizon="daily",
        signal_definition="<img src=x onerror=alert(1)>",
    )

    html = render_dashboard_html(
        hypothesis=hypothesis,
        manifest=_manifest(),
        spec=_spec(),
        result=_result(),
        gate_results=_gates(),
        limitations=["Use <local> data only."],
        next_tests=["Reject <bad> evidence."],
    )

    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "&lt;b&gt;bold&lt;/b&gt;" in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html
    assert "<script>alert(1)</script>" not in html
    assert "<b>bold</b>" not in html
    assert "<img src=x onerror=alert(1)>" not in html


def _hypothesis() -> Hypothesis:
    return Hypothesis(
        id="hyp-1",
        thesis="A cautious offline signal may beat baseline.",
        null_hypothesis="The signal has no edge after costs.",
        asset_universe=["AAA", "BBB"],
        time_horizon="daily",
        signal_definition="Long when short average is above long average.",
        expected_failure_modes=["lookahead leakage", "baseline underperformance"],
        falsification_tests=["schema columns", "baseline comparison"],
        pre_registered_metrics=["strategy_cumulative_return"],
        acceptance_thresholds={"baseline": "strategy > baseline"},
        data_requirements=["local CSV"],
        posthoc_edit_policy="Do not edit after results.",
    )


def _manifest() -> DatasetManifest:
    return DatasetManifest(
        source="examples/toy.csv",
        symbols=["AAA", "BBB"],
        start_date="2026-01-01",
        end_date="2026-01-03",
        columns=["date", "symbol", "open", "high", "low", "close", "volume"],
        content_hash="dataset-hash",
    )


def _spec() -> BacktestSpec:
    return BacktestSpec(
        hypothesis_id="hyp-1",
        dataset_hash="dataset-hash",
        short_window=2,
        long_window=3,
        transaction_cost_bps=10,
        slippage_bps=5,
        execution_delay_bars=1,
    )


def _result() -> BacktestResult:
    return BacktestResult(
        metrics={
            "strategy_cumulative_return": 0.01,
            "baseline_cumulative_return": 0.02,
            "max_drawdown": -0.01,
            "turnover": 0.25,
            "total_cost": 0.001,
        },
        trades=[{"symbol": "AAA"}],
        returns=[0.0, 0.01],
        positions=[],
        warnings=[],
        fingerprint="fingerprint-1",
    )


def _gates() -> list[GateResult]:
    return [
        GateResult(
            gate_name="schema columns",
            status="pass",
            evidence={"missing_columns": []},
            threshold="all required columns present",
            remediation_hint="No action required.",
            severity="info",
        ),
        GateResult(
            gate_name="baseline comparison",
            status="warn",
            evidence={
                "strategy_cumulative_return": 0.01,
                "baseline_cumulative_return": 0.02,
            },
            threshold="strategy_cumulative_return > baseline_cumulative_return",
            remediation_hint="Retest before drawing conclusions.",
            severity="warning",
        ),
    ]


def _artifact(run_id: str, gates: list[GateResult]) -> ResearchRunArtifact:
    return ResearchRunArtifact(
        run_id=run_id,
        verdict="inconclusive",
        hypothesis=_hypothesis(),
        manifest=_manifest(),
        spec=_spec(),
        result=_result(),
        gate_results=gates,
        limitations=["Toy dataset only."],
        next_tests=["Run a walk-forward split."],
    )
