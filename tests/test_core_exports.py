from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from trading_lab.agents import build_agentic_review
from trading_lab.artifacts import ResearchRunArtifact, read_run_artifact
from trading_lab.control_plane import (
    build_evidence_gaps,
    build_lab_control_plane,
    build_next_falsification_tasks,
)
from trading_lab.evidence import summarize_evidence_rigor
from trading_lab.falsification import build_falsification_engine
from trading_lab.point_in_time import build_point_in_time_contract
from trading_lab.readiness import validate_readiness
from trading_lab.readiness_ledger import summarize_readiness_ledger
from trading_lab.trust_packet import build_trust_packet


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_SOURCE = "runs/example-run.json"
READINESS_PATHS = {
    "paper_ledger": PROJECT_ROOT / "runs" / "readiness" / "paper-ledger.json",
    "live_shadow_drift": PROJECT_ROOT / "runs" / "readiness" / "live-shadow-drift.json",
    "calibration_history": PROJECT_ROOT / "runs" / "readiness" / "calibration-history.json",
    "risk_packet": PROJECT_ROOT / "runs" / "readiness" / "risk-packet.json",
}


def test_point_in_time_contract_expands_columns_into_reviewable_field_rows():
    artifact = _artifact()
    summary = summarize_evidence_rigor(
        [*artifact.manifest.columns, "future_return_5d", "vendor_signal"],
        baseline_names=["buy-and-hold"],
    )

    contract = build_point_in_time_contract(
        artifact,
        evidence_summary=asdict(summary),
        source_ref=RUN_SOURCE,
    )

    fields = {field["name"]: field for field in contract["fields"]}
    gap_ids = {gap["id"] for gap in contract["gaps"]}

    assert contract["mode"] == "research_only"
    assert contract["claim_id"] == "toy-moving-average-crossover"
    assert contract["status"] == "needs_review"
    assert contract["as_of_policy"] == "known-at-time inputs only"
    assert fields["close"]["status"] == "allowed"
    assert fields["close"]["evidence_path"] == "manifest.columns.close"
    assert fields["future_return_5d"]["status"] == "leakage_suspect"
    assert fields["future_return_5d"]["review_required"] is True
    assert fields["vendor_signal"]["status"] == "unknown_lineage"
    assert fields["vendor_signal"]["owner"] == "Leak Auditor"
    assert "leakage_suspect:future_return_5d" in gap_ids
    assert "unknown_lineage:vendor_signal" in gap_ids
    assert "missing_baseline:random-control" in gap_ids
    assert _has_no_execution_surface(contract)


def test_falsification_engine_groups_existing_gaps_and_tasks_into_packs():
    artifact = _artifact()
    evidence_rigor = _evidence_rigor(artifact)
    readiness = _readiness_view()
    gaps = build_evidence_gaps(
        artifact,
        readiness=readiness,
        evidence_rigor=evidence_rigor,
        source_ref=RUN_SOURCE,
    )
    tasks = build_next_falsification_tasks(
        artifact,
        evidence_gaps=gaps,
        readiness=readiness,
        source_ref=RUN_SOURCE,
    )

    engine = build_falsification_engine(
        artifact,
        evidence_gaps=gaps,
        control_plane_tasks=tasks,
        source_ref=RUN_SOURCE,
    )

    packs = {pack["pack_id"]: pack for pack in engine["packs"]}
    baseline_pack = packs["baseline-pack"]

    assert engine["mode"] == "research_only"
    assert baseline_pack["status"] == "open"
    assert baseline_pack["owner"] == "Baseline Challenger"
    assert "gate:baseline-comparison" in baseline_pack["gap_ids"]
    assert "rigor:missing_baseline:random-control" in baseline_pack["gap_ids"]
    assert baseline_pack["expected_artifacts"] == ["baseline_pack_result"]
    assert baseline_pack["task_ids"]
    assert all(task["research_only"] is True for task in engine["tasks"])
    assert _has_no_execution_surface(engine)


def test_readiness_ledger_summary_is_append_only_and_source_referenced():
    artifacts = _readiness_artifacts()
    validation = _readiness_validation(artifacts)

    ledger = summarize_readiness_ledger(artifacts, validation=validation)
    second = summarize_readiness_ledger(artifacts, validation=validation)

    assert ledger == second
    assert ledger["mode"] == "research_only"
    assert ledger["write_policy"] == "append_only"
    assert ledger["promotion_ready"] is False
    assert [entry["sequence"] for entry in ledger["entries"]] == [1, 2, 3, 4]
    assert {entry["artifact"] for entry in ledger["entries"]} == set(READINESS_PATHS)
    assert all(entry["source_ref"].startswith("runs/readiness/") for entry in ledger["entries"])
    assert all(entry["source_refs"] == [entry["source_ref"]] for entry in ledger["entries"])
    assert all(len(entry["record_hash"]) == 64 for entry in ledger["entries"])
    entries = {entry["artifact"]: entry for entry in ledger["entries"]}
    assert entries["paper_ledger"]["artifact_type"] == "paper_observation_ledger"
    assert entries["paper_ledger"]["owned_by"] == "Promotion Gatekeeper"
    assert entries["paper_ledger"]["sample_count"] == 6
    assert entries["live_shadow_drift"]["artifact_type"] == "live_shadow_drift_monitor"
    assert entries["live_shadow_drift"]["measured_metrics"] == [
        "expected_vs_observed_return_delta",
        "max_allowed_delta",
        "provider_mismatch_count",
        "quote_freshness_failures",
    ]
    assert entries["calibration_history"]["measured_metrics"] == [
        "brier_score",
        "predicted_probability",
        "realized_frequency",
    ]
    assert entries["risk_packet"]["risk_controls_present"] is True
    assert entries["risk_packet"]["human_review_recorded"] is False
    assert "paper_ledger_sample_count" in {
        check["id"] for check in ledger["missing_failed_checks"]
    }
    assert "risk_packet_human_review" in {
        check["id"] for check in ledger["missing_failed_checks"]
    }
    assert _has_no_execution_surface(ledger)


