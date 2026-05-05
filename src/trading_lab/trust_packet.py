"""Trust packet export data derived from run and control-plane outputs."""

from __future__ import annotations

from typing import Any

from trading_lab.artifacts import ResearchRunArtifact


def build_trust_packet(
    artifact: ResearchRunArtifact,
    *,
    run: dict[str, Any],
    control_plane: dict[str, Any],
    readiness_ledger: dict[str, Any],
    source_ref: str,
) -> dict[str, Any]:
    """Build a compact research review packet from existing derived outputs."""

    gaps = list(control_plane.get("evidence_gaps", []))
    tasks = list(control_plane.get("next_falsification_tasks", []))
    promotion_ready = bool(readiness_ledger.get("promotion_ready"))
    return {
        "mode": "research_only",
        "packet_schema": "trust_packet.v1",
        "claim_id": artifact.hypothesis.id,
        "run_id": artifact.run_id,
        "verdict": artifact.verdict,
        "export_status": _export_status(promotion_ready, gaps),
        "promotion_ready": promotion_ready,
        "source_refs": {
            "run": source_ref,
            "dataset": artifact.manifest.source,
            "readiness": [
                entry["source_ref"]
                for entry in readiness_ledger.get("entries", [])
                if entry.get("source_ref")
            ],
        },
        "evidence_hashes": {
            "dataset_hash": artifact.manifest.content_hash,
            "run_fingerprint": artifact.result.fingerprint,
            "readiness_ledger_id": readiness_ledger.get("ledger_id"),
        },
        "gate_summary": {
            "counts": run.get("gate_counts", {}),
            "open_warning_gates": [
                gate["name"]
                for gate in run.get("gate_results", [])
                if gate.get("status") == "warn"
            ],
            "open_failure_gates": [
                gate["name"]
                for gate in run.get("gate_results", [])
                if gate.get("status") == "fail"
            ],
        },
        "open_gap_ids": [str(gap.get("id")) for gap in gaps if gap.get("id")],
        "next_task_ids": [
            str(task.get("task_id")) for task in tasks if task.get("task_id")
        ],
        "readiness_ledger": {
            "ledger_id": readiness_ledger.get("ledger_id"),
            "write_policy": readiness_ledger.get("write_policy"),
            "entry_count": readiness_ledger.get("entry_count"),
            "promotion_ready": promotion_ready,
            "missing_failed_check_ids": [
                check.get("id")
                for check in readiness_ledger.get("missing_failed_checks", [])
                if check.get("id")
            ],
        },
        "review_packet": {
            "current_stage": control_plane.get("lab_scorecard", {}).get(
                "readiness_stage", "unknown"
            ),
            "active_mission_state": control_plane.get("active_mission", {}).get("state"),
            "promotion_decision": control_plane.get("claim_lifecycle", {}).get(
                "promotion_decision"
            ),
            "allowed_outputs": control_plane.get("claim_lifecycle", {}).get(
                "allowed_outputs", []
            ),
        },
        "research_only": True,
    }


def _export_status(promotion_ready: bool, gaps: list[dict[str, Any]]) -> str:
    if promotion_ready:
        return "ready_for_reviewed_research_packet"
    if gaps:
        return "ready_for_research_review"
    return "ready_for_archive_review"
