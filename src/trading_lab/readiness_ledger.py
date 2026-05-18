"""Append-only readiness ledger summaries from recorded readiness artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


ARTIFACT_TYPES = {
    "paper_ledger": "paper_observation_ledger",
    "live_shadow_drift": "live_shadow_drift_monitor",
    "calibration_history": "calibration_history",
    "risk_packet": "risk_control_packet",
}

ARTIFACT_OWNERS = {
    "paper_ledger": "Promotion Gatekeeper",
    "live_shadow_drift": "Regime Skeptic",
    "calibration_history": "Promotion Gatekeeper",
    "risk_packet": "Promotion Gatekeeper",
}


def summarize_readiness_ledger(
    readiness_artifacts: dict[str, Any],
    *,
    validation: dict[str, Any],
) -> dict[str, Any]:
    """Summarize existing readiness artifacts without mutating their records."""

    entries = [
        _entry(sequence, name, artifact)
        for sequence, (name, artifact) in enumerate(
            sorted(
                readiness_artifacts.items(),
                key=lambda item: (
                    str(item[1].get("recorded_at", "")),
                    item[0],
                ),
            ),
            start=1,
        )
    ]
    return {
        "mode": "research_only",
        "ledger_schema": "readiness_ledger.v1",
        "ledger_id": _ledger_id(entries),
        "write_policy": "append_only",
        "entry_count": len(entries),
        "next_sequence": len(entries) + 1,
        "promotion_ready": bool(validation.get("promotion_ready")),
        "promotion_verdict": validation.get("promotion_verdict", {}),
        "completed_checks": list(validation.get("completed_checks", [])),
        "missing_failed_checks": list(validation.get("missing_failed_checks", [])),
        "entries": entries,
    }


def _entry(sequence: int, name: str, artifact: dict[str, Any]) -> dict[str, Any]:
    payload = artifact.get("payload", {})
    source_ref = artifact.get("path")
    return {
        "sequence": sequence,
        "artifact": name,
        "artifact_type": ARTIFACT_TYPES.get(name, "readiness_artifact"),
        "owned_by": ARTIFACT_OWNERS.get(name, "Promotion Gatekeeper"),
        "status": artifact.get("status", payload.get("status", "unknown")),
        "source_ref": source_ref,
        "source_refs": _source_refs(artifact, payload, source_ref),
        "recorded_at": artifact.get("recorded_at") or payload.get("recorded_at"),
        "hypothesis_id": payload.get("hypothesis_id"),
        "mode": payload.get("mode", "research_readiness"),
        "write_policy": payload.get("write_policy", artifact.get("write_policy")),
        "append_only": _is_append_only(payload),
        "sample_count": _sample_count(payload),
        "measured_metrics": _measured_metrics(payload),
        "risk_controls_present": _has_risk_controls(payload),
        "human_review_recorded": _has_human_review(payload),
        "record_hash": _stable_hash(payload),
        "schema_version": payload.get("schema_version"),
        "limit_count": len(payload.get("limits", []))
        if isinstance(payload.get("limits"), list)
        else 0,
    }


def _ledger_id(entries: list[dict[str, Any]]) -> str:
    digest = _stable_hash(
        [
            {
                "sequence": entry["sequence"],
                "artifact": entry["artifact"],
                "record_hash": entry["record_hash"],
            }
            for entry in entries
        ]
    )
    return f"readiness-ledger-{digest[:16]}"


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sample_count(payload: dict[str, Any]) -> int:
    direct = _int_value(payload.get("sample_count"))
    if direct:
        return direct
    entries = payload.get("entries")
    if isinstance(entries, list):
        total = sum(
            _sample_count(_entry_payload(entry))
            for entry in entries
            if isinstance(entry, dict)
        )
        if total:
            return total
    buckets = payload.get("buckets")
    if isinstance(buckets, list):
        return sum(
            _int_value(bucket.get("sample_count"))
            for bucket in buckets
            if isinstance(bucket, dict)
        )
    summary = payload.get("summary")
    if isinstance(summary, dict):
        return _int_value(
            summary.get("sample_count") or summary.get("hypothetical_setups_recorded")
        )
    return 0


def _source_refs(
    artifact: dict[str, Any],
    payload: dict[str, Any],
    source_ref: str | None,
) -> list[str]:
    refs: list[str] = []
    if source_ref:
        refs.append(source_ref)
    artifact_refs = artifact.get("source_refs")
    if isinstance(artifact_refs, list):
        refs.extend(str(ref) for ref in artifact_refs if str(ref).strip())
    payload_refs = payload.get("source_refs")
    if isinstance(payload_refs, list):
        refs.extend(str(ref) for ref in payload_refs if str(ref).strip())
    direct = payload.get("source_ref")
    if isinstance(direct, str) and direct.strip():
        refs.append(direct)
    return _dedupe(refs)


def _measured_metrics(payload: dict[str, Any]) -> list[str]:
    metrics: set[str] = set()
    for candidate in _payload_views(payload):
        for key in (
            "brier_score",
            "expected_calibration_error",
            "calibration_error",
            "log_loss",
            "drift_metric",
        ):
            if _is_number(candidate.get(key)):
                metrics.add(key)
        for nested_key in ("drift", "measured_drift", "metrics"):
            nested = candidate.get(nested_key)
            if isinstance(nested, dict):
                metrics.update(
                    key for key, value in nested.items() if _is_number(value)
                )
        buckets = candidate.get("buckets")
        if isinstance(buckets, list):
            for bucket in buckets:
                if not isinstance(bucket, dict):
                    continue
                if _is_number(bucket.get("predicted_probability")):
                    metrics.add("predicted_probability")
                if _is_number(bucket.get("realized_frequency")):
                    metrics.add("realized_frequency")
    return sorted(metrics)


def _has_risk_controls(payload: dict[str, Any]) -> bool:
    return any(
        bool(candidate.get("risk_controls") or candidate.get("friction_context"))
        for candidate in _payload_views(payload)
    )


def _has_human_review(payload: dict[str, Any]) -> bool:
    for candidate in _payload_views(payload):
        review = candidate.get("human_review")
        if review is True:
            return True
        if not isinstance(review, dict):
            continue
        reviewer = (
            review.get("reviewed_by")
            or review.get("reviewer")
            or review.get("approved_by")
        )
        reviewed_at = review.get("reviewed_at") or review.get("approved_at")
        if reviewer and reviewed_at:
            return True
    return False


def _is_append_only(payload: dict[str, Any]) -> bool:
    return payload.get("write_policy") == "append_only" or payload.get("append_only") is True


def _payload_views(payload: dict[str, Any]) -> list[dict[str, Any]]:
    views = [payload]
    entries = payload.get("entries")
    if isinstance(entries, list):
        views.extend(
            _entry_payload(entry) for entry in entries if isinstance(entry, dict)
        )
    return views


def _entry_payload(entry: dict[str, Any]) -> dict[str, Any]:
    nested = entry.get("payload")
    if not isinstance(nested, dict):
        return entry
    return {
        **nested,
        **{key: value for key, value in entry.items() if key != "payload"},
    }


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _int_value(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return max(parsed, 0)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
