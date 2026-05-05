"""Falsification pack views derived from gates, gaps, and tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trading_lab.artifacts import ResearchRunArtifact


@dataclass(frozen=True)
class _PackDefinition:
    pack_id: str
    label: str
    owner: str
    expected_artifact: str
    terms: tuple[str, ...]


PACK_DEFINITIONS = (
    _PackDefinition(
        pack_id="baseline-pack",
        label="Baseline comparator pack",
        owner="Baseline Challenger",
        expected_artifact="baseline_pack_result",
        terms=("baseline", "comparator", "random-control", "equal-weight", "momentum", "reversion"),
    ),
    _PackDefinition(
        pack_id="point-in-time-pack",
        label="Point-in-time lineage pack",
        owner="Leak Auditor",
        expected_artifact="point_in_time_lineage_note",
        terms=("lookahead", "chronology", "schema", "leakage", "lineage", "future", "target"),
    ),
    _PackDefinition(
        pack_id="walk-forward-pack",
        label="Walk-forward regime pack",
        owner="Regime Skeptic",
        expected_artifact="walk_forward_fold_ledger",
        terms=("walk-forward", "fold", "regime", "parameter"),
    ),
    _PackDefinition(
        pack_id="cost-stress-pack",
        label="Cost stress pack",
        owner="Cost Stress Critic",
        expected_artifact="cost_stress_grid",
        terms=("cost", "slippage", "delay", "friction"),
    ),
    _PackDefinition(
        pack_id="reproducibility-pack",
        label="Reproducibility pack",
        owner="Reproducibility Clerk",
        expected_artifact="reproducibility_record",
        terms=("reproducibility", "fingerprint", "manifest"),
    ),
    _PackDefinition(
        pack_id="readiness-pack",
        label="Readiness evidence pack",
        owner="Promotion Gatekeeper",
        expected_artifact="readiness_evidence_record",
        terms=("readiness", "paper", "shadow", "calibration", "risk", "human-review"),
    ),
)


def build_falsification_engine(
    artifact: ResearchRunArtifact,
    *,
    evidence_gaps: list[dict[str, Any]],
    control_plane_tasks: list[dict[str, Any]],
    source_ref: str,
) -> dict[str, Any]:
    """Group existing gaps and tasks into deterministic falsification packs."""

    return {
        "mode": "research_only",
        "engine_schema": "falsification_engine.v1",
        "claim_id": artifact.hypothesis.id,
        "run_id": artifact.run_id,
        "source_ref": source_ref,
        "packs": [
            _pack(definition, artifact, evidence_gaps, control_plane_tasks, source_ref)
            for definition in PACK_DEFINITIONS
        ],
        "tasks": [_task_view(task) for task in control_plane_tasks],
    }


def _pack(
    definition: _PackDefinition,
    artifact: ResearchRunArtifact,
    evidence_gaps: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    source_ref: str,
) -> dict[str, Any]:
    related_gates = [
        gate for gate in artifact.gate_results if _matches(definition, gate.gate_name)
    ]
    related_gaps = [gap for gap in evidence_gaps if _gap_matches(definition, gap)]
    related_tasks = [task for task in tasks if _task_matches(definition, task)]
    open_gate_names = [
        gate.gate_name for gate in related_gates if gate.status != "pass"
    ]
    status = "open" if related_gaps or open_gate_names else "recorded"

    return {
        "pack_id": definition.pack_id,
        "label": definition.label,
        "owner": definition.owner,
        "status": status,
        "claim_id": artifact.hypothesis.id,
        "source_refs": sorted(
            {source_ref, *[str(gap.get("source_ref", source_ref)) for gap in related_gaps]}
        ),
        "gate_names": [gate.gate_name for gate in related_gates],
        "open_gate_names": open_gate_names,
        "gap_ids": [str(gap["id"]) for gap in related_gaps],
        "task_ids": [str(task["task_id"]) for task in related_tasks],
        "expected_artifacts": [definition.expected_artifact],
        "acceptance_tests": sorted(
            {
                *[
                    str(gap.get("acceptance_test"))
                    for gap in related_gaps
                    if gap.get("acceptance_test")
                ],
                *[gate.threshold for gate in related_gates],
            }
        ),
        "research_only": True,
    }


def _task_view(task: dict[str, Any]) -> dict[str, Any]:
    allowed_keys = (
        "task_id",
        "priority",
        "owner",
        "claim_id",
        "label",
        "kind",
        "status",
        "source",
        "gap_ids",
        "expected_artifact",
        "completion_criteria",
        "source_ref",
        "research_only",
    )
    return {key: task[key] for key in allowed_keys if key in task}


def _gap_matches(definition: _PackDefinition, gap: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(gap.get(key, ""))
        for key in ("id", "kind", "category", "required_artifact", "detail", "acceptance_test")
    )
    return _matches(definition, haystack)


def _task_matches(definition: _PackDefinition, task: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(task.get(key, ""))
        for key in ("task_id", "label", "source", "expected_artifact")
    )
    return _matches(definition, haystack) or bool(
        set(task.get("gap_ids", []))
        & {
            str(gap_id)
            for gap_id in task.get("gap_ids", [])
            if any(term in str(gap_id).lower() for term in definition.terms)
        }
    )


def _matches(definition: _PackDefinition, value: str) -> bool:
    normalized = str(value).lower().replace("_", "-")
    return any(term in normalized for term in definition.terms)
