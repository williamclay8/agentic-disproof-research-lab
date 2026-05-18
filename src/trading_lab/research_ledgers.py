"""Artifact-backed research ledgers for claim disproof workflows."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping

from trading_lab.artifacts import ResearchRunArtifact
from trading_lab.evidence import REQUIRED_BASELINES
from trading_lab.metrics import cumulative_return
from trading_lab.point_in_time import build_point_in_time_contract


RESEARCH_BOUNDARY = (
    "research-only falsification evidence; no advice, account, credential, "
    "allocation, order, or execution surface"
)


def build_baseline_pack_ledger(
    artifact: ResearchRunArtifact,
    *,
    rows: list[dict[str, Any]],
    source_ref: str,
) -> dict[str, Any]:
    """Build same-sample baseline evidence for every required comparator."""

    strategy_return = _float_metric(
        artifact.result.metrics.get("strategy_cumulative_return")
    )
    baseline_returns = _baseline_returns(artifact, rows)
    entries = [
        _baseline_entry(
            artifact,
            name=name,
            cumulative=baseline_returns[name],
            strategy_return=strategy_return,
            source_ref=source_ref,
        )
        for name in REQUIRED_BASELINES
    ]
    strongest = max(entries, key=lambda entry: entry["cumulative_return"])
    return {
        "mode": "research_only",
        "ledger_schema": "baseline_pack_ledger.v1",
        "claim_id": artifact.hypothesis.id,
        "run_id": artifact.run_id,
        "boundary": RESEARCH_BOUNDARY,
        "source_refs": {
            "run": source_ref,
            "dataset": artifact.manifest.source,
            "dataset_hash": artifact.manifest.content_hash,
        },
        "summary": {
            "required_baselines": list(REQUIRED_BASELINES),
            "recorded_baselines": [entry["name"] for entry in entries],
            "missing_baselines": [],
            "strategy_cumulative_return": strategy_return,
            "strongest_baseline": strongest["name"],
            "strongest_baseline_return": strongest["cumulative_return"],
            "status": (
                "baseline_challenge_open"
                if any(entry["delta_vs_strategy"] <= 0 for entry in entries)
                else "strategy_above_recorded_baselines"
            ),
        },
        "entries": entries,
        "research_only": True,
    }


def build_walk_forward_ledger(
    artifact: ResearchRunArtifact,
    *,
    source_ref: str,
) -> dict[str, Any]:
    """Turn walk-forward gate evidence into an auditable fold ledger."""

    gate = _gate_by_name(artifact, "walk-forward robustness")
    evidence = dict(gate.evidence if gate else {})
    fold_metrics = [
        fold for fold in evidence.get("fold_metrics", []) if isinstance(fold, dict)
    ]
    folds = [
        _fold_row(artifact, fold=fold, source_ref=source_ref)
        for fold in sorted(fold_metrics, key=lambda item: int(item.get("fold", 0)))
    ]
    passing = sum(1 for fold in folds if fold["passed"])
    total = len(folds)
    pass_ratio = (passing / total) if total else 0.0
    return {
        "mode": "research_only",
        "ledger_schema": "walk_forward_ledger.v1",
        "claim_id": artifact.hypothesis.id,
        "run_id": artifact.run_id,
        "boundary": RESEARCH_BOUNDARY,
        "source_ref": source_ref,
        "summary": {
            "folds": total,
            "passing_folds": passing,
            "pass_ratio": pass_ratio,
            "status": (
                "blocked_by_fold_fragility"
                if gate and gate.status != "pass"
                else "fold_evidence_recorded"
            ),
            "gate_status": gate.status if gate else "missing",
            "threshold": gate.threshold if gate else "walk-forward evidence required",
            "primary_failure_reason": (
                gate.remediation_hint
                if gate and gate.status != "pass"
                else "No fold blocker recorded."
            ),
        },
        "folds": folds,
        "research_only": True,
    }


def build_point_in_time_proof(
    artifact: ResearchRunArtifact,
    *,
    evidence_summary: Mapping[str, Any] | Any,
    snapshot: dict[str, Any] | None,
    source_ref: str,
) -> dict[str, Any]:
    """Enrich field contracts with source timestamps and known-at-time proof."""

    contract = build_point_in_time_contract(
        artifact,
        evidence_summary=evidence_summary,
        source_ref=source_ref,
    )
    metadata = (snapshot or {}).get("metadata", {})
    source_timestamp = metadata.get("source_timestamp") or "unavailable"
    provenance = metadata.get("provenance") if isinstance(metadata, dict) else {}
    source_note = (
        provenance.get("source_ref")
        if isinstance(provenance, dict)
        else None
    ) or artifact.manifest.source
    fields = [
        {
            **field,
            "source_timestamp": source_timestamp,
            "known_at_time_proof": _known_at_time_proof(field),
            "vendor_or_source_ref": source_note,
        }
        for field in contract.get("fields", [])
    ]
    escalations = [
        {
            **gap,
            "escalation_policy": "block promotion until source timing is reviewed",
        }
        for gap in contract.get("gaps", [])
    ]
    return {
        "mode": "research_only",
        "proof_schema": "point_in_time_proof.v1",
        "claim_id": artifact.hypothesis.id,
        "run_id": artifact.run_id,
        "status": contract.get("status", "needs_review"),
        "boundary": RESEARCH_BOUNDARY,
        "as_of_policy": contract.get("as_of_policy", "known-at-time inputs only"),
        "source_timestamp": source_timestamp,
        "vendor_or_source_ref": source_note,
        "source_refs": contract.get("source_refs", {}),
        "fields": fields,
        "unknown_lineage_escalations": escalations,
        "review_roles": contract.get("review_roles", ["Leak Auditor"]),
        "research_only": True,
    }


def build_failure_gallery(
    artifact: ResearchRunArtifact,
    *,
    baseline_ledger: dict[str, Any],
    walk_forward_ledger: dict[str, Any],
    source_ref: str,
) -> dict[str, Any]:
    """Make failed and warning evidence first-class product assets."""

    cards = [
        _failure_card(
            artifact,
            gate=gate,
            baseline_ledger=baseline_ledger,
            walk_forward_ledger=walk_forward_ledger,
            source_ref=source_ref,
        )
        for gate in artifact.gate_results
        if gate.status != "pass"
    ]
    return {
        "mode": "research_only",
        "gallery_schema": "failure_gallery.v1",
        "claim_id": artifact.hypothesis.id,
        "run_id": artifact.run_id,
        "boundary": RESEARCH_BOUNDARY,
        "summary": {
            "card_count": len(cards),
            "status": "failure_assets_recorded" if cards else "no_failures_recorded",
            "message": (
                "Failed and warning claims are preserved as learning assets."
            ),
        },
        "cards": cards,
        "research_only": True,
    }


def build_action_guidance(
    artifact: ResearchRunArtifact,
    *,
    readiness: dict[str, Any],
    baseline_ledger: dict[str, Any],
    walk_forward_ledger: dict[str, Any],
    source_ref: str,
) -> dict[str, Any]:
    """Return one obvious plain action plus expert evidence routes."""

    cards = build_failure_gallery(
        artifact,
        baseline_ledger=baseline_ledger,
        walk_forward_ledger=walk_forward_ledger,
        source_ref=source_ref,
    )["cards"]
    primary = cards[0] if cards else {}
    label = primary.get("next_research_action") or "Archive reviewed evidence packet"
    missing = readiness.get("missing_checks", [])
    return {
        "mode": "research_only",
        "guidance_schema": "action_guidance.v1",
        "claim_id": artifact.hypothesis.id,
        "run_id": artifact.run_id,
        "boundary": RESEARCH_BOUNDARY,
        "plain_next_action": {
            "label": label,
            "why": primary.get(
                "why_it_failed",
                "The lab needs stronger recorded evidence before trust increases.",
            ),
            "owner": primary.get("caught_by", "Reproducibility Clerk"),
            "source_ref": source_ref,
        },
        "expert_next_actions": [
            {
                "label": card["next_research_action"],
                "owner": card["caught_by"],
                "source_ref": card["source_ref"],
                "evidence_path": card["evidence_path"],
            }
            for card in cards
        ]
        or [
            {
                "label": "Design a harder falsification pass.",
                "owner": "Promotion Gatekeeper",
                "source_ref": source_ref,
                "evidence_path": "gate_results",
            }
        ],
        "would_change_our_mind": [
            check.get("label") or check.get("id")
            for check in missing[:4]
            if isinstance(check, dict)
        ],
        "blocked_outputs": [
            "personalized recommendation",
            "directional live call",
            "allocation guidance",
            "account route",
            "autonomous execution",
        ],
        "research_only": True,
    }


def _baseline_returns(
    artifact: ResearchRunArtifact,
    rows: list[dict[str, Any]],
) -> dict[str, float]:
    per_symbol = _close_returns_by_symbol(rows, artifact.spec.long_window)
    by_date = _returns_by_date(per_symbol)
    dates = sorted(by_date)
    buy_and_hold = _float_metric(
        artifact.result.metrics.get("baseline_cumulative_return")
    )
    equal_weight = cumulative_return(
        [_mean([item["return"] for item in by_date[date]]) for date in dates]
    )
    naive_momentum = cumulative_return(
        [_selected_return(by_date[date], reverse=True) for date in dates]
    )
    naive_reversion = cumulative_return(
        [_selected_return(by_date[date], reverse=False) for date in dates]
    )
    random_control = cumulative_return(
        [_seeded_return(by_date[date], artifact.manifest.content_hash, date) for date in dates]
    )
    return {
        "buy-and-hold": buy_and_hold,
        "equal-weight": equal_weight,
        "naive-momentum": naive_momentum,
        "naive-mean-reversion": naive_reversion,
        "random-control": random_control,
    }


def _baseline_entry(
    artifact: ResearchRunArtifact,
    *,
    name: str,
    cumulative: float,
    strategy_return: float,
    source_ref: str,
) -> dict[str, Any]:
    delta = strategy_return - cumulative
    return {
        "artifact_id": f"baseline:{artifact.run_id}:{name}",
        "name": name,
        "cumulative_return": cumulative,
        "strategy_cumulative_return": strategy_return,
        "delta_vs_strategy": delta,
        "status": (
            "baseline_challenges_claim"
            if delta <= 0
            else "strategy_above_baseline"
        ),
        "source_metric": (
            "result.metrics.baseline_cumulative_return"
            if name == "buy-and-hold"
            else f"derived_baseline_pack.{name}.cumulative_return"
        ),
        "seed": artifact.manifest.content_hash[:12] if name == "random-control" else None,
        "owner": "Baseline Challenger",
        "source_ref": source_ref,
        "research_only": True,
    }


def _close_returns_by_symbol(
    rows: list[dict[str, Any]],
    long_window: int,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["symbol"]), []).append(row)

    output: dict[str, list[dict[str, Any]]] = {}
    for symbol, symbol_rows in grouped.items():
        sorted_rows = sorted(symbol_rows, key=lambda row: row["date"])
        returns: list[dict[str, Any]] = []
        first_usable_index = long_window - 1
        for index in range(first_usable_index, len(sorted_rows)):
            close_return = (
                (sorted_rows[index]["close"] / sorted_rows[index - 1]["close"]) - 1.0
                if index > 0
                else 0.0
            )
            previous_return = (
                (sorted_rows[index - 1]["close"] / sorted_rows[index - 2]["close"]) - 1.0
                if index > 1
                else 0.0
            )
            returns.append(
                {
                    "date": sorted_rows[index]["date"],
                    "symbol": symbol,
                    "return": close_return,
                    "previous_return": previous_return,
                }
            )
        output[symbol] = returns
    return output


def _returns_by_date(
    per_symbol: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    by_date: dict[str, list[dict[str, Any]]] = {}
    for symbol_rows in per_symbol.values():
        for row in symbol_rows:
            by_date.setdefault(str(row["date"]), []).append(row)
    return by_date


def _selected_return(rows: list[dict[str, Any]], *, reverse: bool) -> float:
    selected = sorted(
        rows,
        key=lambda row: (float(row["previous_return"]), str(row["symbol"])),
        reverse=reverse,
    )[0]
    return float(selected["return"])


def _seeded_return(rows: list[dict[str, Any]], seed: str, date: str) -> float:
    ordered = sorted(rows, key=lambda row: str(row["symbol"]))
    digest = hashlib.sha256(f"{seed}:{date}".encode("utf-8")).hexdigest()
    index = int(digest[:8], 16) % len(ordered)
    return float(ordered[index]["return"])


def _fold_row(
    artifact: ResearchRunArtifact,
    *,
    fold: dict[str, Any],
    source_ref: str,
) -> dict[str, Any]:
    strategy = _float_metric(fold.get("strategy_cumulative_return"))
    baseline = _float_metric(fold.get("baseline_cumulative_return"))
    passed = strategy > baseline
    fold_number = int(fold.get("fold", 0))
    return {
        "fold_id": f"fold:{artifact.run_id}:{fold_number}",
        "fold": fold_number,
        "regime_label": f"chronological-window-{fold_number}",
        "train_window": {
            "start": fold.get("train_start"),
            "end": fold.get("train_end"),
        },
        "test_window": {
            "start": fold.get("test_start"),
            "end": fold.get("test_end"),
        },
        "strategy_cumulative_return": strategy,
        "baseline_cumulative_return": baseline,
        "delta_vs_baseline": strategy - baseline,
        "passed": passed,
        "primary_failure_reason": (
            "strategy did not beat the same-window baseline"
            if not passed
            else "fold beat the same-window baseline"
        ),
        "owner": "Regime Skeptic",
        "source_ref": source_ref,
        "research_only": True,
    }


def _failure_card(
    artifact: ResearchRunArtifact,
    *,
    gate,
    baseline_ledger: dict[str, Any],
    walk_forward_ledger: dict[str, Any],
    source_ref: str,
) -> dict[str, Any]:
    owner = _owner_for_gate(gate.gate_name)
    return {
        "card_id": f"failure:{artifact.run_id}:{_slug(gate.gate_name)}",
        "claim_id": artifact.hypothesis.id,
        "gate_name": gate.gate_name,
        "status": gate.status,
        "severity": gate.severity,
        "caught_by": owner,
        "what_failed": gate.remediation_hint,
        "why_it_failed": _why_failed(gate, baseline_ledger, walk_forward_ledger),
        "what_would_change_our_mind": _change_mind(gate),
        "next_research_action": f"Retest {gate.gate_name} against stricter offline evidence.",
        "evidence_path": f"gate_results.{_slug(gate.gate_name)}",
        "source_ref": source_ref,
        "research_only": True,
    }


def _why_failed(
    gate,
    baseline_ledger: dict[str, Any],
    walk_forward_ledger: dict[str, Any],
) -> str:
    if gate.gate_name == "baseline comparison":
        strongest = baseline_ledger.get("summary", {}).get("strongest_baseline", "baseline")
        return f"The claim is weaker than at least one same-sample baseline: {strongest}."
    if gate.gate_name == "walk-forward robustness":
        summary = walk_forward_ledger.get("summary", {})
        return (
            f"Only {summary.get('passing_folds', 0)} of "
            f"{summary.get('folds', 0)} chronological folds beat baseline."
        )
    return gate.remediation_hint


def _change_mind(gate) -> list[str]:
    if gate.gate_name == "baseline comparison":
        return [
            "record all required baseline comparators",
            "show strategy return above every same-sample baseline",
        ]
    if gate.gate_name == "walk-forward robustness":
        return [
            "record more chronological folds",
            "show a majority of folds beating the comparator",
        ]
    return [gate.threshold]


def _known_at_time_proof(field: dict[str, Any]) -> str:
    if field.get("review_required"):
        return "blocked_until_reviewed"
    return "manifest_field_known_at_dataset_timestamp"


def _owner_for_gate(gate_name: str) -> str:
    normalized = gate_name.lower()
    if any(term in normalized for term in ("lookahead", "chronology", "schema")):
        return "Leak Auditor"
    if "baseline" in normalized:
        return "Baseline Challenger"
    if any(term in normalized for term in ("cost", "slippage", "delay")):
        return "Cost Stress Critic"
    if any(term in normalized for term in ("walk-forward", "parameter", "regime")):
        return "Regime Skeptic"
    if "reproduc" in normalized or "fingerprint" in normalized:
        return "Reproducibility Clerk"
    return "Promotion Gatekeeper"


def _gate_by_name(artifact: ResearchRunArtifact, gate_name: str):
    return next(
        (gate for gate in artifact.gate_results if gate.gate_name == gate_name),
        None,
    )


def _float_metric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def _mapping(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return dict(value)


def _slug(value: str) -> str:
    text = str(value).lower().replace(":", "-").replace("_", "-")
    chars = [char if char.isalnum() else "-" for char in text]
    return "-".join(part for part in "".join(chars).split("-") if part)
