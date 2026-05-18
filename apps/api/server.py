"""Tiny product API shell for the standalone Trading Lab.

This intentionally uses the standard library for the first local product lane
so the research kernel stays runnable without adding framework dependencies.
The documented production target is FastAPI once dependency management and
deployment are formalized.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from trading_lab.agents import build_agentic_review
from trading_lab.artifacts import read_run_artifact
from trading_lab.control_plane import build_lab_control_plane
from trading_lab.evidence import baseline_pack, summarize_evidence_rigor
from trading_lab.intake import build_strategy_import_preview
from trading_lab.platform import build_platform_overview
from trading_lab.readiness import validate_readiness
from trading_lab.snapshots import read_latest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5299
ALLOWED_WEB_ORIGINS = {
    "http://127.0.0.1:5199",
    "http://localhost:5199",
}
READINESS_ARTIFACTS = {
    "paper_ledger": PROJECT_ROOT / "runs" / "readiness" / "paper-ledger.json",
    "live_shadow_drift": PROJECT_ROOT / "runs" / "readiness" / "live-shadow-drift.json",
    "calibration_history": PROJECT_ROOT / "runs" / "readiness" / "calibration-history.json",
    "risk_packet": PROJECT_ROOT / "runs" / "readiness" / "risk-packet.json",
}
RESEARCH_DEVELOPMENT_FORBIDDEN_OUTPUTS = [
    "personalized recommendation",
    "directional live call",
    "position sizing guidance",
    "broker/account/order route",
    "autonomous execution",
]
RESEARCH_DEVELOPMENT_STEP_REQUIRED_FIELDS = [
    "id",
    "title",
    "status",
    "owner",
    "current_research_state",
    "visible_api_fields",
    "source_refs",
    "missing_proof",
    "next_safe_research_action",
]


def health_payload() -> dict[str, Any]:
    return {
        "service": "trading-lab-api",
        "status": "ok",
        "boundary": "standalone research lab",
        "execution": "disabled",
        "advice": "disabled",
    }


def run_payload(path: Path | None = None) -> dict[str, Any]:
    run_path = path or PROJECT_ROOT / "runs" / "example-run.json"
    artifact = read_run_artifact(run_path)
    gate_results = [
        {
            "name": gate.gate_name,
            "status": gate.status,
            "passed": gate.status == "pass",
            "detail": gate.remediation_hint,
            "severity": gate.severity,
            "threshold": gate.threshold,
            "evidence": gate.evidence,
        }
        for gate in artifact.gate_results
    ]
    return {
        "id": artifact.hypothesis.id,
        "thesis": artifact.hypothesis.thesis,
        "verdict": artifact.verdict,
        "disproof_score": artifact.disproof_score,
        "gate_counts": _gate_counts(gate_results),
        "blocking_gates": [gate for gate in gate_results if gate["status"] != "pass"],
        "gate_results": gate_results,
        "limitations": artifact.limitations,
        "next_tests": artifact.next_tests,
        "source": str(run_path.relative_to(PROJECT_ROOT)),
    }


def latest_snapshot_payload(path: Path | None = None) -> dict[str, Any]:
    snapshot_path = path or PROJECT_ROOT / "runs" / "live" / "latest.json"
    latest = read_latest(snapshot_path)
    events = [] if latest is None else [latest]
    return {
        "snapshot": str(snapshot_path.relative_to(PROJECT_ROOT)),
        "count": len(events),
        "boundary": "research observations only",
        "events": [
            _snapshot_event_payload(event)
            for event in events
        ],
    }


def product_release_rule_payload(
    *,
    run: dict[str, Any],
    readiness: dict[str, Any],
    blockers: list[str],
    control_plane: dict[str, Any],
    ranked_attention_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return the four answers every Trading Lab surface must expose."""

    lifecycle = control_plane.get("claim_lifecycle", {})
    gates = control_plane.get("gate_summaries", {}).get("weakest", [])
    weak_gate = gates[0] if gates else {}
    missing_checks = readiness.get("missing_checks", [])
    first_missing = missing_checks[0] if missing_checks else {}
    tasks = control_plane.get("next_falsification_tasks", [])
    first_task = tasks[0] if tasks else (ranked_attention_items[0] if ranked_attention_items else {})
    stage = readiness.get("current_stage", {}).get("label") or lifecycle.get("stage", "research-only hold")
    return {
        "current_research_state": (
            f"{stage}: verdict {run.get('verdict', 'unknown')} with "
            f"{len(blockers)} promotion blockers."
        ),
        "plain_english_meaning": (
            weak_gate.get("plain_english")
            or weak_gate.get("detail")
            or "The claim remains a research artifact until stronger evidence exists."
        ),
        "missing_proof": (
            first_missing.get("label")
            or first_missing.get("id")
            or weak_gate.get("name")
            or "No missing proof is exposed by the current packet."
        ),
        "next_safe_research_action": (
            "Research: "
            + (
                first_task.get("label")
                or first_task.get("why")
                or "Review the current evidence packet before increasing trust."
            )
        ),
        "blocked_actions": [
            "investment advice",
            "broker connection",
            "order routing",
            "live signal language",
            "personalized guidance",
            "position sizing",
        ],
    }


