from __future__ import annotations

import json

from trading_lab.artifacts import (
    ResearchRunArtifact,
    read_run_artifact,
    write_run_artifact,
)
from trading_lab.models import (
    BacktestResult,
    BacktestSpec,
    DatasetManifest,
    GateResult,
    Hypothesis,
)


def test_run_artifact_round_trips_as_structured_json(tmp_path):
    artifact = _artifact()
    path = tmp_path / "runs" / "run.json"

    write_run_artifact(path, artifact)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["verdict"] == "inconclusive"
    assert payload["hypothesis"]["id"] == "hyp-1"
    assert payload["gate_results"][0]["gate_name"] == "baseline comparison"

    loaded = read_run_artifact(path)
    assert loaded == artifact


def test_run_artifact_disproof_score_weights_failures_and_warnings():
    artifact = _artifact(
        gates=[
            _gate("critical leak", "fail", "critical"),
            _gate("baseline comparison", "warn", "warning"),
            _gate("schema columns", "pass", "info"),
        ]
    )

    assert artifact.disproof_score == 5


def _artifact(gates: list[GateResult] | None = None) -> ResearchRunArtifact:
    return ResearchRunArtifact(
        run_id="run-1",
        verdict="inconclusive",
        hypothesis=Hypothesis(
            id="hyp-1",
            thesis="Offline signal may survive disproof.",
            null_hypothesis="Offline signal has no edge.",
            asset_universe=["AAA"],
            time_horizon="daily",
            signal_definition="Moving average crossover.",
        ),
        manifest=DatasetManifest(
            source="local.csv",
            symbols=["AAA"],
            start_date="2026-01-01",
            end_date="2026-01-02",
            columns=["date", "symbol", "open", "high", "low", "close", "volume"],
            content_hash="hash-1",
        ),
        spec=BacktestSpec(
            hypothesis_id="hyp-1",
            dataset_hash="hash-1",
            short_window=2,
            long_window=3,
            transaction_cost_bps=10,
            slippage_bps=5,
            execution_delay_bars=1,
        ),
        result=BacktestResult(
            metrics={
                "strategy_cumulative_return": 0.01,
                "baseline_cumulative_return": 0.02,
            },
            trades=[],
            returns=[0.01],
            positions=[1.0],
            warnings=[],
            fingerprint="fingerprint-1",
        ),
        gate_results=gates or [_gate("baseline comparison", "warn", "warning")],
        limitations=["Toy data."],
        next_tests=["Run a walk-forward split."],
    )


def _gate(name: str, status: str, severity: str) -> GateResult:
    return GateResult(
        gate_name=name,
        status=status,
        evidence={"example": name},
        threshold="threshold",
        remediation_hint="Add pressure.",
        severity=severity,
    )
