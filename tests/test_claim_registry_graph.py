from __future__ import annotations

import json
from pathlib import Path

from trading_lab.artifacts import ResearchRunArtifact, write_run_artifact
from trading_lab.claim_registry import build_claim_run_registry
from trading_lab.evidence_graph import build_evidence_graph
from trading_lab.models import (
    BacktestResult,
    BacktestSpec,
    DatasetManifest,
    GateResult,
    Hypothesis,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SURFACE_TERMS = (
    "broker",
    "account",
    "order",
    "advice",
    "sizing",
    "live-signal",
)


def test_claim_run_registry_derives_records_from_existing_artifacts():
    registry = build_claim_run_registry(
        PROJECT_ROOT / "hypotheses",
        PROJECT_ROOT / "runs",
        project_root=PROJECT_ROOT,
    )

    payload = registry.to_payload()

    assert payload["schema_version"] == 1
    assert payload["mode"] == "research_only"
    assert payload["boundary"] == "offline research falsification only"
    assert [claim["claim_id"] for claim in payload["claims"]] == [
        "toy-moving-average-crossover"
    ]
    assert payload["claims"][0]["source_ref"] == (
        "hypotheses/toy-moving-average-crossover.json"
    )
    assert payload["claims"][0]["run_ids"] == [
        "toy-moving-average-crossover-52635e40"
    ]
    assert payload["claims"][0]["latest_verdict"] == "inconclusive"
    assert payload["claims"][0]["open_gate_names"] == [
        "baseline comparison",
        "walk-forward robustness",
    ]
    assert len(payload["claims"][0]["artifact_hash"]) == 64

    assert [run["run_id"] for run in payload["runs"]] == [
        "toy-moving-average-crossover-52635e40"
    ]
    run = payload["runs"][0]
    assert run["claim_id"] == "toy-moving-average-crossover"
    assert run["source_ref"] == "runs/example-run.json"
    assert run["gate_counts"] == {"fail": 0, "pass": 8, "warn": 2}
    assert run["dataset_hash"] == (
        "52635e40771bdd93cb3df91e76808bcdf5cbb67446bebb28c136611068e3ea06"
    )
    assert {
        gate["gate_id"]
        for gate in run["gate_evidence"]
        if gate["status"] != "pass"
    } == {
        "gate:toy-moving-average-crossover-52635e40:baseline-comparison",
        "gate:toy-moving-average-crossover-52635e40:walk-forward-robustness",
    }
    assert payload["issues"] == []
    assert_no_execution_surface(payload)


def test_claim_run_registry_supports_multiple_claims_and_orphan_run_issues(tmp_path):
    hypotheses_dir = tmp_path / "hypotheses"
    runs_dir = tmp_path / "runs"
    hypotheses_dir.mkdir()
    runs_dir.mkdir()
    _write_hypothesis(hypotheses_dir / "beta.json", "beta-claim")
    _write_hypothesis(hypotheses_dir / "alpha.json", "alpha-claim")
    write_run_artifact(runs_dir / "beta-run.json", _artifact("run-beta", "beta-claim"))
    write_run_artifact(
        runs_dir / "orphan-run.json",
        _artifact("run-orphan", "orphan-claim"),
    )

    registry = build_claim_run_registry(
        hypotheses_dir,
        runs_dir,
        project_root=tmp_path,
    )
    payload = registry.to_payload()

    assert [claim["claim_id"] for claim in payload["claims"]] == [
        "alpha-claim",
        "beta-claim",
    ]
    assert payload["claims"][0]["run_ids"] == []
    assert payload["claims"][1]["run_ids"] == ["run-beta"]
    assert [run["run_id"] for run in payload["runs"]] == [
        "run-beta",
        "run-orphan",
    ]
    assert payload["issues"] == [
        {
            "kind": "unregistered_run_claim",
            "claim_id": "orphan-claim",
            "run_id": "run-orphan",
            "source_ref": "runs/orphan-run.json",
        }
    ]
    assert_no_execution_surface(payload)


def test_evidence_graph_links_registry_records_with_stable_source_refs():
    registry = build_claim_run_registry(
        PROJECT_ROOT / "hypotheses",
        PROJECT_ROOT / "runs",
        project_root=PROJECT_ROOT,
    )

    graph = build_evidence_graph(registry)
    payload = graph.to_payload()

    node_ids = {node["id"] for node in payload["nodes"]}
    claim_node = "claim:toy-moving-average-crossover"
    run_node = "run:toy-moving-average-crossover-52635e40"
    dataset_node = (
        "dataset:52635e40771bdd93cb3df91e76808bcdf5cbb67446bebb28c136611068e3ea06"
    )
    baseline_gate_node = (
        "gate:toy-moving-average-crossover-52635e40:baseline-comparison"
    )
    assert {claim_node, run_node, dataset_node, baseline_gate_node} <= node_ids

    baseline_gate = next(
        node for node in payload["nodes"] if node["id"] == baseline_gate_node
    )
    assert baseline_gate["source_refs"] == ["runs/example-run.json"]
    assert baseline_gate["attributes"]["status"] == "warn"
    assert baseline_gate["attributes"]["severity"] == "warning"
    assert baseline_gate["attributes"]["evidence_path"] == (
        "gate_results.baseline-comparison"
    )
    assert len(baseline_gate["attributes"]["evidence_digest"]) == 64

    edges = {
        (edge["source"], edge["target"], edge["relationship"])
        for edge in payload["edges"]
    }
    assert (claim_node, run_node, "tested_by") in edges
    assert (run_node, dataset_node, "uses_dataset") in edges
    assert (run_node, baseline_gate_node, "records_gate") in edges
    assert (baseline_gate_node, claim_node, "challenges_claim") in edges
    assert payload == build_evidence_graph(registry).to_payload()
    assert_no_execution_surface(payload)


def assert_no_execution_surface(payload: dict) -> None:
    serialized = json.dumps(payload, sort_keys=True).lower()
    for term in FORBIDDEN_SURFACE_TERMS:
        assert term not in serialized
    assert "trades" not in serialized
    assert "positions" not in serialized


def _write_hypothesis(path: Path, claim_id: str) -> None:
    payload = {
        "schema_version": 1,
        "id": claim_id,
        "status": "active",
        "registered_at": "2026-05-02T00:00:00Z",
        "thesis": f"{claim_id} may survive offline falsification.",
        "null_hypothesis": f"{claim_id} has no edge after costs.",
        "asset_universe": ["AAA"],
        "time_horizon": "daily bars over a local sample",
        "signal_definition": "Toy moving-average crossover.",
        "expected_failure_modes": ["weak comparator"],
        "falsification_tests": ["baseline comparison"],
        "pre_registered_metrics": ["strategy_cumulative_return"],
        "acceptance_thresholds": {
            "baseline_comparison": "strategy_cumulative_return > baseline"
        },
        "data_requirements": ["local CSV only"],
        "posthoc_edit_policy": "No edits after observing results.",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _artifact(run_id: str, claim_id: str) -> ResearchRunArtifact:
    return ResearchRunArtifact(
        run_id=run_id,
        verdict="inconclusive",
        hypothesis=Hypothesis(
            id=claim_id,
            thesis=f"{claim_id} may survive offline falsification.",
            null_hypothesis=f"{claim_id} has no edge after costs.",
            asset_universe=["AAA"],
            time_horizon="daily",
            signal_definition="Toy moving-average crossover.",
        ),
        manifest=DatasetManifest(
            source="examples/local.csv",
            symbols=["AAA"],
            start_date="2026-01-01",
            end_date="2026-01-02",
            columns=["date", "symbol", "open", "high", "low", "close", "volume"],
            content_hash=f"hash-{claim_id}",
        ),
        spec=BacktestSpec(
            hypothesis_id=claim_id,
            dataset_hash=f"hash-{claim_id}",
            short_window=2,
            long_window=3,
            transaction_cost_bps=10,
            slippage_bps=5,
            execution_delay_bars=1,
        ),
        result=BacktestResult(
            metrics={"strategy_cumulative_return": 0.01},
            trades=[],
            returns=[0.01],
            positions=[1.0],
            warnings=[],
            fingerprint=f"fingerprint-{claim_id}",
        ),
        gate_results=[_gate("baseline comparison", "warn", "warning")],
        limitations=["Local sample only."],
        next_tests=["Record more offline comparator evidence."],
    )


def _gate(name: str, status: str, severity: str) -> GateResult:
    return GateResult(
        gate_name=name,
        status=status,
        evidence={"strategy_cumulative_return": 0.01},
        threshold="strategy_cumulative_return > baseline",
        remediation_hint="Comparator evidence remains open.",
        severity=severity,
    )
