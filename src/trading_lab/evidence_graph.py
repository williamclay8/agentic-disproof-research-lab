"""Stable evidence graph built from the claim/run registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from trading_lab.claim_registry import (
    ClaimRunRegistry,
    GateEvidenceRecord,
    RunRecord,
    RESEARCH_BOUNDARY,
    SCHEMA_VERSION,
)


@dataclass(frozen=True)
class EvidenceNode:
    id: str
    kind: str
    label: str
    source_refs: list[str]
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "source_refs": self.source_refs,
            "attributes": self.attributes,
        }


@dataclass(frozen=True)
class EvidenceEdge:
    source: str
    target: str
    relationship: str
    source_refs: list[str]

    def to_payload(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
            "source_refs": self.source_refs,
        }


@dataclass(frozen=True)
class EvidenceGraph:
    nodes: list[EvidenceNode]
    edges: list[EvidenceEdge]
    schema_version: int = SCHEMA_VERSION
    mode: str = "research_only"
    boundary: str = RESEARCH_BOUNDARY

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "boundary": self.boundary,
            "nodes": [node.to_payload() for node in self.nodes],
            "edges": [edge.to_payload() for edge in self.edges],
        }


def build_evidence_graph(registry: ClaimRunRegistry) -> EvidenceGraph:
    """Build graph nodes and edges with artifact source references."""

    nodes: dict[str, EvidenceNode] = {}
    edges: list[EvidenceEdge] = []

    for claim in registry.claims:
        claim_node_id = f"claim:{claim.claim_id}"
        nodes[claim_node_id] = EvidenceNode(
            id=claim_node_id,
            kind="claim",
            label=claim.claim_id,
            source_refs=[claim.source_ref],
            attributes={
                "status": claim.status,
                "latest_run_id": claim.latest_run_id,
                "latest_verdict": claim.latest_verdict,
                "open_gate_count": len(claim.open_gate_names),
                "artifact_hash": claim.artifact_hash,
                "research_only": True,
            },
        )

    for run in registry.runs:
        _add_run_nodes(nodes, edges, run)

    return EvidenceGraph(
        nodes=[nodes[node_id] for node_id in sorted(nodes)],
        edges=sorted(edges, key=lambda edge: (edge.source, edge.target, edge.relationship)),
    )


def _add_run_nodes(
    nodes: dict[str, EvidenceNode],
    edges: list[EvidenceEdge],
    run: RunRecord,
) -> None:
    claim_node_id = f"claim:{run.claim_id}"
    run_node_id = f"run:{run.run_id}"
    dataset_node_id = f"dataset:{run.dataset_hash}"

    nodes.setdefault(
        claim_node_id,
        EvidenceNode(
            id=claim_node_id,
            kind="unregistered_claim",
            label=run.claim_id,
            source_refs=[run.source_ref],
            attributes={"registered": False, "research_only": True},
        ),
    )
    nodes[run_node_id] = EvidenceNode(
        id=run_node_id,
        kind="run",
        label=run.run_id,
        source_refs=[run.source_ref],
        attributes={
            "claim_id": run.claim_id,
            "verdict": run.verdict,
            "disproof_score": run.disproof_score,
            "gate_counts": run.gate_counts,
            "artifact_hash": run.artifact_hash,
            "result_fingerprint": run.result_fingerprint,
            "research_only": True,
        },
    )
    _merge_node(
        nodes,
        EvidenceNode(
            id=dataset_node_id,
            kind="dataset",
            label=run.dataset_hash,
            source_refs=[run.source_ref],
            attributes={"dataset_hash": run.dataset_hash},
        ),
    )
    edges.append(
        EvidenceEdge(
            source=claim_node_id,
            target=run_node_id,
            relationship="tested_by",
            source_refs=[run.source_ref],
        )
    )
    edges.append(
        EvidenceEdge(
            source=run_node_id,
            target=dataset_node_id,
            relationship="uses_dataset",
            source_refs=[run.source_ref],
        )
    )

    for gate in run.gate_evidence:
        _add_gate_node(nodes, edges, run, gate, claim_node_id, run_node_id)


def _add_gate_node(
    nodes: dict[str, EvidenceNode],
    edges: list[EvidenceEdge],
    run: RunRecord,
    gate: GateEvidenceRecord,
    claim_node_id: str,
    run_node_id: str,
) -> None:
    nodes[gate.gate_id] = EvidenceNode(
        id=gate.gate_id,
        kind="gate",
        label=gate.name,
        source_refs=[gate.source_ref],
        attributes={
            "claim_id": run.claim_id,
            "run_id": run.run_id,
            "status": gate.status,
            "severity": gate.severity,
            "threshold": gate.threshold,
            "evidence_path": gate.evidence_path,
            "evidence_digest": gate.evidence_digest,
            "research_only": True,
        },
    )
    edges.append(
        EvidenceEdge(
            source=run_node_id,
            target=gate.gate_id,
            relationship="records_gate",
            source_refs=[gate.source_ref],
        )
    )
    edges.append(
        EvidenceEdge(
            source=gate.gate_id,
            target=claim_node_id,
            relationship="challenges_claim",
            source_refs=[gate.source_ref],
        )
    )


def _merge_node(nodes: dict[str, EvidenceNode], node: EvidenceNode) -> None:
    existing = nodes.get(node.id)
    if existing is None:
        nodes[node.id] = node
        return

    source_refs = sorted(set(existing.source_refs) | set(node.source_refs))
    attributes = {**existing.attributes, **node.attributes}
    nodes[node.id] = EvidenceNode(
        id=existing.id,
        kind=existing.kind,
        label=existing.label,
        source_refs=source_refs,
        attributes=attributes,
    )