def test_trust_packet_exports_current_run_and_control_plane_without_promotion():
    artifact = _artifact()
    run = _run_view(artifact)
    readiness = _readiness_view()
    evidence_rigor = _evidence_rigor(artifact)
    agentic_review = {
        **build_agentic_review(
            artifact.gate_results,
            artifact.next_tests,
            artifact.limitations,
        ),
        "source": RUN_SOURCE,
    }
    control_plane = build_lab_control_plane(
        artifact,
        run=run,
        snapshot={"snapshot": "runs/live/latest.json", "events": []},
        readiness=readiness,
        evidence_rigor=evidence_rigor,
        agentic_review=agentic_review,
        blockers=["Evidence run still has unresolved warnings."],
        ranked_attention_items=[],
        spread_bps=None,
        freshness={"label": "unknown", "age_seconds": None},
    )
    ledger = summarize_readiness_ledger(
        readiness["readiness_artifacts"],
        validation=readiness["validation"],
    )

    packet = build_trust_packet(
        artifact,
        run=run,
        control_plane=control_plane,
        readiness_ledger=ledger,
        source_ref=RUN_SOURCE,
    )

    assert packet["mode"] == "research_only"
    assert packet["claim_id"] == "toy-moving-average-crossover"
    assert packet["run_id"] == artifact.run_id
    assert packet["verdict"] == "inconclusive"
    assert packet["export_status"] == "ready_for_research_review"
    assert packet["promotion_ready"] is False
    assert packet["source_refs"]["run"] == RUN_SOURCE
    assert packet["readiness_ledger"]["promotion_ready"] is False
    assert "gate:baseline-comparison" in packet["open_gap_ids"]
    assert packet["next_task_ids"]
    assert packet["review_packet"]["current_stage"] == "research_candidate"
    assert _has_no_execution_surface(packet)


def _artifact() -> ResearchRunArtifact:
    return read_run_artifact(PROJECT_ROOT / RUN_SOURCE)


def _evidence_rigor(artifact: ResearchRunArtifact) -> dict[str, Any]:
    summary = summarize_evidence_rigor(
        artifact.manifest.columns,
        baseline_names=["buy-and-hold"],
    )
    return {
        "run_id": artifact.run_id,
        "source": RUN_SOURCE,
        "summary": asdict(summary),
    }


def _readiness_artifacts() -> dict[str, Any]:
    artifacts = {}
    for name, path in READINESS_PATHS.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        artifacts[name] = {
            "status": payload.get("status", "unknown"),
            "path": str(path.relative_to(PROJECT_ROOT)),
            "recorded_at": payload.get("recorded_at"),
            "payload": payload,
        }
    return artifacts


def _readiness_validation(artifacts: dict[str, Any]) -> dict[str, Any]:
    return validate_readiness(
        paper_ledger=artifacts["paper_ledger"]["payload"],
        live_shadow_drift=artifacts["live_shadow_drift"]["payload"],
        calibration_history=artifacts["calibration_history"]["payload"],
        risk_packet=artifacts["risk_packet"]["payload"],
    )


def _readiness_view() -> dict[str, Any]:
    artifacts = _readiness_artifacts()
    validation = _readiness_validation(artifacts)
    missing = [
        {
            **check,
            "why": check["detail"],
        }
        for check in validation["missing_failed_checks"]
    ]
    return {
        "current_stage": {
            "id": "research_candidate",
            "label": "Research candidate",
        },
        "allowed_output": "Show claim under test, next falsification task, and source-labeled context.",
        "completed_checks": sorted(validation["completed_checks"]),
        "validation": validation,
        "readiness_artifacts": artifacts,
        "missing_checks": missing,
        "not_allowed": [],
    }


def _run_view(artifact: ResearchRunArtifact) -> dict[str, Any]:
    gate_results = [
        {
            "name": gate.gate_name,
            "status": gate.status,
            "passed": gate.status == "pass",
            "detail": gate.remediation_hint,
            "severity": gate.severity,
            "threshold": gate.threshold,
            "evidence": gate.evidence,
        }
        for gate in artifact.gate_results
    ]
    return {
        "id": artifact.hypothesis.id,
        "thesis": artifact.hypothesis.thesis,
        "verdict": artifact.verdict,
        "disproof_score": artifact.disproof_score,
        "gate_counts": {
            "pass": sum(1 for gate in gate_results if gate["status"] == "pass"),
            "warn": sum(1 for gate in gate_results if gate["status"] == "warn"),
            "fail": sum(1 for gate in gate_results if gate["status"] == "fail"),
        },
        "gate_results": gate_results,
        "limitations": artifact.limitations,
        "next_tests": artifact.next_tests,
        "source": RUN_SOURCE,
    }


def _has_no_execution_surface(payload: dict[str, Any]) -> bool:
    serialized = json.dumps(payload).lower()
    banned = [
        "buy now",
        "sell now",
        "submit order",
        "place order",
        "broker api",
        "api key",
    ]
    return not any(phrase in serialized for phrase in banned)