def claim_journey_payload(
    *,
    run: dict[str, Any],
    snapshot: dict[str, Any],
    readiness: dict[str, Any],
    blockers: list[str],
    control_plane: dict[str, Any],
    ranked_attention_items: list[dict[str, Any]],
    evidence_rigor: dict[str, Any],
) -> dict[str, Any]:
    """Return the six-step plain-to-pro claim journey."""

    gates = {gate.get("name"): gate for gate in run.get("gate_results", [])}
    baseline_gate = gates.get("baseline comparison", {})
    walk_gate = gates.get("walk-forward robustness", {})
    weak_gate = (control_plane.get("gate_summaries", {}).get("weakest") or [{}])[0]
    missing_checks = readiness.get("missing_checks", [])
    first_missing = missing_checks[0] if missing_checks else {}
    tasks = control_plane.get("next_falsification_tasks", [])
    first_task = tasks[0] if tasks else (ranked_attention_items[0] if ranked_attention_items else {})
    rigor_summary = evidence_rigor.get("summary", evidence_rigor)
    missing_baselines = rigor_summary.get("missing_baselines", [])
    current_stage = readiness.get("current_stage", {}).get("label", "research-only hold")
    source_ref = run.get("source", "runs/example-run.json")
    snapshot_ref = snapshot.get("snapshot", "runs/live/latest.json")

    def step(
        step_number: int,
        step_id: str,
        title: str,
        question: str,
        state: str,
        meaning: str,
        missing_proof: str,
        next_action: str,
        *,
        status: str = "warn",
        owner: str = "Promotion Gatekeeper",
        source: str | None = None,
    ) -> dict[str, Any]:
        return {
            "step_number": step_number,
            "id": step_id,
            "title": title,
            "question": question,
            "status": status,
            "owner": owner,
            "current_research_state": state,
            "plain_english_meaning": meaning,
            "missing_proof": missing_proof,
            "next_safe_research_action": f"Research: {next_action}",
            "source_ref": source or source_ref,
        }

    steps = [
        step(
            1,
            "what_are_we_testing",
            "What are we testing?",
            "What claim is under test?",
            f"{run.get('id', 'unknown')} is registered with verdict {run.get('verdict', 'unknown')}.",
            run.get("thesis", "The lab has no thesis text for this claim."),
            "The claim must keep a thesis, null hypothesis, dataset, and source artifact attached.",
            "keep the claim registered and inspect the baseline evidence before trust increases.",
            status="ok",
            owner="Reproducibility Clerk",
        ),
        step(
            2,
            "simple_baseline",
            "Can it beat a simple baseline?",
            "Did the idea beat a boring comparison?",
            f"Baseline comparison is {baseline_gate.get('status', 'unknown')}.",
            baseline_gate.get("detail", "Comparator evidence is not exposed."),
            ", ".join(missing_baselines) or baseline_gate.get("threshold", "Baseline evidence is required."),
            "rerun or inspect the baseline pack with same-sample comparators.",
            status=baseline_gate.get("status", "warn"),
            owner="Baseline Challenger",
        ),
        step(
            3,
            "fooling_risks",
            "What could be fooling us?",
            "Could leakage, costs, slippage, or regime fragility explain the result?",
            f"Weakest exposed gate is {weak_gate.get('name', 'unknown')}.",
            weak_gate.get("plain_english") or weak_gate.get("detail") or "The lab is still checking ways the result could be misleading.",
            walk_gate.get("detail") or "Leakage, cost, slippage, and regime checks must stay visible.",
            "inspect leakage, cost stress, slippage, and walk-forward evidence before adding trust.",
            status=weak_gate.get("status", "warn"),
            owner=weak_gate.get("owner", "Regime Skeptic"),
        ),
        step(
            4,
            "evidence_origin",
            "Where did this evidence come from?",
            "Can we trace the result to data, code, source refs, and hashes?",
            f"Evidence is anchored to {source_ref} and {snapshot_ref}.",
            "Every result should be explainable from artifacts, not dashboard copy.",
            "Run artifact, snapshot provenance, source timestamps, and hashes must remain available.",
            "open the ledger or provenance view when any result feels unclear.",
            status="ok",
            owner="Reproducibility Clerk",
            source=snapshot_ref,
        ),
        step(
            5,
            "research_readiness",
            "Is this ready for more research?",
            "Can the claim advance beyond the current research stage?",
            f"Current stage is {current_stage} with {len(blockers)} blockers.",
            "Promotion is blocked until evidence quality and human review requirements clear.",
            first_missing.get("label") or first_missing.get("id") or "No missing readiness check is exposed.",
            "clear the first missing readiness check before changing the claim state.",
            status="warn",
            owner="Promotion Gatekeeper",
        ),
        step(
            6,
            "next_research_test",
            "What should we test next?",
            "What is the next safe research action?",
            first_task.get("label", "No next task is exposed."),
            first_task.get("why") or "The next action must stay inside offline research.",
            first_task.get("expected_artifact") or first_task.get("source_ref") or "A source-referenced offline artifact is required.",
            first_task.get("label", "review the current evidence packet."),
            status=first_task.get("status", "warn"),
            owner=first_task.get("owner", "Promotion Gatekeeper"),
            source=first_task.get("source_ref", source_ref),
        ),
    ]
    return {
        "mode": "research_only",
        "boundary": "claim journey is research-only and not a trade instruction",
        "steps": steps,
    }


