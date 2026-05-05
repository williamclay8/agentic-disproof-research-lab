"""Durable claim/run registry derived from local research artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from trading_lab.artifacts import ResearchRunArtifact, read_run_artifact
from trading_lab.models import GateResult, Hypothesis
from trading_lab.registry import load_hypothesis


SCHEMA_VERSION = 1
RESEARCH_BOUNDARY = "offline research falsification only"


@dataclass(frozen=True)
class GateEvidenceRecord:
    gate_id: str
    name: str
    status: str
    severity: str
    threshold: str
    evidence_digest: str
    evidence_path: str
    source_ref: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "name": self.name,
            "status": self.status,
            "severity": self.severity,
            "threshold": self.threshold,
            "evidence_digest": self.evidence_digest,
            "evidence_path": self.evidence_path,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    thesis: str
    null_hypothesis: str
    status: str
    registered_at: str
    source_ref: str
    artifact_hash: str
    run_ids: list[str]
    latest_run_id: str | None
    latest_verdict: str | None
    open_gate_names: list[str]

    def to_payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "thesis": self.thesis,
            "null_hypothesis": self.null_hypothesis,
            "status": self.status,
            "registered_at": self.registered_at,
            "source_ref": self.source_ref,
            "artifact_hash": self.artifact_hash,
            "run_ids": self.run_ids,
            "latest_run_id": self.latest_run_id,
            "latest_verdict": self.latest_verdict,
            "open_gate_names": self.open_gate_names,
            "research_only": True,
        }


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    claim_id: str
    verdict: str
    source_ref: str
    artifact_hash: str
    dataset_hash: str
    result_fingerprint: str
    disproof_score: int
    gate_counts: dict[str, int]
    open_gate_names: list[str]
    gate_evidence: list[GateEvidenceRecord]

    def to_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "claim_id": self.claim_id,
            "verdict": self.verdict,
            "source_ref": self.source_ref,
            "artifact_hash": self.artifact_hash,
            "dataset_hash": self.dataset_hash,
            "result_fingerprint": self.result_fingerprint,
            "disproof_score": self.disproof_score,
            "gate_counts": self.gate_counts,
            "open_gate_names": self.open_gate_names,
            "gate_evidence": [gate.to_payload() for gate in self.gate_evidence],
            "research_only": True,
        }


@dataclass(frozen=True)
class RegistryIssue:
    kind: str
    claim_id: str
    run_id: str
    source_ref: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "claim_id": self.claim_id,
            "run_id": self.run_id,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True)
class ClaimRunRegistry:
    claims: list[ClaimRecord]
    runs: list[RunRecord]
    issues: list[RegistryIssue]
    schema_version: int = SCHEMA_VERSION
    mode: str = "research_only"
    boundary: str = RESEARCH_BOUNDARY

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "boundary": self.boundary,
            "claims": [claim.to_payload() for claim in self.claims],
            "runs": [run.to_payload() for run in self.runs],
            "issues": [issue.to_payload() for issue in self.issues],
        }


def build_claim_run_registry(
    hypotheses_path: str | Path,
    runs_path: str | Path,
    *,
    project_root: str | Path | None = None,
) -> ClaimRunRegistry:
    """Build a deterministic registry from pre-registration and run artifacts."""

    root = Path(project_root).resolve() if project_root is not None else None
    claim_stubs = _load_claim_stubs(Path(hypotheses_path), root)
    runs = _load_run_records(Path(runs_path), root)
    runs_by_claim: dict[str, list[RunRecord]] = {}
    for run in runs:
        runs_by_claim.setdefault(run.claim_id, []).append(run)

    claims: list[ClaimRecord] = []
    for claim in claim_stubs:
        claim_runs = sorted(runs_by_claim.get(claim.claim_id, []), key=_run_sort_key)
        latest = claim_runs[-1] if claim_runs else None
        claims.append(
            replace(
                claim,
                run_ids=[run.run_id for run in claim_runs],
                latest_run_id=latest.run_id if latest else None,
                latest_verdict=latest.verdict if latest else None,
                open_gate_names=latest.open_gate_names if latest else [],
            )
        )

    registered_claim_ids = {claim.claim_id for claim in claims}
    issues = [
        RegistryIssue(
            kind="unregistered_run_claim",
            claim_id=run.claim_id,
            run_id=run.run_id,
            source_ref=run.source_ref,
        )
        for run in runs
        if run.claim_id not in registered_claim_ids
    ]

    return ClaimRunRegistry(
        claims=sorted(claims, key=lambda claim: claim.claim_id),
        runs=sorted(runs, key=_run_sort_key),
        issues=sorted(issues, key=lambda issue: (issue.claim_id, issue.run_id)),
    )


def gate_record_id(run_id: str, gate_name: str) -> str:
    return f"gate:{run_id}:{slug(gate_name)}"


def slug(value: str) -> str:
    text = str(value).lower().replace(":", "-").replace("_", "-")
    chars = [char if char.isalnum() else "-" for char in text]
    return "-".join(part for part in "".join(chars).split("-") if part)


def _load_claim_stubs(path: Path, root: Path | None) -> list[ClaimRecord]:
    return [_claim_stub(file_path, root) for file_path in _json_files(path)]


def _claim_stub(path: Path, root: Path | None) -> ClaimRecord:
    payload = json.loads(path.read_text(encoding="utf-8"))
    hypothesis = load_hypothesis(path)
    return _claim_record(
        hypothesis,
        status=str(payload.get("status", "active")),
        registered_at=str(payload.get("registered_at", "")),
        source_ref=_source_ref(path, root),
        artifact_hash=_artifact_hash(path),
    )


def _claim_record(
    hypothesis: Hypothesis,
    *,
    status: str,
    registered_at: str,
    source_ref: str,
    artifact_hash: str,
) -> ClaimRecord:
    return ClaimRecord(
        claim_id=hypothesis.id,
        thesis=hypothesis.thesis,
        null_hypothesis=hypothesis.null_hypothesis,
        status=status,
        registered_at=registered_at,
        source_ref=source_ref,
        artifact_hash=artifact_hash,
        run_ids=[],
        latest_run_id=None,
        latest_verdict=None,
        open_gate_names=[],
    )


def _load_run_records(path: Path, root: Path | None) -> list[RunRecord]:
    records: list[RunRecord] = []
    for file_path in _json_files(path):
        if not _is_run_artifact(file_path):
            continue
        artifact = read_run_artifact(file_path)
        records.append(_run_record(artifact, file_path, root))
    return records


def _run_record(
    artifact: ResearchRunArtifact,
    path: Path,
    root: Path | None,
) -> RunRecord:
    source_ref = _source_ref(path, root)
    return RunRecord(
        run_id=artifact.run_id,
        claim_id=artifact.hypothesis.id,
        verdict=artifact.verdict,
        source_ref=source_ref,
        artifact_hash=_artifact_hash(path),
        dataset_hash=artifact.manifest.content_hash,
        result_fingerprint=artifact.result.fingerprint,
        disproof_score=artifact.disproof_score,
        gate_counts=_gate_counts(artifact.gate_results),
        open_gate_names=[
            gate.gate_name for gate in artifact.gate_results if gate.status != "pass"
        ],
        gate_evidence=[
            _gate_evidence_record(artifact.run_id, gate, source_ref)
            for gate in artifact.gate_results
        ],
    )


def _gate_evidence_record(
    run_id: str,
    gate: GateResult,
    source_ref: str,
) -> GateEvidenceRecord:
    return GateEvidenceRecord(
        gate_id=gate_record_id(run_id, gate.gate_name),
        name=gate.gate_name,
        status=gate.status,
        severity=gate.severity,
        threshold=gate.threshold,
        evidence_digest=_json_digest(gate.evidence),
        evidence_path=f"gate_results.{slug(gate.gate_name)}",
        source_ref=source_ref,
    )


def _gate_counts(gates: list[GateResult]) -> dict[str, int]:
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for gate in gates:
        counts[gate.status] += 1
    return counts


def _json_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(file_path for file_path in path.rglob("*.json") if file_path.is_file())
    return [path]


def _is_run_artifact(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return (
        payload.get("schema_version") == SCHEMA_VERSION
        and isinstance(payload.get("run_id"), str)
        and isinstance(payload.get("hypothesis"), dict)
        and isinstance(payload.get("gate_results"), list)
    )


def _artifact_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_ref(path: Path, root: Path | None) -> str:
    resolved = path.resolve()
    if root is not None:
        try:
            return resolved.relative_to(root).as_posix()
        except ValueError:
            pass
    return path.as_posix()


def _run_sort_key(run: RunRecord) -> tuple[str, str]:
    return (run.source_ref, run.run_id)
