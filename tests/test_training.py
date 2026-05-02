from __future__ import annotations

from trading_lab.models import GateResult
from trading_lab.training import (
    build_commercial_readiness,
    build_experiment_ledger,
    build_mistake_taxonomy,
    build_training_plan,
    build_workflow_outcomes,
    research_maturity_score,
)
from trading_lab.artifacts import ResearchRunArtifact
from trading_lab.models import BacktestResult, BacktestSpec, DatasetManifest, Hypothesis


def test_research_maturity_score_rewards_evidence_coverage_not_returns():
    gates = [
        _gate("schema columns", "pass", "info"),
        _gate("chronology", "pass", "info"),
        _gate("walk-forward robustness", "warn", "warning"),
        _gate("parameter sensitivity", "pass", "info"),
        _gate("cost grid robustness", "pass", "info"),
    ]

    score = research_maturity_score(gates)

    assert score["score"] == 50
    assert score["label"] == "partial evidence coverage"
    assert "return" not in " ".join(score["components"]).lower()


def test_mistake_taxonomy_maps_warning_gates_to_learning_items():
    taxonomy = build_mistake_taxonomy(
        [
            _gate("baseline comparison", "warn", "warning"),
            _gate("walk-forward robustness", "warn", "warning"),
        ]
    )

    names = {item["name"] for item in taxonomy}
    assert "Comparator weakness" in names
    assert "Fold fragility" in names
    assert all("trade" not in item["learning_focus"].lower() for item in taxonomy)


def test_training_plan_has_100_rounds_without_advice_language():
    plan = build_training_plan()

    assert len(plan) == 100
    assert plan[0]["round"] == 1
    assert plan[-1]["round"] == 100
    text = " ".join(str(value) for item in plan for value in item.values()).lower()
    for forbidden in [
        "buy",
        "sell",
        "recommended",
        "entry",
        "exit",
        "place order",
        "submit order",
        "api_key",
        "secret",
        "credentials",
        "websocket",
    ]:
        assert forbidden not in text


def test_training_plan_items_are_evidence_first():
    evidence_terms = (
        "gate",
        "baseline",
        "cost",
        "slippage",
        "delay",
        "fold",
        "parameter",
        "dataset",
        "hash",
        "reproducibility",
        "limitation",
        "null",
        "evidence",
    )

    for item in build_training_plan():
        text = " ".join(str(value).lower() for value in item.values())
        assert any(term in text for term in evidence_terms)


def test_experiment_ledger_summarizes_recurring_mistakes_across_runs():
    ledger = build_experiment_ledger(
        [
            _artifact("run-1", [_gate("baseline comparison", "warn", "warning")]),
            _artifact(
                "run-2",
                [
                    _gate("baseline comparison", "warn", "warning"),
                    _gate("walk-forward robustness", "warn", "warning"),
                ],
            ),
        ]
    )

    row = ledger[0]
    assert row["hypothesis_id"] == "hyp-1"
    assert row["runs"] == 2
    assert row["latest_verdict"] == "inconclusive"
    assert row["worst_disproof_score"] == 4
    assert "Comparator weakness" in row["recurring_mistake_types"]
    assert "Fold fragility" in row["recurring_mistake_types"]
    assert row["next_curriculum_round"] > 0


def test_workflow_outcomes_turn_evidence_into_usable_flow():
    outcomes = build_workflow_outcomes(
        [_artifact("run-1", [_gate("baseline comparison", "warn", "warning")])]
    )

    labels = {item["label"] for item in outcomes}
    assert "Inspect first" in labels
    assert "Current learning objective" in labels
    assert "Next evidence product" in labels
    text = " ".join(item["outcome"] for item in outcomes).lower()
    assert "recommend" not in text
    assert "trade" not in text


def test_commercial_readiness_frames_paid_value_as_evidence_not_returns():
    readiness = build_commercial_readiness(
        [_artifact("run-1", [_gate("baseline comparison", "warn", "warning")])]
    )

    assert readiness["audience"] == "systematic research teams"
    assert readiness["paid_data_asset"] == "auditable falsification records"
    text = " ".join(str(value) for value in readiness.values()).lower()
    assert "returns" not in text
    assert "recommendation" not in text


def _gate(name: str, status: str, severity: str) -> GateResult:
    return GateResult(
        gate_name=name,
        status=status,
        evidence={},
        threshold="evidence recorded",
        remediation_hint="Recorded evidence gap.",
        severity=severity,
    )


def _artifact(run_id: str, gates: list[GateResult]) -> ResearchRunArtifact:
    return ResearchRunArtifact(
        run_id=run_id,
        verdict="inconclusive",
        hypothesis=Hypothesis(
            id="hyp-1",
            thesis="Offline claim.",
            null_hypothesis="No edge.",
            asset_universe=["AAA"],
            time_horizon="daily",
            signal_definition="Toy crossover.",
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
            metrics={},
            trades=[],
            returns=[],
            positions=[],
            warnings=[],
            fingerprint=run_id,
        ),
        gate_results=gates,
        limitations=[],
        next_tests=[],
    )