def research_development_pass_payload(
    *,
    platform: dict[str, Any] | None = None,
    agentic_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the eight-step R&D pass from existing product evidence."""

    if platform is None:
        return platform_payload()["research_development_pass"]

    engine = platform.get("falsification_engine", {})
    pit = platform.get("point_in_time_contract", {})
    contracts = platform.get("agent_contracts", [])
    readiness = platform.get("readiness_ledger", {})
    gallery = platform.get("failure_gallery", {})
    strategy_import = platform.get("strategy_import", {})
    strategy_preview = platform.get("strategy_import_preview", {})
    product_rule = platform.get("product_release_rule", {})
    claim_journey = platform.get("claim_journey", {})
    baseline_pack = _pack_by_id(engine, "baseline-pack")
    walk_forward_pack = _pack_by_id(engine, "walk-forward-pack")
    findings = (agentic_review or {}).get("findings", [])
    first_failure = (gallery.get("failed_or_blocked_claims") or [{}])[0]
    first_missing = (readiness.get("missing_checks") or [{}])[0]

    steps = [
        _research_development_step(
            1,
            "action_native_first_move",
            "Action-native first move",
            "ready",
            "Promotion Gatekeeper",
            "Validate-only intake is available as the first native action.",
            ["strategy_import", "strategy_import_preview", "first_falsification_tasks"],
            _source_refs(strategy_preview, "manual:intake:example"),
            "A quarantined draft still needs point-in-time, baseline, fold, cost, and readiness proof.",
            "Research: preview a quarantined research draft before adding it to the claim surface.",
            "ActionNativeFirstMove",
            source_payload="/strategy-import/preview",
            native_action={
                "label": "Preview Research Draft",
                "method": "POST",
                "route": "/strategy-import/preview",
                "default_state": strategy_import.get("intake_contract", {}).get(
                    "default_state",
                    "quarantine_until_evidence_exists",
                ),
                "creates": "quarantined_claim_draft",
                "research_only": True,
            },
        ),
        _research_development_step(
            2,
            "baseline_ledger",
            "Baseline ledger",
            baseline_pack.get("status", "open"),
            baseline_pack.get("owner", "Baseline Challenger"),
            f"baseline comparison pack is {baseline_pack.get('status', 'open')}.",
            ["baseline_pack", "packs", "queue", "missing_items", "required_artifacts"],
            _source_refs(baseline_pack, "runs/example-run.json"),
            _join_or_default(
                baseline_pack.get("missing_items"),
                "Same-sample boring comparators must be recorded.",
            ),
            "Research: rerun the baseline ledger with same-sample comparator artifacts.",
            "BaselineLedgerStep",
            source_payload="/falsification-engine/current",
            expected_artifacts=baseline_pack.get("required_artifacts", ["baseline_pack_result"]),
        ),
        _research_development_step(
            3,
            "walk_forward_ledger",
            "Walk-forward ledger",
            walk_forward_pack.get("status", "open"),
            walk_forward_pack.get("owner", "Regime Skeptic"),
            f"walk-forward robustness pack is {walk_forward_pack.get('status', 'open')}.",
            ["packs", "queue", "open_gate_names", "missing_items", "required_artifacts"],
            _source_refs(walk_forward_pack, "runs/example-run.json"),
            _join_or_default(
                walk_forward_pack.get("missing_items"),
                "Chronological fold evidence must be recorded.",
            ),
            "Research: record additional offline walk-forward folds and mark fold fragility.",
            "WalkForwardLedgerStep",
            source_payload="/falsification-engine/current",
            expected_artifacts=walk_forward_pack.get(
                "required_artifacts",
                ["walk_forward_fold_ledger"],
            ),
        ),
        _research_development_step(
            4,
            "point_in_time_proof",
            "Point-in-time proof",
            pit.get("status", "needs_review"),
            "Leak Auditor",
            f"Point-in-time contract is {pit.get('status', 'needs_review')}.",
            ["contract_schema", "allowed_fields", "fields", "gaps", "source_refs"],
            _source_refs(pit.get("source_refs", {}), "runs/example-run.json"),
            _join_or_default(
                [gap.get("id") for gap in pit.get("gaps", [])],
                "Known-at-time field lineage must stay source-referenced.",
            ),
            "Research: resolve open point-in-time gaps before trusting any field.",
            "PointInTimeProofStep",
            source_payload="/point-in-time-contract/current",
            contract_refs=[pit.get("contract_schema", "point_in_time_contract.v1")],
        ),
        _research_development_step(
            5,
            "agent_reviewer_artifacts",
            "Measurable agent reviewer artifacts",
            "open" if any(contract.get("open_finding_count", 0) for contract in contracts) else "ready",
            "Reproducibility Clerk",
            f"{sum(contract.get('open_finding_count', 0) for contract in contracts)} open reviewer findings are measurable.",
            ["agent_contracts", "open_finding_count", "required_output_fields", "source_refs"],
            _source_refs({"source_refs": [ref for contract in contracts for ref in contract.get("source_refs", [])]}, "runs/example-run.json"),
            _join_or_default(
                [finding.get("gate_name") for finding in findings if finding.get("status") != "pass"],
                "Agent findings must include status, severity, source refs, and next falsification step.",
            ),
            "Research: attach measurable reviewer findings to each owned evidence gap.",
            "AgentReviewerArtifactStep",
            source_payload="/agent-contracts",
            measurement_fields=["open_finding_count", "required_output_fields", "source_refs"],
        ),
        _research_development_step(
            6,
            "failure_gallery",
            "Failure gallery",
            "open" if gallery.get("failed_or_blocked_claims") else "ready",
            "Baseline Challenger",
            f"{len(gallery.get('failed_or_blocked_claims', []))} failed or blocked claims are visible.",
            ["failed_or_blocked_claims", "learning_value", "next_archive_action"],
            _source_refs(first_failure, "runs/example-run.json"),
            first_failure.get("primary_failure_reason", "No blocked claim failure reason is recorded."),
            "Research: archive the failure reason and reviewer notes as training memory.",
            "FailureGalleryStep",
            source_payload="/failure-gallery",
        ),
        _research_development_step(
            7,
            "readiness_evidence",
            "Readiness evidence",
            "blocked" if not readiness.get("promotion_ready") else "ready",
            "Promotion Gatekeeper",
            f"Readiness stage is {readiness.get('current_stage', {}).get('label', 'Observe-only')}.",
            ["append_only_entries", "sample_thresholds", "missing_checks", "source_refs"],
            _source_refs(readiness, "runs/example-run.json"),
            first_missing.get("label") or first_missing.get("id") or "Human review and sample thresholds must be recorded.",
            "Research: clear the first readiness blocker before changing product language.",
            "ReadinessEvidenceStep",
            source_payload="/readiness/ledger",
        ),
        _research_development_step(
            8,
            "hardened_response_schemas",
            "Hardened response schemas",
            "ready",
            "Reproducibility Clerk",
            "Release-rule, claim-journey, and R&D pass schemas are exposed in the response.",
            ["product_release_rule", "claim_journey", "research_development_pass", "response_schema"],
            _source_refs(product_rule, "packages/contracts/openapi/trading-lab.v0.yaml"),
            "OpenAPI schema fields must remain required before a surface is treated as shippable.",
            "Research: validate schema required fields before adding new release surfaces.",
            "HardenedResponseSchemaStep",
            source_payload="/platform/overview",
            schema_refs=[
                "ProductReleaseRule",
                "ClaimJourney",
                "ResearchDevelopmentPass",
                "ResearchDevelopmentStep",
            ],
            claim_journey_step_count=len(claim_journey.get("steps", [])),
        ),
    ]
    return {
        "mode": "research_only",
        "schema_version": "research_development_pass.v1",
        "boundary": "offline R&D evidence only; not a trade instruction",
        "steps": steps,
        "forbidden_outputs": RESEARCH_DEVELOPMENT_FORBIDDEN_OUTPUTS,
        "response_schema": {
            "name": "ResearchDevelopmentPass",
            "required_fields": [
                "mode",
                "schema_version",
                "boundary",
                "steps",
                "forbidden_outputs",
            ],
            "openapi_refs": [
                "ResearchDevelopmentPass",
                "ResearchDevelopmentStep",
            ],
        },
    }


def terminal_payload() -> dict[str, Any]:
    """Return the compact terminal view assembled from existing evidence only."""

    run = run_payload()
    snapshot = latest_snapshot_payload()
    event = snapshot["events"][0] if snapshot["events"] else {}
    quote = event.get("payload", {})
    metadata = event.get("metadata", {})
    gate_counts = _gate_counts(run["gate_results"])
    spread_bps = _spread_bps(quote)
    freshness = _freshness_label(metadata.get("source_timestamp"))
    blockers = _terminal_blockers(run, snapshot, spread_bps, freshness)
    ranked_attention_items = _focus_queue(run, snapshot, spread_bps, freshness)
    readiness = confidence_readiness_payload(run, snapshot, spread_bps, freshness)
    agentic_review = agentic_review_payload()
    evidence_rigor = evidence_rigor_payload()
    control_plane = control_plane_payload(
        run=run,
        snapshot=snapshot,
        spread_bps=spread_bps,
        freshness=freshness,
        blockers=blockers,
        readiness=readiness,
        agentic_review=agentic_review,
        evidence_rigor=evidence_rigor,
        ranked_attention_items=ranked_attention_items,
    )
    product_rule = product_release_rule_payload(
        run=run,
        readiness=readiness,
        blockers=blockers,
        control_plane=control_plane,
        ranked_attention_items=ranked_attention_items,
    )
    claim_journey = claim_journey_payload(
        run=run,
        snapshot=snapshot,
        readiness=readiness,
        blockers=blockers,
        control_plane=control_plane,
        ranked_attention_items=ranked_attention_items,
        evidence_rigor=evidence_rigor,
    )

    return {
        "mode": "research_only",
        "product_release_rule": product_rule,
        "claim_journey": claim_journey,
        "headline": _headline(run, event, freshness),
        "readiness_verdict": _readiness_verdict(run, snapshot, spread_bps, freshness, blockers),
        "market": {
            "symbol": quote.get("symbol", "unknown"),
            "venue": quote.get("venue", event.get("producer", "unknown")),
            "bid": quote.get("bid"),
            "ask": quote.get("ask"),
            "last": quote.get("last"),
            "mid": _mid_price(quote),
            "spread_abs": _spread_abs(quote),
            "spread_bps": spread_bps,
            "last_vs_mid": _last_vs_mid(quote),
            "last_location": _last_location(quote),
            "freshness": freshness,
            "source": metadata.get("source", event.get("producer", "unknown")),
            "source_timestamp": metadata.get("source_timestamp"),
            "license_note": metadata.get("license_note", "research data only"),
        },
        "snapshot_event": event,
        "evidence": {
            "run_id": run["id"],
            "verdict": run["verdict"],
            "disproof_score": run["disproof_score"],
            "gate_counts": gate_counts,
            "source": run["source"],
            "top_gates": _top_gates(run["gate_results"]),
        },
        "setup_visibility": _setup_visibility(run, snapshot, freshness, blockers),
        "evidence_passport": _evidence_passport(run),
        "agentic_review": agentic_review,
        "evidence_rigor": evidence_rigor,
        "ranked_attention_items": ranked_attention_items,
        "blockers": blockers,
        "confidence_readiness": readiness,
        "mission_control": control_plane,
        "human_brief": control_plane["human_brief"],
        "agent_mission_board": control_plane["agent_mission_board"],
        "claim_lifecycle": control_plane["claim_lifecycle"],
        "gate_summaries": control_plane["gate_summaries"],
        "evidence_gaps": control_plane["evidence_gaps"],
        "next_falsification_tasks": control_plane["next_falsification_tasks"],
        "lab_scorecard": control_plane["lab_scorecard"],
        "learning_loop": control_plane["learning_loop"],
        "noise_filters": [
            "Hide any setup without source timestamp, provider, and artifact ref.",
            "Collapse passed gates; show warnings and failures first.",
            "Show the next falsification task before any upside story.",
            "Do not display live guidance, sizing, entry, or execution prompts.",
        ],
    }


def platform_payload() -> dict[str, Any]:
    """Return the platform wedge payload assembled from existing evidence."""

    run = run_payload()
    snapshot = latest_snapshot_payload()
    event = snapshot["events"][0] if snapshot["events"] else {}
    quote = event.get("payload", {})
    metadata = event.get("metadata", {})
    spread_bps = _spread_bps(quote)
    freshness = _freshness_label(metadata.get("source_timestamp"))
    blockers = _terminal_blockers(run, snapshot, spread_bps, freshness)
    ranked_attention_items = _focus_queue(run, snapshot, spread_bps, freshness)
    readiness = confidence_readiness_payload(run, snapshot, spread_bps, freshness)
    agentic_review = agentic_review_payload()
    evidence_rigor = evidence_rigor_payload()
    control_plane = control_plane_payload(
        run=run,
        snapshot=snapshot,
        spread_bps=spread_bps,
        freshness=freshness,
        blockers=blockers,
        readiness=readiness,
        agentic_review=agentic_review,
        evidence_rigor=evidence_rigor,
        ranked_attention_items=ranked_attention_items,
    )
    artifact = read_run_artifact(PROJECT_ROOT / run["source"])
    payload = build_platform_overview(
        artifact,
        run=run,
        snapshot=snapshot,
        readiness=readiness,
        evidence_rigor=evidence_rigor,
        agentic_review=agentic_review,
        control_plane=control_plane,
    )
    payload["product_release_rule"] = product_release_rule_payload(
        run=run,
        readiness=readiness,
        blockers=blockers,
        control_plane=control_plane,
        ranked_attention_items=ranked_attention_items,
    )
    payload["claim_journey"] = claim_journey_payload(
        run=run,
        snapshot=snapshot,
        readiness=readiness,
        blockers=blockers,
        control_plane=control_plane,
        ranked_attention_items=ranked_attention_items,
        evidence_rigor=evidence_rigor,
    )
    payload["strategy_import_preview"] = strategy_import_preview_payload(
        {
            "source_type": "plain_language_claim",
            "raw_text": (
                "Thesis: BTC/USD daily momentum may beat buy-and-hold after costs. "
                "Null: no edge after costs. Universe: BTC/USD. Horizon: daily bars. "
                "Signal: close above 20 day high. Data: local OHLCV CSV."
            ),
            "source_ref": "manual:intake:example",
        }
    )
    payload["research_development_pass"] = research_development_pass_payload(
        platform=payload,
        agentic_review=agentic_review,
    )
    return payload


def claims_payload() -> dict[str, Any]:
    return platform_payload()["claim_registry"]


def claim_payload(claim_id: str) -> dict[str, Any]:
    platform = platform_payload()
    registry = platform["claim_registry"]
    claims = registry.get("claims", [])
    claim = next((item for item in claims if item.get("claim_id") == claim_id), None)
    if claim is None:
        return {
            "error": "claim_not_found",
            "claim_id": claim_id,
            "available_claim_ids": [item.get("claim_id") for item in claims],
        }
    return {
        "claim": claim,
        "runs": [
            run
            for run in registry.get("runs", [])
            if run.get("claim_id") == claim_id
        ],
        "trust_packet_ref": "/trust-packet/current",
    }


def strategy_import_preview_payload(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    return build_strategy_import_preview(
        source_type=str(payload.get("source_type", "plain_language_claim")),
        raw_text=str(payload.get("raw_text", "")),
        source_ref=str(payload.get("source_ref", "manual:intake")),
    )


def control_plane_payload(
    run: dict[str, Any] | None = None,
    snapshot: dict[str, Any] | None = None,
    spread_bps: float | None = None,
    freshness: dict[str, Any] | None = None,
    blockers: list[str] | None = None,
    readiness: dict[str, Any] | None = None,
    agentic_review: dict[str, Any] | None = None,
    evidence_rigor: dict[str, Any] | None = None,
    ranked_attention_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return the derived research lab control plane for the current packet."""

    run = run or run_payload()
    snapshot = snapshot or latest_snapshot_payload()
    event = snapshot["events"][0] if snapshot["events"] else {}
    quote = event.get("payload", {})
    metadata = event.get("metadata", {})
    if spread_bps is None:
        spread_bps = _spread_bps(quote)
    if freshness is None:
        freshness = _freshness_label(metadata.get("source_timestamp"))
    if blockers is None:
        blockers = _terminal_blockers(run, snapshot, spread_bps, freshness)
    readiness = readiness or confidence_readiness_payload(run, snapshot, spread_bps, freshness)
    agentic_review = agentic_review or agentic_review_payload()
    evidence_rigor = evidence_rigor or evidence_rigor_payload()
    ranked_attention_items = ranked_attention_items or _focus_queue(
        run,
        snapshot,
        spread_bps,
        freshness,
    )
    artifact = read_run_artifact(PROJECT_ROOT / run["source"])
    return build_lab_control_plane(
        artifact,
        run=run,
        snapshot=snapshot,
        readiness=readiness,
        evidence_rigor=evidence_rigor,
        agentic_review=agentic_review,
        blockers=blockers,
        ranked_attention_items=ranked_attention_items,
        spread_bps=spread_bps,
        freshness=freshness,
    )


def confidence_readiness_payload(
    run: dict[str, Any] | None = None,
    snapshot: dict[str, Any] | None = None,
    spread_bps: float | None = None,
    freshness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe what must exist before higher-confidence setup views are allowed."""

    run = run or run_payload()
    snapshot = snapshot or latest_snapshot_payload()
    artifacts = readiness_artifacts_payload()
    validation = readiness_validation_payload(artifacts)
    if freshness is None:
        event = snapshot["events"][0] if snapshot["events"] else {}
        freshness = _freshness_label(event.get("source_timestamp"))
    if spread_bps is None:
        event = snapshot["events"][0] if snapshot["events"] else {}
        spread_bps = _spread_bps(event.get("payload", {}))
    completed = _completed_readiness_checks(run, snapshot, spread_bps, freshness, artifacts)
    completed.update(validation["completed_checks"])
    stages = _confidence_stages()
    current_stage = _current_stage(stages, completed)
    missing = [
        check
        for check in _readiness_checks(run, snapshot, spread_bps, freshness, artifacts)
        if not check["passed"]
    ]
    missing.extend(validation["missing_failed_checks"])
    return {
        "current_stage": current_stage,
        "allowed_output": _allowed_output(current_stage),
        "not_allowed": [
            "personalized recommendations",
            "directional live calls",
            "position sizing guidance",
            "broker/account/order routes",
            "autonomous execution",
        ],
        "completed_checks": sorted(completed),
        "validation": validation,
        "readiness_artifacts": artifacts,
        "missing_checks": missing,
        "stages": stages,
        "display_rules": [
            "Show probability only after calibration evidence exists.",
            "Show setup readiness only with horizon, invalidation, expiry, and source refs.",
            "Show confidence as a measured label with Brier/calibration history, not persuasive copy.",
            "Degrade to observe-only when data freshness, drift, or execution assumptions fail.",
        ],
    }


def readiness_artifacts_payload() -> dict[str, Any]:
    return {
        name: _readiness_artifact(path)
        for name, path in READINESS_ARTIFACTS.items()
    }


def readiness_validation_payload(
    artifacts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifacts = artifacts or readiness_artifacts_payload()
    return validate_readiness(
        paper_ledger=artifacts.get("paper_ledger", {}).get("payload", {}),
        live_shadow_drift=artifacts.get("live_shadow_drift", {}).get("payload", {}),
        calibration_history=artifacts.get("calibration_history", {}).get("payload", {}),
        risk_packet=artifacts.get("risk_packet", {}).get("payload", {}),
    )


def agentic_review_payload(path: Path | None = None) -> dict[str, Any]:
    run_path = path or PROJECT_ROOT / "runs" / "example-run.json"
    artifact = read_run_artifact(run_path)
    review = build_agentic_review(
        artifact.gate_results,
        artifact.next_tests,
        artifact.limitations,
    )
    return {
        **review,
        "run_id": artifact.run_id,
        "source": str(run_path.relative_to(PROJECT_ROOT)),
    }


def evidence_rigor_payload(path: Path | None = None) -> dict[str, Any]:
    run_path = path or PROJECT_ROOT / "runs" / "example-run.json"
    artifact = read_run_artifact(run_path)
    summary = summarize_evidence_rigor(
        artifact.manifest.columns,
        baseline_names=["buy-and-hold"],
    )
    return {
        "run_id": artifact.run_id,
        "source": str(run_path.relative_to(PROJECT_ROOT)),
        "summary": asdict(summary),
        "baseline_pack": [
            asdict(descriptor) for descriptor in baseline_pack().values()
        ],
    }


def _readiness_verdict(
    run: dict[str, Any],
    snapshot: dict[str, Any],
    spread_bps: float | None,
    freshness: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    market_ready = (
        snapshot["count"] > 0
        and freshness["label"] == "fresh"
        and spread_bps is not None
    )
    setup_ready = (
        run["gate_counts"]["fail"] == 0
        and run["gate_counts"]["warn"] == 0
        and run["disproof_score"] == 0
    )
    action_ready = False
    if action_ready and setup_ready and market_ready:
        label = "Review-ready research packet"
        confidence = "research confidence only"
    elif market_ready and run["gate_counts"]["fail"] == 0:
        label = "Not live-signal ready"
        confidence = "medium: clean observation, evidence unresolved"
    else:
        label = "Not live-signal ready"
        confidence = "low: unresolved blockers"
    return {
        "label": label,
        "subline": (
            "Market observation may be available, but this terminal remains "
            "research-only until freshness, provenance, falsification, "
            "paper-ledger, live-shadow, calibration, and human-review checks clear."
        ),
        "confidence_label": confidence,
        "market_ready": market_ready,
        "setup_ready": setup_ready,
        "action_ready": action_ready,
        "blocker_count": len(blockers),
    }


def _setup_visibility(
    run: dict[str, Any],
    snapshot: dict[str, Any],
    freshness: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    stage = "hidden"
    allowed_to_display = False
    if snapshot["count"] > 0:
        stage = "observation_only"
        allowed_to_display = True
    if stage == "observation_only" and run["gate_counts"]["fail"] == 0:
        stage = "research_candidate"
    if stage == "research_candidate" and run["gate_counts"]["warn"] == 0:
        stage = "preliminary_survivor"
    return {
        "setup_id": run["id"],
        "symbol": _snapshot_symbol(snapshot),
        "setup_label": "claim under test",
        "visibility_stage": stage,
        "allowed_to_display": allowed_to_display,
        "blocking_reasons": blockers,
        "last_gate_reviewed_at": freshness.get("age_seconds"),
        "artifact_ref": run["source"],
        "snapshot_ref": snapshot["snapshot"],
    }


def _evidence_passport(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "registered_hypothesis_id": run["id"],
        "pre_registered_at": "local artifact",
        "dataset_hash": _first_evidence_value(run, "reproducibility", "dataset_hash"),
        "run_fingerprint": _first_evidence_value(run, "reproducibility", "first_fingerprint"),
        "verdict": run["verdict"],
        "disproof_score": run["disproof_score"],
        "gate_counts": run["gate_counts"],
        "open_warning_gates": [
            gate["name"] for gate in run["gate_results"] if gate["status"] == "warn"
        ],
        "open_failure_gates": [
            gate["name"] for gate in run["gate_results"] if gate["status"] == "fail"
        ],
    }


def _research_development_step(
    step_number: int,
    step_id: str,
    title: str,
    status: str,
    owner: str,
    current_research_state: str,
    visible_api_fields: list[str],
    source_refs: list[str],
    missing_proof: str,
    next_safe_research_action: str,
    schema_name: str,
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "step_number": step_number,
        "id": step_id,
        "title": title,
        "status": status if status in {"ready", "open", "blocked", "needs_review"} else "open",
        "owner": owner,
        "current_research_state": current_research_state,
        "visible_api_fields": visible_api_fields,
        "source_refs": source_refs or ["runs/example-run.json"],
        "missing_proof": missing_proof,
        "next_safe_research_action": next_safe_research_action,
        "response_schema": {
            "name": schema_name,
            "required_fields": RESEARCH_DEVELOPMENT_STEP_REQUIRED_FIELDS,
            "forbidden_outputs": RESEARCH_DEVELOPMENT_FORBIDDEN_OUTPUTS,
        },
    }
    payload.update(extra)
    return payload


def _pack_by_id(engine: dict[str, Any], pack_id: str) -> dict[str, Any]:
    return next(
        (pack for pack in engine.get("packs", []) if pack.get("pack_id") == pack_id),
        {},
    )


def _source_refs(payload: dict[str, Any], fallback: str) -> list[str]:
    values: list[Any] = []
    source_refs = payload.get("source_refs")
    if isinstance(source_refs, list):
        values.extend(source_refs)
    elif isinstance(source_refs, dict):
        values.extend(source_refs.values())
    for key in ("source_ref", "source", "path"):
        if payload.get(key):
            values.append(payload[key])
    refs = [str(value) for value in values if str(value).strip()]
    if fallback:
        refs.append(fallback)
    return list(dict.fromkeys(refs))


def _join_or_default(values: Any, default: str) -> str:
    if not isinstance(values, list):
        return default
    clean = [str(value) for value in values if str(value).strip()]
    return ", ".join(clean) if clean else default


class TradingLabHandler(BaseHTTPRequestHandler):
    server_version = "TradingLabAPI/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler convention
        route = urlparse(self.path).path.rstrip("/") or "/"
        try:
            if route == "/health":
                self._send_json(health_payload())
            elif route == "/runs/example":
                self._send_json(run_payload())
            elif route == "/snapshots/latest":
                self._send_json(latest_snapshot_payload())
            elif route == "/terminal":
                self._send_json(terminal_payload())
            elif route == "/terminal/overview":
                self._send_json(terminal_payload())
            elif route == "/control-plane/lab":
                self._send_json(control_plane_payload())
            elif route == "/platform/overview":
                self._send_json(platform_payload())
            elif route == "/claims":
                self._send_json(claims_payload())
            elif route.startswith("/claims/"):
                payload = claim_payload(route.split("/", 2)[2])
                self._send_json(payload, status=404 if "error" in payload else 200)
            elif route == "/evidence-graph/current":
                self._send_json(platform_payload()["evidence_graph"])
            elif route == "/point-in-time-contract/current":
                self._send_json(platform_payload()["point_in_time_contract"])
            elif route == "/falsification-engine/current":
                self._send_json(platform_payload()["falsification_engine"])
            elif route == "/agent-contracts":
                self._send_json({"agent_contracts": platform_payload()["agent_contracts"]})
            elif route == "/readiness/ledger":
                self._send_json(platform_payload()["readiness_ledger"])
            elif route == "/trust-packet/current":
                self._send_json(platform_payload()["trust_packet"])
            elif route == "/strategy-import/contract":
                self._send_json(platform_payload()["strategy_import"])
            elif route == "/strategy-import/example-preview":
                self._send_json(
                    strategy_import_preview_payload(
                        {
                            "source_type": "plain_language_claim",
                            "raw_text": (
                                "Thesis: BTC/USD daily momentum may beat buy-and-hold after costs. "
                                "Null: no edge after costs. Universe: BTC/USD. Horizon: daily bars. "
                                "Signal: close above 20 day high. Data: local OHLCV CSV."
                            ),
                            "source_ref": "manual:intake:example",
                        }
                    )
                )
            elif route == "/failure-gallery":
                self._send_json(platform_payload()["failure_gallery"])
            elif route == "/research-development/pass":
                self._send_json(research_development_pass_payload())
            elif route == "/confidence/readiness":
                self._send_json(confidence_readiness_payload())
            elif route == "/readiness/artifacts":
                self._send_json(readiness_artifacts_payload())
            elif route == "/agentic/review":
                self._send_json(agentic_review_payload())
            elif route == "/evidence/rigor":
                self._send_json(evidence_rigor_payload())
            else:
                self._send_json(
                    {
                        "error": "not_found",
                        "routes": [
                            "/health",
                            "/runs/example",
                            "/snapshots/latest",
                            "/terminal",
                            "/control-plane/lab",
                            "/platform/overview",
                            "/claims",
                            "/claims/{claim_id}",
                            "/evidence-graph/current",
                            "/point-in-time-contract/current",
                            "/falsification-engine/current",
                            "/agent-contracts",
                            "/readiness/ledger",
                            "/trust-packet/current",
                            "/strategy-import/contract",
                            "/strategy-import/preview",
                            "/strategy-import/example-preview",
                            "/failure-gallery",
                            "/research-development/pass",
                            "/confidence/readiness",
                            "/readiness/artifacts",
                            "/agentic/review",
                            "/evidence/rigor",
                        ],
                    },
                    status=404,
                )
        except Exception as exc:  # pragma: no cover - defensive server boundary
            self._send_json(
                {"error": type(exc).__name__, "detail": str(exc)},
                status=500,
            )

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler convention
        route = urlparse(self.path).path.rstrip("/") or "/"
        try:
            if route == "/strategy-import/preview":
                self._send_json(strategy_import_preview_payload(self._read_json_body()))
            else:
                self._send_json(
                    {"error": "not_found", "routes": ["/strategy-import/preview"]},
                    status=404,
                )
        except ValueError as exc:
            self._send_json({"error": "bad_request", "detail": str(exc)}, status=400)
        except Exception as exc:  # pragma: no cover - defensive server boundary
            self._send_json(
                {"error": type(exc).__name__, "detail": str(exc)},
                status=500,
            )

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib handler convention
        self.send_response(204)
        self._send_common_headers(content_length=0)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        if os.environ.get("TRADING_LAB_API_ACCESS_LOG") == "1":
            super().log_message(format, *args)

    def _send_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self._send_common_headers(content_length=len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_common_headers(self, *, content_length: int) -> None:
        origin = self.headers.get("Origin")
        self.send_header(
            "Access-Control-Allow-Origin",
            origin if origin in ALLOWED_WEB_ORIGINS else "http://127.0.0.1:5199",
        )
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(content_length))

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > 64_000:
            raise ValueError("request body is too large for local preview")
        if length == 0:
            return {}
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("request body must be JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = ThreadingHTTPServer((host, port), TradingLabHandler)
    print(f"Trading Lab API: http://{host}:{port}")
    print("Boundary: research-only; no advice, broker, order, or execution APIs.")
    server.serve_forever()


def main() -> int:
    host = os.environ.get("TRADING_LAB_API_HOST", DEFAULT_HOST)
    port = int(os.environ.get("TRADING_LAB_API_PORT", str(DEFAULT_PORT)))
    serve(host, port)
    return 0


def _gate_counts(gates: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for gate in gates:
        status = gate.get("status")
        if status in counts:
            counts[status] += 1
    return counts


def _snapshot_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    metadata = event.get("metadata", {})
    provenance = metadata.get("provenance", {})
    return {
        "topic": event.get("topic"),
        "producer": event.get("producer"),
        "payload": payload,
        "metadata": metadata,
        "record_hash": event.get("hash"),
        "created_at": event.get("created_at"),
        "observed_at": payload.get("observed_at"),
        "source_timestamp": metadata.get("source_timestamp"),
        "license_note": metadata.get("license_note"),
        "delay_class": metadata.get("delay_class"),
        "source_ref": provenance.get("source_ref"),
        "provider": provenance.get("provider", {}),
        "raw_hash": provenance.get("raw_hash"),
        "normalized_hash": provenance.get("normalized_hash"),
    }


def _top_gates(gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {"fail": 0, "warn": 1, "pass": 2}
    return sorted(gates, key=lambda gate: priority.get(gate.get("status"), 3))[:4]


def _mid_price(quote: dict[str, Any]) -> float | None:
    bid = _number(quote.get("bid"))
    ask = _number(quote.get("ask"))
    if bid is None or ask is None:
        return None
    return round((bid + ask) / 2, 8)


def _spread_bps(quote: dict[str, Any]) -> float | None:
    bid = _number(quote.get("bid"))
    ask = _number(quote.get("ask"))
    mid = _mid_price(quote)
    if bid is None or ask is None or mid in (None, 0):
        return None
    return round(((ask - bid) / mid) * 10_000, 2)


def _spread_abs(quote: dict[str, Any]) -> float | None:
    bid = _number(quote.get("bid"))
    ask = _number(quote.get("ask"))
    if bid is None or ask is None:
        return None
    return round(ask - bid, 8)


def _last_vs_mid(quote: dict[str, Any]) -> float | None:
    last = _number(quote.get("last"))
    mid = _mid_price(quote)
    if last is None or mid is None:
        return None
    return round(last - mid, 8)


def _last_location(quote: dict[str, Any]) -> str:
    bid = _number(quote.get("bid"))
    ask = _number(quote.get("ask"))
    last = _number(quote.get("last"))
    if bid is None or ask is None or last is None:
        return "unknown"
    if last < bid:
        return "below_bid"
    if last == bid:
        return "at_bid"
    if bid < last < ask:
        return "inside_spread"
    if last == ask:
        return "at_ask"
    return "above_ask"


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _freshness_label(source_timestamp: Any) -> dict[str, Any]:
    if not source_timestamp:
        return {"label": "unknown", "age_seconds": None}
    try:
        observed = datetime.fromisoformat(str(source_timestamp).replace("Z", "+00:00"))
        age_seconds = max(0, round((datetime.now().astimezone() - observed).total_seconds()))
    except ValueError:
        return {"label": "unknown", "age_seconds": None}
    if age_seconds <= 60:
        label = "fresh"
    elif age_seconds <= 300:
        label = "aging"
    else:
        label = "stale"
    return {"label": label, "age_seconds": age_seconds}


def _headline(run: dict[str, Any], event: dict[str, Any], freshness: dict[str, Any]) -> str:
    symbol = event.get("payload", {}).get("symbol", "market")
    verdict = run.get("verdict", "unknown")
    return f"{symbol}: observe only; evidence verdict is {verdict}; quote is {freshness['label']}."


def _focus_queue(
    run: dict[str, Any],
    snapshot: dict[str, Any],
    spread_bps: float | None,
    freshness: dict[str, Any],
) -> list[dict[str, str]]:
    queue = []
    if freshness["label"] != "fresh":
        queue.append(
            {
                "label": "Refresh observation",
                "why": "A terminal should not promote stale market context.",
            }
        )
    if spread_bps is not None:
        queue.append(
            {
                "label": "Review market-friction context",
                "why": f"Current observed spread is {spread_bps} bps; keep it as context, not advice.",
            }
        )
    for gate in _top_gates(run["gate_results"]):
        if gate["status"] != "pass":
            queue.append(
                {
                    "label": f"Resolve {gate['name']}",
                    "why": gate["detail"],
                }
            )
    if snapshot["count"] == 0:
        queue.append(
            {
                "label": "Collect bounded observation",
                "why": "No provider-backed market snapshot is available.",
            }
        )
    return queue[:4]


def _terminal_blockers(
    run: dict[str, Any],
    snapshot: dict[str, Any],
    spread_bps: float | None,
    freshness: dict[str, Any],
) -> list[str]:
    blockers = [
        "No paper ledger or live-shadow drift monitor exists.",
        "No human approval packet exists.",
        "Advice and execution routes are disabled.",
    ]
    if snapshot["count"] == 0:
        blockers.append("No market observation snapshot exists.")
    if freshness["label"] != "fresh":
        blockers.append("Latest quote is not fresh.")
    if spread_bps is None:
        blockers.append("Spread cannot be computed from the current observation.")
    if run["disproof_score"] > 0:
        blockers.append("Evidence run still has unresolved warnings or failures.")
    return blockers


def _readiness_checks(
    run: dict[str, Any],
    snapshot: dict[str, Any],
    spread_bps: float | None,
    freshness: dict[str, Any],
    artifacts: dict[str, Any],
) -> list[dict[str, Any]]:
    gate_counts = run["gate_counts"]
    checks = [
        {
            "id": "provider_provenance",
            "label": "Provider provenance",
            "passed": snapshot["count"] > 0,
            "why": "Every displayed market fact needs source, timestamp, and hash lineage.",
        },
        {
            "id": "fresh_observation",
            "label": "Fresh market observation",
            "passed": freshness["label"] == "fresh",
            "why": "Live setup views should degrade when the latest quote is aging or stale.",
        },
        {
            "id": "spread_context",
            "label": "Spread context",
            "passed": spread_bps is not None,
            "why": "A setup cannot be judged without at least basic bid/ask friction.",
        },
        {
            "id": "no_failed_gates",
            "label": "No failed evidence gates",
            "passed": gate_counts["fail"] == 0,
            "why": "Critical evidence failures must block higher-confidence labels.",
        },
        {
            "id": "no_warning_gates",
            "label": "No warning evidence gates",
            "passed": gate_counts["warn"] == 0,
            "why": "Warnings like weak comparator performance keep the claim in research mode.",
        },
        {
            "id": "walk_forward_positive",
            "label": "Walk-forward edge",
            "passed": _gate_passed(run, "walk-forward robustness"),
            "why": "Rolling out-of-sample windows are the minimum defense against overfit claims.",
        },
        {
            "id": "baseline_beaten",
            "label": "Comparator beaten",
            "passed": _gate_passed(run, "baseline comparison"),
            "why": "A setup family must beat a boring baseline before it deserves attention.",
        },
        {
            "id": "paper_ledger",
            "label": "Paper ledger",
            "passed": _artifact_passed(artifacts, "paper_ledger"),
            "why": "Forward paper outcomes must be logged before any confident live setup view.",
        },
        {
            "id": "live_shadow_drift",
            "label": "Live-shadow drift",
            "passed": _artifact_passed(artifacts, "live_shadow_drift"),
            "why": "Backtest expectations need live-market shadow comparison before promotion.",
        },
        {
            "id": "calibration_history",
            "label": "Confidence calibration",
            "passed": _artifact_passed(artifacts, "calibration_history"),
            "why": "Probability labels need realized-outcome calibration, such as Brier-style scoring.",
        },
        {
            "id": "risk_packet",
            "label": "Risk packet",
            "passed": _artifact_passed(artifacts, "risk_packet"),
            "why": "A setup view needs horizon, invalidation, expiry, slippage cap, and loss assumptions.",
        },
        {
            "id": "human_review",
            "label": "Human review",
            "passed": False,
            "why": "A human approval packet must exist before anything leaves research-only mode.",
        },
    ]
    return checks


def _completed_readiness_checks(
    run: dict[str, Any],
    snapshot: dict[str, Any],
    spread_bps: float | None,
    freshness: dict[str, Any],
    artifacts: dict[str, Any],
) -> set[str]:
    return {
        check["id"]
        for check in _readiness_checks(run, snapshot, spread_bps, freshness, artifacts)
        if check["passed"]
    }


def _confidence_stages() -> list[dict[str, Any]]:
    return [
        {
            "id": "observe_only",
            "label": "Observe-only",
            "requires": ["provider_provenance"],
            "output": "Show source-labeled market facts and evidence blockers.",
        },
        {
            "id": "research_candidate",
            "label": "Research candidate",
            "requires": [
                "provider_provenance",
                "fresh_observation",
                "spread_context",
                "no_failed_gates",
            ],
            "output": "Show claim under test, next falsification task, and non-actionable context.",
        },
        {
            "id": "validated_setup_note",
            "label": "Validated setup note",
            "requires": [
                "fresh_observation",
                "no_warning_gates",
                "walk_forward_positive",
                "baseline_beaten",
                "risk_packet_promotion_ready",
            ],
            "output": "Show scenario, horizon, invalidation, expiry, and evidence refs without execution.",
        },
        {
            "id": "shadow_confidence",
            "label": "Shadow confidence",
            "requires": [
                "paper_ledger_promotion_ready",
                "live_shadow_drift_promotion_ready",
                "calibration_history_promotion_ready",
                "risk_packet_promotion_ready",
                "no_warning_gates",
                "walk_forward_positive",
                "baseline_beaten",
            ],
            "output": "Show calibrated confidence bands and live-vs-expected drift state.",
        },
        {
            "id": "limited_live_review",
            "label": "Limited live review",
            "requires": [
                "paper_ledger_promotion_ready",
                "live_shadow_drift_promotion_ready",
                "calibration_history_promotion_ready",
                "risk_packet_promotion_ready",
                "no_warning_gates",
                "walk_forward_positive",
                "baseline_beaten",
                "human_review",
            ],
            "output": "Show human-reviewed setup packet; execution remains disabled in this product lane.",
        },
    ]


def _current_stage(stages: list[dict[str, Any]], completed: set[str]) -> dict[str, Any]:
    current = stages[0]
    for stage in stages:
        if set(stage["requires"]).issubset(completed):
            current = stage
    return current


def _allowed_output(stage: dict[str, Any]) -> str:
    return str(stage["output"])


def _gate_passed(run: dict[str, Any], name: str) -> bool:
    for gate in run["gate_results"]:
        if gate["name"] == name:
            return gate["status"] == "pass"
    return False


def _first_evidence_value(run: dict[str, Any], gate_name: str, field: str) -> Any:
    for gate in run["gate_results"]:
        if gate["name"] == gate_name:
            return gate.get("evidence", {}).get(field)
    return None


def _snapshot_symbol(snapshot: dict[str, Any]) -> str:
    if not snapshot["events"]:
        return "unknown"
    return str(snapshot["events"][0].get("payload", {}).get("symbol", "unknown"))


def _readiness_artifact(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "missing",
            "path": str(path.relative_to(PROJECT_ROOT)),
            "summary": "No artifact recorded.",
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": payload.get("status", "unknown"),
        "path": str(path.relative_to(PROJECT_ROOT)),
        "recorded_at": payload.get("recorded_at"),
        "summary": payload.get("summary", payload.get("drift", payload.get("limits", []))),
        "payload": payload,
    }


def _artifact_passed(artifacts: dict[str, Any], name: str) -> bool:
    return artifacts.get(name, {}).get("status") == "pass"


if __name__ == "__main__":
    raise SystemExit(main())
