"""Append-only readiness ledger summaries from recorded readiness artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


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
    return {
        "sequence": sequence,
        "artifact": name,
        "status": artifact.get("status", payload.get("status", "unknown")),
        "source_ref": artifact.get("path"),
        "recorded_at": artifact.get("recorded_at") or payload.get("recorded_at"),
        "hypothesis_id": payload.get("hypothesis_id"),
        "mode": payload.get("mode", "research_readiness"),
        "sample_count": _sample_count(payload),
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


def _int_value(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return max(parsed, 0)
