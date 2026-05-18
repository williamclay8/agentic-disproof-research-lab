"""Readiness validation for research-only promotion artifacts."""

from __future__ import annotations

from typing import Any


MIN_SAMPLE_COUNT = 30


def validate_readiness(
    *,
    paper_ledger: dict[str, Any],
    live_shadow_drift: dict[str, Any],
    calibration_history: dict[str, Any],
    risk_packet: dict[str, Any],
) -> dict[str, Any]:
    """Validate readiness artifacts without producing execution guidance."""

    artifacts = {
        "paper_ledger": paper_ledger,
        "live_shadow_drift": live_shadow_drift,
        "calibration_history": calibration_history,
        "risk_packet": risk_packet,
    }
    artifact_present = {
        name: _artifact_present(payload) for name, payload in artifacts.items()
    }
    completed_checks: list[str] = []
    missing_failed_checks: list[dict[str, str]] = []

    for name, present in artifact_present.items():
        check_id = f"{name}_artifact_present"
        if present:
            completed_checks.append(check_id)
        else:
            missing_failed_checks.append(
                _failed(check_id, _label(name, "artifact present"), "Artifact payload is missing.")
            )

    _validate_paper_ledger(paper_ledger, completed_checks, missing_failed_checks)
    _validate_live_shadow_drift(live_shadow_drift, completed_checks, missing_failed_checks)
    _validate_calibration_history(
        calibration_history, completed_checks, missing_failed_checks
    )
    _validate_risk_packet(risk_packet, completed_checks, missing_failed_checks)

    required = {
        "paper_ledger_promotion_ready",
        "live_shadow_drift_promotion_ready",
        "calibration_history_promotion_ready",
        "risk_packet_promotion_ready",
        "risk_packet_human_review",
    }
    completed = set(completed_checks)
    promotion_ready = required.issubset(completed)

    return {
        "artifact_present": artifact_present,
        "completed_checks": completed_checks,
        "missing_failed_checks": missing_failed_checks,
        "promotion_ready": promotion_ready,
        "promotion_verdict": _promotion_verdict(promotion_ready, missing_failed_checks),
    }


def _validate_paper_ledger(
    payload: dict[str, Any],
    completed: list[str],
    missing_failed: list[dict[str, str]],
) -> None:
    if not _artifact_present(payload):
        return
    if _is_append_only(payload):
        completed.append("paper_ledger_append_only")
    sample_count = _sample_count(payload)
    if sample_count >= MIN_SAMPLE_COUNT:
        completed.append("paper_ledger_sample_count")
        completed.append("paper_ledger_promotion_ready")
        return
    if _has_limitation(payload):
        completed.append("paper_ledger_limitation_acknowledged")
    missing_failed.append(
        _failed(
            "paper_ledger_sample_count",
            "Paper ledger sample count",
            f"Paper ledger has {sample_count} samples; {MIN_SAMPLE_COUNT} are required for promotion readiness.",
        )
    )


def _validate_live_shadow_drift(
    payload: dict[str, Any],
    completed: list[str],
    missing_failed: list[dict[str, str]],
) -> None:
    if not _artifact_present(payload):
        return
    if _is_append_only(payload):
        completed.append("live_shadow_drift_append_only")
    has_metric = _has_drift_metric(payload)
    sample_count = _sample_count(payload)
    if has_metric:
        completed.append("live_shadow_drift_metric_present")
    else:
        missing_failed.append(
            _failed(
                "live_shadow_drift_metric",
                "Live-shadow drift metric",
                "Live-shadow artifact needs a measured drift field.",
            )
        )
    if sample_count >= MIN_SAMPLE_COUNT:
        completed.append("live_shadow_drift_sample_count")
    else:
        missing_failed.append(
            _failed(
                "live_shadow_drift_sample_count",
                "Live-shadow sample count",
                f"Live-shadow artifact has {sample_count} samples; {MIN_SAMPLE_COUNT} are required for promotion readiness.",
            )
        )
    if has_metric and sample_count >= MIN_SAMPLE_COUNT:
        completed.append("live_shadow_drift_promotion_ready")


def _validate_calibration_history(
    payload: dict[str, Any],
    completed: list[str],
    missing_failed: list[dict[str, str]],
) -> None:
    if not _artifact_present(payload):
        return
    if _is_append_only(payload):
        completed.append("calibration_history_append_only")
    has_metric = _has_calibration_metric(payload)
    sample_count = _sample_count(payload)
    if has_metric:
        completed.append("calibration_history_metric_present")
    else:
        missing_failed.append(
            _failed(
                "calibration_history_metric",
                "Calibration metric",
                "Calibration history needs a metric such as Brier score or calibration error.",
            )
        )
    if sample_count >= MIN_SAMPLE_COUNT:
        completed.append("calibration_history_sample_count")
    else:
        missing_failed.append(
            _failed(
                "calibration_history_sample_count",
                "Calibration sample count",
                f"Calibration history has {sample_count} samples; {MIN_SAMPLE_COUNT} are required for promotion readiness.",
            )
        )
    if has_metric and sample_count >= MIN_SAMPLE_COUNT:
        completed.append("calibration_history_promotion_ready")


