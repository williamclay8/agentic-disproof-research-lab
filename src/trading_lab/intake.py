"""Validate-only strategy intake previews for research claims."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


SUPPORTED_STRATEGY_SOURCES = [
    "plain_language_claim",
    "csv_backtest",
    "pine_script",
    "lean_algorithm",
    "notebook_summary",
]

BLOCKED_IMPORT_FIELDS = [
    "broker",
    "account",
    "api_key",
    "secret",
    "order",
    "position_size",
    "entry",
    "exit",
    "live_signal",
]

REQUIRED_FIELDS = [
    "thesis",
    "null_hypothesis",
    "asset_universe",
    "time_horizon",
    "signal_definition",
    "data_requirements",
]


def build_strategy_import_preview(
    *,
    source_type: str,
    raw_text: str,
    source_ref: str = "manual:intake",
) -> dict[str, Any]:
    """Convert untrusted strategy text into a quarantined research draft."""

    normalized_source = str(source_type or "").strip()
    text = _clean(raw_text)
    if normalized_source not in SUPPORTED_STRATEGY_SOURCES:
        return {
            "mode": "research_only",
            "status": "unsupported_source_type",
            "promotion_allowed": False,
            "source_type": normalized_source or "unknown",
            "supported_sources": list(SUPPORTED_STRATEGY_SOURCES),
            "source_refs": [source_ref],
        }
    if not text:
        return {
            "mode": "research_only",
            "status": "missing_source_text",
            "promotion_allowed": False,
            "source_type": normalized_source,
            "supported_sources": list(SUPPORTED_STRATEGY_SOURCES),
            "source_refs": [source_ref],
            "missing_fields": list(REQUIRED_FIELDS),
            "candidate_claim": _empty_claim(),
            "first_falsification_tasks": [_required_fields_task(source_ref)],
            "next_action": {
                "label": "Add research claim text",
                "why": "The lab needs a thesis, null hypothesis, universe, horizon, signal, and data reference before review.",
            },
        }

    fields = _extract_fields(text)
    blocked_terms = _blocked_terms(text)
    claim = _candidate_claim(fields, text)
    missing_fields = _missing_fields(claim)
    tasks = _falsification_tasks(source_ref)
    if blocked_terms:
        tasks = [_boundary_scrub_task(source_ref, blocked_terms)] + tasks
    elif missing_fields:
        tasks = [_required_fields_task(source_ref)] + tasks

    status = "quarantine_until_evidence_exists"
    if blocked_terms:
        status = "blocked_by_execution_terms"
    elif missing_fields:
        status = "needs_required_fields"

    return {
        "mode": "research_only",
        "preview_schema": "strategy_import_preview.v1",
        "status": status,
        "promotion_allowed": False,
        "source_type": normalized_source,
        "supported_sources": list(SUPPORTED_STRATEGY_SOURCES),
        "draft_id": _draft_id(normalized_source, text),
        "source_refs": [source_ref],
        "candidate_claim": claim,
        "missing_fields": missing_fields,
        "blocked_terms": blocked_terms,
        "blocked_fields": list(BLOCKED_IMPORT_FIELDS),
        "first_falsification_tasks": tasks,
        "next_action": _next_action(status, missing_fields),
        "intake_policy": (
            "Validate only: no files are written, no claim is promoted, and no "
            "market action is exposed from intake text."
        ),
    }


def _extract_fields(text: str) -> dict[str, str]:
    return {
        "thesis": _extract_label(text, "Thesis") or _first_sentence(text),
        "null_hypothesis": _extract_label(text, "Null"),
        "asset_universe": _extract_label(text, "Universe"),
        "time_horizon": _extract_label(text, "Horizon"),
        "signal_definition": _extract_label(text, "Signal"),
        "data_requirements": _extract_label(text, "Data"),
        "baseline": _extract_label(text, "Baseline"),
    }


def _candidate_claim(fields: dict[str, str], text: str) -> dict[str, Any]:
    thesis = fields.get("thesis", "")
    null_hypothesis = fields.get("null_hypothesis", "")
    universe = _asset_universe(fields.get("asset_universe") or text)
    data = fields.get("data_requirements", "")
    return {
        "claim_id": f"draft-{_slug(thesis)[:72]}",
        "thesis": thesis,
        "null_hypothesis": null_hypothesis,
        "asset_universe": universe,
        "time_horizon": fields.get("time_horizon", ""),
        "signal_definition": fields.get("signal_definition", ""),
        "expected_failure_modes": [
            "point-in-time leakage",
            "weak comparator",
            "walk-forward fragility",
            "cost and slippage fragility",
            "insufficient paper or shadow evidence",
        ],
        "falsification_tests": [
            "point-in-time contract",
            "baseline comparison",
            "walk-forward robustness",
            "cost stress",
            "reproducibility",
            "readiness ledger",
        ],
        "pre_registered_metrics": [
            "strategy_cumulative_return",
            "baseline_cumulative_return",
            "max_drawdown",
            "turnover",
            "total_cost",
        ],
        "acceptance_thresholds": {
            "baseline_comparison": "strategy_cumulative_return > same-sample baseline",
            "walk_forward": "majority of chronological folds beat the comparator",
            "cost_stress": "edge survives a predeclared fee, slippage, and delay grid",
        },
        "data_requirements": [data] if data else [],
        "baseline_hint": fields.get("baseline", ""),
        "posthoc_edit_policy": "Do not edit the claim or thresholds after observing results.",
    }


def _missing_fields(claim: dict[str, Any]) -> list[str]:
    missing = []
    for field in REQUIRED_FIELDS:
        value = claim.get(field)
        if isinstance(value, list):
            is_missing = not value
        else:
            is_missing = not str(value or "").strip()
        if is_missing:
            missing.append(field)
    return missing


def _falsification_tasks(source_ref: str) -> list[dict[str, Any]]:
    return [
        _task(
            "point-in-time-pack",
            "Leak Auditor",
            "Prove every field was known at the tested timestamp.",
            "point_in_time_contract",
            source_ref,
        ),
        _task(
            "baseline-pack",
            "Baseline Challenger",
            "Compare against boring same-sample baselines before interpreting edge.",
            "baseline_pack_result",
            source_ref,
        ),
        _task(
            "walk-forward-pack",
            "Regime Skeptic",
            "Run chronological folds and mark fold-fragile claims early.",
            "walk_forward_fold_ledger",
            source_ref,
        ),
        _task(
            "cost-stress-pack",
            "Cost Stress Critic",
            "Stress fees, slippage, and delay before the claim earns attention.",
            "cost_grid_result",
            source_ref,
        ),
        _task(
            "readiness-pack",
            "Promotion Gatekeeper",
            "Keep the claim out of promotion until paper, shadow, calibration, risk, and human review proof exist.",
            "readiness_evidence_record",
            source_ref,
        ),
    ]


def _boundary_scrub_task(source_ref: str, blocked_terms: list[str]) -> dict[str, Any]:
    task = _task(
        "boundary-scrub-pack",
        "Promotion Gatekeeper",
        "Remove execution, account, credential, and action-language before research intake.",
        "boundary_scrub_note",
        source_ref,
    )
    task["blocked_terms"] = blocked_terms
    return task


def _required_fields_task(source_ref: str) -> dict[str, Any]:
    return _task(
        "required-fields-pack",
        "Reproducibility Clerk",
        "Capture thesis, null, universe, horizon, signal, and source data requirements.",
        "pre_registered_claim_draft",
        source_ref,
    )


def _task(
    pack_id: str,
    owner: str,
    label: str,
    expected_artifact: str,
    source_ref: str,
) -> dict[str, Any]:
    return {
        "pack_id": pack_id,
        "owner": owner,
        "label": label,
        "expected_artifact": expected_artifact,
        "status": "open",
        "source_ref": source_ref,
        "research_only": True,
    }


def _next_action(status: str, missing_fields: list[str]) -> dict[str, str]:
    if status == "blocked_by_execution_terms":
        return {
            "label": "Scrub boundary violations",
            "why": "The draft mentions prohibited execution, account, credential, or action surfaces.",
        }
    if missing_fields:
        return {
            "label": "Complete research draft",
            "why": f"Missing required fields: {', '.join(missing_fields)}.",
        }
    return {
        "label": "Create offline evidence packet",
        "why": "The draft is structured enough to run point-in-time, baseline, fold, cost, and readiness checks.",
    }


def _extract_label(text: str, label: str) -> str:
    labels = "Thesis|Null|Universe|Horizon|Signal|Data|Baseline"
    pattern = rf"\b{label}\s*:\s*(.*?)(?=\s+\b(?:{labels})\s*:|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return ""
    return _remove_blocked_sentences(_strip_sentence(match.group(1)))


def _first_sentence(text: str) -> str:
    sentence = re.split(r"[.!?]", text, maxsplit=1)[0]
    return _remove_blocked_sentences(_strip_sentence(sentence))


def _asset_universe(value: str) -> list[str]:
    candidates = re.findall(r"\b[A-Z]{1,6}(?:/[A-Z]{2,6})?\b", value)
    ignored = {"CSV", "OHLCV", "API", "KEY", "NULL", "DATA"}
    universe = []
    for candidate in candidates:
        if candidate in ignored:
            continue
        if candidate not in universe:
            universe.append(candidate)
    return universe[:12]


def _blocked_terms(text: str) -> list[str]:
    normalized = text.lower().replace("-", "_")
    patterns = {
        "broker": ("broker",),
        "account": ("account",),
        "api_key": ("api key", "api_key"),
        "secret": ("secret", "credential"),
        "order": ("order",),
        "position_size": ("position size", "position_size", "sizing"),
        "entry": ("entry",),
        "exit": ("exit",),
        "live_signal": ("live signal", "live_signal"),
    }
    found = [
        label
        for label, needles in patterns.items()
        if any(needle in normalized for needle in needles)
    ]
    return [field for field in BLOCKED_IMPORT_FIELDS if field in found]


def _remove_blocked_sentences(value: str) -> str:
    pieces = [
        piece.strip()
        for piece in re.split(r"(?<=[.!?])\s+", str(value or ""))
        if piece.strip()
    ]
    safe = [piece for piece in pieces if not _blocked_terms(piece)]
    return _strip_sentence(" ".join(safe))


def _draft_id(source_type: str, text: str) -> str:
    digest = hashlib.sha256(
        json.dumps(
            {"source_type": source_type, "text": text},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return f"intake:{digest[:16]}"


def _empty_claim() -> dict[str, Any]:
    return {
        "claim_id": "draft-empty",
        "thesis": "",
        "null_hypothesis": "",
        "asset_universe": [],
        "time_horizon": "",
        "signal_definition": "",
        "expected_failure_modes": [],
        "falsification_tests": [],
        "pre_registered_metrics": [],
        "acceptance_thresholds": {},
        "data_requirements": [],
        "posthoc_edit_policy": "",
    }


def _clean(value: str) -> str:
    return " ".join(str(value or "").split())


def _strip_sentence(value: str) -> str:
    return str(value or "").strip().strip(".; ")


def _slug(value: str) -> str:
    text = str(value).lower().replace("/", "-").replace("_", "-")
    chars = [char if char.isalnum() else "-" for char in text]
    return "-".join(part for part in "".join(chars).split("-") if part) or "untitled"
