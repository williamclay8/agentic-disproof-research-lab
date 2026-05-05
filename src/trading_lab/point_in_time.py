"""Point-in-time contracts derived from recorded research evidence."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from trading_lab.artifacts import ResearchRunArtifact


AS_OF_POLICY = "known-at-time inputs only"


def build_point_in_time_contract(
    artifact: ResearchRunArtifact,
    *,
    evidence_summary: Mapping[str, Any] | Any,
    source_ref: str,
) -> dict[str, Any]:
    """Build a field-level point-in-time review contract from evidence summary."""

    summary = _mapping(evidence_summary)
    allowed = _string_set(summary.get("allowed_fields"))
    leakage = _string_set(summary.get("leakage_suspect_fields"))
    unknown = _string_set(summary.get("unknown_lineage_fields"))
    columns = sorted(
        set(artifact.manifest.columns) | allowed | leakage | unknown,
        key=lambda value: value.lower(),
    )
    gaps = [_gap(gap, source_ref) for gap in _string_list(summary.get("evidence_gaps"))]

    return {
        "mode": "research_only",
        "contract_schema": "point_in_time_contract.v1",
        "claim_id": artifact.hypothesis.id,
        "run_id": artifact.run_id,
        "status": "needs_review" if gaps else "ready",
        "as_of_policy": AS_OF_POLICY,
        "source_refs": {
            "run": source_ref,
            "dataset": artifact.manifest.source,
            "dataset_hash": artifact.manifest.content_hash,
        },
        "fields": [
            _field_row(
                name=column,
                allowed=allowed,
                leakage=leakage,
                unknown=unknown,
                artifact=artifact,
                source_ref=source_ref,
            )
            for column in columns
        ],
        "gaps": gaps,
        "review_roles": ["Leak Auditor", "Baseline Challenger"],
    }


def _field_row(
    *,
    name: str,
    allowed: set[str],
    leakage: set[str],
    unknown: set[str],
    artifact: ResearchRunArtifact,
    source_ref: str,
) -> dict[str, Any]:
    status = "allowed"
    owner = "Leak Auditor"
    review_required = False
    if name in leakage:
        status = "leakage_suspect"
        review_required = True
    elif name in unknown:
        status = "unknown_lineage"
        review_required = True
    elif name not in allowed:
        status = "unknown_lineage"
        review_required = True

    return {
        "name": name,
        "status": status,
        "as_of_policy": AS_OF_POLICY,
        "owner": owner,
        "review_required": review_required,
        "source_ref": source_ref,
        "dataset_source": artifact.manifest.source,
        "evidence_path": _field_evidence_path(name, artifact),
    }


def _gap(gap_id: str, source_ref: str) -> dict[str, Any]:
    kind, _, subject = gap_id.partition(":")
    return {
        "id": gap_id,
        "kind": kind or "evidence_gap",
        "subject": subject,
        "status": "open",
        "owner": _owner_for_gap(gap_id),
        "source_ref": source_ref,
        "evidence_path": f"evidence_rigor.summary.evidence_gaps.{_slug(gap_id)}",
        "review_required": True,
    }


def _owner_for_gap(gap_id: str) -> str:
    if gap_id.startswith("missing_baseline"):
        return "Baseline Challenger"
    if gap_id.startswith(("leakage_suspect", "unknown_lineage")):
        return "Leak Auditor"
    return "Reproducibility Clerk"


def _field_evidence_path(name: str, artifact: ResearchRunArtifact) -> str:
    if name in artifact.manifest.columns:
        return f"manifest.columns.{_slug(name)}"
    return f"evidence_rigor.summary.fields.{_slug(name)}"


def _mapping(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return dict(value)


def _string_set(value: Any) -> set[str]:
    return set(_string_list(value))


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _slug(value: str) -> str:
    text = str(value).lower().replace(":", "-").replace("_", "-")
    chars = [char if char.isalnum() else "-" for char in text]
    return "-".join(part for part in "".join(chars).split("-") if part)