def _validate_risk_packet(
    payload: dict[str, Any],
    completed: list[str],
    missing_failed: list[dict[str, str]],
) -> None:
    if not _artifact_present(payload):
        return
    if _is_append_only(payload):
        completed.append("risk_packet_append_only")
    has_invalidation = _has_invalidation_evidence(payload)
    has_controls = _has_risk_controls(payload)
    human_reviewed = _has_human_review(payload)
    if has_invalidation:
        completed.append("risk_packet_invalidation_present")
    else:
        missing_failed.append(
            _failed(
                "risk_packet_invalidation",
                "Risk packet invalidation",
                "Risk packet needs invalidation evidence for research display review.",
            )
        )
    if has_controls:
        completed.append("risk_packet_controls_present")
    else:
        missing_failed.append(
            _failed(
                "risk_packet_controls",
                "Risk packet controls",
                "Risk packet needs controls such as freshness expiry or drift review.",
            )
        )
    if human_reviewed:
        completed.append("risk_packet_human_review")
    else:
        missing_failed.append(
            _failed(
                "risk_packet_human_review",
                "Human review",
                "Human review must be recorded before promotion beyond research candidate.",
            )
        )
    if has_invalidation and has_controls and human_reviewed:
        completed.append("risk_packet_promotion_ready")


def _promotion_verdict(
    promotion_ready: bool, missing_failed_checks: list[dict[str, str]]
) -> dict[str, str]:
    if promotion_ready:
        return {
            "level": "human_reviewed_research_packet",
            "summary": "Promotion checks passed for a human-reviewed research packet; execution remains disabled.",
        }
    if missing_failed_checks:
        return {
            "level": "research_candidate",
            "summary": "Artifact evidence is incomplete for promotion; keep the packet in research review.",
        }
    return {
        "level": "research_candidate",
        "summary": "Artifact evidence remains in research review.",
    }


def _artifact_present(payload: dict[str, Any]) -> bool:
    return bool(payload)


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
        return sum(_int_value(bucket.get("sample_count")) for bucket in buckets if isinstance(bucket, dict))
    summary = payload.get("summary")
    if isinstance(summary, dict):
        return _int_value(summary.get("sample_count") or summary.get("hypothetical_setups_recorded"))
    return 0


def _has_limitation(payload: dict[str, Any]) -> bool:
    limits = payload.get("limits") or payload.get("limitations")
    return isinstance(limits, list) and any(str(limit).strip() for limit in limits)


def _has_drift_metric(payload: dict[str, Any]) -> bool:
    return any(_has_drift_metric_direct(candidate) for candidate in _payload_views(payload))


def _has_calibration_metric(payload: dict[str, Any]) -> bool:
    return any(
        _has_calibration_metric_direct(candidate) for candidate in _payload_views(payload)
    )


def _has_invalidation_evidence(payload: dict[str, Any]) -> bool:
    return any(
        bool(candidate.get("invalidation_evidence") or candidate.get("invalidation"))
        for candidate in _payload_views(payload)
    )


def _has_risk_controls(payload: dict[str, Any]) -> bool:
    return any(
        bool(candidate.get("risk_controls") or candidate.get("friction_context"))
        for candidate in _payload_views(payload)
    )


def _has_human_review(payload: dict[str, Any]) -> bool:
    return any(_human_review_recorded(candidate) for candidate in _payload_views(payload))


def _is_append_only(payload: dict[str, Any]) -> bool:
    return payload.get("write_policy") == "append_only" or payload.get("append_only") is True


def _has_drift_metric_direct(payload: dict[str, Any]) -> bool:
    drift = payload.get("drift") or payload.get("measured_drift")
    if isinstance(drift, dict) and any(_is_number(value) for value in drift.values()):
        return True
    metrics = payload.get("metrics")
    if isinstance(metrics, dict) and any(_is_number(value) for value in metrics.values()):
        return True
    return _is_number(payload.get("drift_metric"))


def _has_calibration_metric_direct(payload: dict[str, Any]) -> bool:
    metric_names = (
        "brier_score",
        "expected_calibration_error",
        "calibration_error",
        "log_loss",
    )
    if any(_is_number(payload.get(name)) for name in metric_names):
        return True
    buckets = payload.get("buckets")
    return isinstance(buckets, list) and any(
        isinstance(bucket, dict)
        and _is_number(bucket.get("predicted_probability"))
        and _is_number(bucket.get("realized_frequency"))
        for bucket in buckets
    )


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


def _human_review_recorded(payload: dict[str, Any]) -> bool:
    review = payload.get("human_review")
    if review is True:
        return True
    if not isinstance(review, dict):
        return False
    reviewer = review.get("reviewed_by") or review.get("reviewer") or review.get("approved_by")
    reviewed_at = review.get("reviewed_at") or review.get("approved_at")
    return bool(reviewer and reviewed_at)


def _int_value(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return max(parsed, 0)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _failed(check_id: str, label: str, detail: str) -> dict[str, str]:
    return {
        "id": check_id,
        "label": label,
        "status": "missing_or_failed",
        "detail": detail,
    }


def _label(artifact_name: str, suffix: str) -> str:
    return f"{artifact_name.replace('_', ' ').title()} {suffix}"
