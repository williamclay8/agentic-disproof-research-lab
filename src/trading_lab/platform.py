"""Platform-level operating views for the agentic research lab."""

from __future__ import annotations

from typing import Any

from trading_lab.agents import AGENT_ROLES
from trading_lab.artifacts import ResearchRunArtifact
from trading_lab.control_plane import gate_evidence_summary, owner_for_gate, role_id, slug
from trading_lab.falsification import build_falsification_engine as build_core_falsification_engine
from trading_lab.point_in_time import (
    build_point_in_time_contract as build_core_point_in_time_contract,
)
from trading_lab.readiness_ledger import summarize_readiness_ledger
from trading_lab.trust_packet import build_trust_packet as build_core_trust_packet


WEDGE_SENTENCE = (
    "The agentic trading lab that kills weak strategies faster than anyone else, "
    "and only lets surviving claims advance through auditable evidence gates."
)

SUPPORTED_STRATEGY_SOURCES = [
    "plain_language_claim",
    "csv_backtest",
    "pine_script",
    "lean_algorithm",
    "notebook_summary",
]


def build_platform_overview(
    artifact: ResearchRunArtifact,
    *,
    run: dict[str, Any],
    snapshot: dict[str, Any],
    readiness: dict[str, Any],
    evidence_rigor: dict[str, Any],
    agentic_review: dict[str, Any],
    control_plane: dict[str, Any],
) -> dict[str, Any]:
    """Build the core platform map from already-recorded research evidence."""

    source_ref = run.get("source", "runs/example-run.json")
    gaps = control_plane.get("evidence_gaps", [])
    tasks = control_plane.get("next_falsification_tasks", [])
    lifecycle = control_plane.get("claim_lifecycle", {})
    readiness_ledger = _readiness_ledger(readiness, control_plane, source_ref)
    return {
        "mode": "research_only",
        "wedge_sentence": WEDGE_SENTENCE,
        "build_philosophy": [
            "Make every claim pre-registered, source-referenced, and easy to disprove.",
            "Render the next falsification move before any positive narrative.",
            "Use agents as evidence-contract owners inside offline review.",
            "Promote only research packets that survive explicit readiness gates.",
            "Keep market observations bounded, labeled, and non-actionable.",
        ],
        "claim_registry": _claim_registry(artifact, run, lifecycle, gaps, source_ref),
        "evidence_graph": _evidence_graph(
            artifact,
            run=run,
            snapshot=snapshot,
            readiness=readiness,
            evidence_rigor=evidence_rigor,
            control_plane=control_plane,
            source_ref=source_ref,
        ),
        "point_in_time_contract": _point_in_time_contract(
            artifact,
            snapshot=snapshot,
            evidence_rigor=evidence_rigor,
            source_ref=source_ref,
        ),
        "falsification_engine": _falsification_engine(
            artifact,
            evidence_rigor=evidence_rigor,
            evidence_gaps=gaps,
            tasks=tasks,
            source_ref=source_ref,
        ),
        "agent_contracts": _agent_contracts(agentic_review, source_ref),
        "readiness_ledger": readiness_ledger,
        "trust_packet": _trust_packet(
            artifact,
            run=run,
            readiness=readiness,
            readiness_ledger=readiness_ledger,
            control_plane=control_plane,
            source_ref=source_ref,
        ),
        "strategy_import": _strategy_import(),
        "failure_gallery": _failure_gallery(artifact, run, lifecycle, gaps, source_ref),
    }


def _claim_registry(
    artifact: ResearchRunArtifact,
    run: dict[str, Any],
    lifecycle: dict[str, Any],
    gaps: list[dict[str, Any]],
    source_ref: str,
) -> dict[str, Any]:
    warning_gates = [gate.gate_name for gate in artifact.gate_results if gate.status == "warn"]
    failure_gates = [gate.gate_name for gate in artifact.gate_results if gate.status == "fail"]
    return {
        "claims": [
            {
                "claim_id": artifact.hypothesis.id,
                "thesis": artifact.hypothesis.thesis,
                "null_hypothesis": artifact.hypothesis.null_hypothesis,
                "state": lifecycle.get("stage", "research_only_hold"),
                "verdict": artifact.verdict,
                "disproof_score": artifact.disproof_score,
                "asset_universe": artifact.hypothesis.asset_universe,
                "time_horizon": artifact.hypothesis.time_horizon,
                "latest_run_id": artifact.run_id,
                "open_gap_count": len(gaps),
                "warning_gates": warning_gates,
                "failure_gates": failure_gates,
                "source_ref": source_ref,
            }
        ],
        "runs": [
            {
                "run_id": artifact.run_id,
                "claim_id": artifact.hypothesis.id,
                "verdict": artifact.verdict,
                "gate_counts": run.get("gate_counts", {}),
                "disproof_score": artifact.disproof_score,
                "dataset_hash": artifact.manifest.content_hash,
                "source_ref": source_ref,
            }
        ],
        "states": [
            "pre_registered",
            "offline_tested",
            "agent_reviewed",
            "research_only_hold",
            "offline_reviewed_research_packet",
        ],
        "registry_policy": "Claims advance by evidence state, not by persuasion or market excitement.",
    }


def _evidence_graph(
    artifact: ResearchRunArtifact,
    *,
    run: dict[str, Any],
    snapshot: dict[str, Any],
    readiness: dict[str, Any],
    evidence_rigor: dict[str, Any],
    control_plane: dict[str, Any],
    source_ref: str,
) -> dict[str, Any]:
    claim_id = artifact.hypothesis.id
    run_id = artifact.run_id
    dataset_id = f"dataset:{artifact.manifest.content_hash[:12]}"
    nodes = [
        _node(f"claim:{claim_id}", "claim", claim_id, artifact.verdict, source_ref),
        _node(f"run:{run_id}", "run", run_id, artifact.verdict, source_ref),
        _node(dataset_id, "dataset", artifact.manifest.source, "recorded", source_ref),
        _node(
            "snapshot:latest",
            "observation",
            snapshot.get("snapshot", "runs/live/latest.json"),
            "context_only",
            snapshot.get("snapshot", "runs/live/latest.json"),
        ),
        _node(
            "readiness:current",
            "readiness",
            readiness.get("current_stage", {}).get("label", "Observe-only"),
            "not_ready" if not readiness.get("validation", {}).get("promotion_ready") else "ready",
            source_ref,
        ),
    ]
    for gate in artifact.gate_results:
        nodes.append(
            _node(
                f"gate:{slug(gate.gate_name)}",
                "gate",
                gate.gate_name,
                gate.status,
                source_ref,
                {
                    "owner": owner_for_gate(gate.gate_name),
                    "severity": gate.severity,
                    "summary": gate_evidence_summary(gate),
                },
            )
        )
    for gap in control_plane.get("evidence_gaps", []):
        nodes.append(
            _node(
                gap["id"],
                "gap",
                gap.get("acceptance_test", gap["id"]),
                gap.get("status", "open"),
                gap.get("source_ref", source_ref),
                {"owner": gap.get("owner"), "severity": gap.get("severity")},
            )
        )
    for gap in evidence_rigor.get("summary", {}).get("evidence_gaps", []):
        gap_id = f"pit:{gap}"
        nodes.append(_node(gap_id, "point_in_time_gap", gap, "open", source_ref))

    edges = [
        _edge(f"claim:{claim_id}", f"run:{run_id}", "tested_by", source_ref),
        _edge(f"run:{run_id}", dataset_id, "uses_dataset", source_ref),
        _edge(f"run:{run_id}", "snapshot:latest", "displayed_with_context", source_ref),
        _edge(f"run:{run_id}", "readiness:current", "gated_by", source_ref),
    ]
    for gate in artifact.gate_results:
        gate_id = f"gate:{slug(gate.gate_name)}"
        edges.append(_edge(f"run:{run_id}", gate_id, "evaluated_by", source_ref))
        if gate.status != "pass":
            edges.append(_edge(gate_id, f"claim:{claim_id}", "blocks_promotion", source_ref))
    for gap in control_plane.get("evidence_gaps", []):
        gap_source = gap.get("source_ref", source_ref)
        edges.append(_edge(gap["id"], f"claim:{claim_id}", "blocks_claim_state", gap_source))
        if gap["id"].startswith("gate:"):
            edges.append(
                _edge(
                    gap["id"],
                    f"gate:{gap['id'].split(':', 1)[1]}",
                    "explains_gate",
                    gap_source,
                )
            )
    for gap in evidence_rigor.get("summary", {}).get("evidence_gaps", []):
        edges.append(_edge(f"pit:{gap}", "readiness:current", "blocks_readiness", source_ref))
    return {
        "graph_id": f"evidence-graph:{claim_id}",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "policy": "Every visible conclusion must trace back to a claim, run, gate, source, or readiness artifact.",
    }


def _point_in_time_contract(
    artifact: ResearchRunArtifact,
    *,
    snapshot: dict[str, Any],
    evidence_rigor: dict[str, Any],
    source_ref: str,
) -> dict[str, Any]:
    summary = evidence_rigor.get("summary", {})
    core_contract = build_core_point_in_time_contract(
        artifact,
        evidence_summary=summary,
        source_ref=source_ref,
    )
    gap_ids = summary.get("evidence_gaps", [])
    status = "needs_review" if gap_ids or summary.get("status") != "ready" else "ready"
    return {
        "contract_id": f"pit:{artifact.hypothesis.id}:v0",
        "contract_schema": core_contract.get("contract_schema"),
        "claim_id": artifact.hypothesis.id,
        "run_id": artifact.run_id,
        "status": status,
        "as_of_policy": "known-at-time inputs only",
        "allowed_fields": summary.get("allowed_fields", []),
        "leakage_suspect_fields": summary.get("leakage_suspect_fields", []),
        "unknown_lineage_fields": summary.get("unknown_lineage_fields", []),
        "present_baselines": summary.get("present_baselines", []),
        "missing_baselines": summary.get("missing_baselines", []),
        "dataset_window": {
            "start": artifact.manifest.start_date,
            "end": artifact.manifest.end_date,
            "source": artifact.manifest.source,
            "content_hash": artifact.manifest.content_hash,
        },
        "observation_refs": [snapshot.get("snapshot", "runs/live/latest.json")],
        "gaps": [
            {
                "id": gap,
                "status": "open",
                "owner": owner_for_gate(gap),
                "source_ref": evidence_rigor.get("source", source_ref),
            }
            for gap in gap_ids
        ],
        "fields": core_contract.get("fields", []),
        "review_roles": core_contract.get("review_roles", []),
        "source_refs": core_contract.get("source_refs", {}),
        "blocked_outputs": [
            "future-aware feature claims",
            "unstamped dataset claims",
            "unreferenced performance claims",
        ],
    }


def _falsification_engine(
    artifact: ResearchRunArtifact,
    *,
    evidence_rigor: dict[str, Any],
    evidence_gaps: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    source_ref: str,
) -> dict[str, Any]:
    core_engine = build_core_falsification_engine(
        artifact,
        evidence_gaps=evidence_gaps,
        control_plane_tasks=tasks,
        source_ref=source_ref,
    )
    missing_baselines = evidence_rigor.get("summary", {}).get("missing_baselines", [])
    objective_by_pack = {
        "baseline-pack": "Force every strategy to beat boring offline comparators.",
        "point-in-time-pack": "Prove every field and timestamp was known at the time under review.",
        "walk-forward-pack": "Break fold-fragile claims with chronological out-of-sample tests.",
        "cost-stress-pack": "Stress fees, slippage, and delay before claims can sound useful.",
        "reproducibility-pack": "Make reruns, hashes, and manifests inspectable before trust grows.",
        "readiness-pack": "Block promotion until paper, shadow, calibration, risk, and review proof exist.",
        "parameter-sweep-pack": "Reject isolated parameter peaks and fragile curve-fit stories.",
        "randomized-control-pack": "Compare against deterministic null controls before promotion.",
    }
    packs = []
    for pack in core_engine.get("packs", []):
        pack_id = pack["pack_id"]
        enriched = {
            **pack,
            "status": "ready" if pack.get("status") == "recorded" else pack.get("status"),
            "objective": objective_by_pack.get(pack_id, pack.get("label", pack_id)),
            "required_artifacts": pack.get("expected_artifacts", []),
            "missing_items": pack.get("gap_ids", []) or pack.get("open_gate_names", []),
            "source_ref": (pack.get("source_refs") or [source_ref])[0],
        }
        if pack_id == "baseline-pack" and missing_baselines:
            enriched["missing_items"] = missing_baselines
        packs.append(enriched)
    packs.append(
        {
            "pack_id": "parameter-sweep-pack",
            "status": _pack_status(artifact, "parameter sensitivity"),
            "owner": "Regime Skeptic",
            "claim_id": artifact.hypothesis.id,
            "objective": objective_by_pack["parameter-sweep-pack"],
            "required_artifacts": ["parameter_sensitivity_grid"],
            "missing_items": _gate_missing_items(artifact, "parameter sensitivity"),
            "source_ref": source_ref,
            "research_only": True,
        }
    )
    packs.append(
        {
            "pack_id": "randomized-control-pack",
            "status": "open" if "random-control" in missing_baselines else "ready",
            "owner": "Baseline Challenger",
            "claim_id": artifact.hypothesis.id,
            "objective": objective_by_pack["randomized-control-pack"],
            "required_artifacts": ["seeded_random_control_result"],
            "missing_items": ["random-control"] if "random-control" in missing_baselines else [],
            "source_ref": source_ref,
            "research_only": True,
        }
    )
    return {
        "engine_id": core_engine.get("engine_schema", "research-disproof-engine:v0"),
        "active_pack_id": "baseline-pack",
        "principle": "First try to kill the claim; only survivors earn more UI surface area.",
        "packs": packs,
        "queue": core_engine.get("tasks", tasks),
        "kill_criteria": [
            "Warning or failure gates stay open after the assigned pack runs.",
            "Point-in-time lineage cannot be proven from source artifacts.",
            "Readiness sample thresholds or human review remain missing.",
        ],
    }


def _agent_contracts(
    agentic_review: dict[str, Any],
    source_ref: str,
) -> list[dict[str, Any]]:
    findings_by_role: dict[str, list[dict[str, Any]]] = {}
    for finding in agentic_review.get("findings", []):
        findings_by_role.setdefault(finding.get("role", "Promotion Gatekeeper"), []).append(finding)
    return [
        {
            "agent": role["name"],
            "agent_id": role_id(role["name"]),
            "boundary": role["boundary"],
            "focus": role["focus"],
            "input_schema": "evidence_packet.v1",
            "output_schema": "agent_finding.v1",
            "required_output_fields": [
                "claim_id",
                "finding",
                "status",
                "severity",
                "source_refs",
                "next_falsification_step",
            ],
            "open_finding_count": len(
                [finding for finding in findings_by_role.get(role["name"], []) if finding.get("status") != "pass"]
            ),
            "source_refs": [source_ref],
            "forbidden_outputs": [
                "personalized recommendation",
                "position sizing guidance",
                "account action",
                "autonomous execution",
            ],
        }
        for role in AGENT_ROLES
    ]


def _readiness_ledger(
    readiness: dict[str, Any],
    control_plane: dict[str, Any],
    source_ref: str,
) -> dict[str, Any]:
    validation = readiness.get("validation", {})
    scorecard = control_plane.get("lab_scorecard", {})
    artifacts = readiness.get("readiness_artifacts", {})
    append_only_ledger = summarize_readiness_ledger(artifacts, validation=validation)
    return {
        "ledger_id": append_only_ledger.get("ledger_id", "readiness-ledger:v0"),
        "ledger_schema": append_only_ledger.get("ledger_schema"),
        "write_policy": append_only_ledger.get("write_policy"),
        "promotion_ready": validation.get("promotion_ready", False),
        "promotion_verdict": validation.get("promotion_verdict", {}),
        "current_stage": readiness.get("current_stage", {}),
        "completed_checks": readiness.get("completed_checks", []),
        "missing_checks": readiness.get("missing_checks", []),
        "missing_failed_checks": append_only_ledger.get("missing_failed_checks", []),
        "readiness_artifacts": [
            {
                "name": name,
                "status": payload.get("status"),
                "path": payload.get("path"),
                "summary": payload.get("summary", {}),
            }
            for name, payload in artifacts.items()
        ],
        "sample_thresholds": scorecard.get("readiness_samples", {}),
        "source_refs": [source_ref]
        + [payload.get("path") for payload in artifacts.values() if payload.get("path")],
        "append_only_entries": append_only_ledger.get("entries", []),
        "append_only_ledger": append_only_ledger,
    }


def _trust_packet(
    artifact: ResearchRunArtifact,
    *,
    run: dict[str, Any],
    readiness: dict[str, Any],
    readiness_ledger: dict[str, Any],
    control_plane: dict[str, Any],
    source_ref: str,
) -> dict[str, Any]:
    gaps = control_plane.get("evidence_gaps", [])
    core_packet = build_core_trust_packet(
        artifact,
        run=run,
        control_plane=control_plane,
        readiness_ledger=readiness_ledger.get("append_only_ledger", readiness_ledger),
        source_ref=source_ref,
    )
    return {
        **core_packet,
        "packet_id": f"trust:{artifact.run_id}",
        "claim_id": artifact.hypothesis.id,
        "run_id": artifact.run_id,
        "verdict": artifact.verdict,
        "export_status": "ready_for_research_review",
        "summary": (
            f"{artifact.hypothesis.id} remains {artifact.verdict}: "
            f"{run.get('gate_counts', {}).get('warn', 0)} warning gates, "
            f"{len(gaps)} open evidence gaps, "
            f"readiness promotion={readiness.get('validation', {}).get('promotion_ready', False)}."
        ),
        "evidence_refs": [
            source_ref,
            *[
                ref
                for ref in readiness_ledger.get("source_refs", [])
                if ref and ref != source_ref
            ][:4],
        ],
        "open_gaps": [gap["id"] for gap in gaps],
        "open_gap_ids": core_packet.get("open_gap_ids", [gap["id"] for gap in gaps]),
        "blocker_count": len(gaps) + len(readiness.get("missing_checks", [])),
        "not_allowed": readiness.get("not_allowed", []),
        "review_questions": [
            "Which evidence gap would most quickly disprove the claim?",
            "Does every displayed claim trace back to a source reference?",
            "Which agent contract owns the weakest unresolved proof?",
        ],
    }


def _strategy_import() -> dict[str, Any]:
    return {
        "supported_sources": SUPPORTED_STRATEGY_SOURCES,
        "intake_contract": {
            "required_outputs": [
                "pre_registered_claim",
                "null_hypothesis",
                "data_requirements",
                "falsification_tests",
                "blocked_outputs",
            ],
            "default_state": "quarantine_until_evidence_exists",
            "first_gate": "point_in_time_contract",
        },
        "blocked_fields": [
            "broker",
            "account",
            "api_key",
            "secret",
            "order",
            "position_size",
            "entry",
            "exit",
            "live_signal",
        ],
        "normalization_steps": [
            "Extract the claim and null hypothesis.",
            "Convert source code or narrative into a research-only test spec.",
            "Attach dataset, timestamp, and source references.",
            "Run disproof packs before the claim appears in the main console.",
        ],
        "blocked_imports": [
            "credentialed account connectors",
            "unstamped live-feed dependencies",
            "claims without a null hypothesis",
        ],
    }


def _failure_gallery(
    artifact: ResearchRunArtifact,
    run: dict[str, Any],
    lifecycle: dict[str, Any],
    gaps: list[dict[str, Any]],
    source_ref: str,
) -> dict[str, Any]:
    blocked = artifact.verdict != "passed preliminary gates" or bool(gaps)
    entries = []
    if blocked:
        entries.append(
            {
                "claim_id": artifact.hypothesis.id,
                "run_id": artifact.run_id,
                "stage": lifecycle.get("stage", "research_only_hold"),
                "verdict": artifact.verdict,
                "disproof_score": artifact.disproof_score,
                "open_warning_gates": [
                    gate.gate_name for gate in artifact.gate_results if gate.status == "warn"
                ],
                "open_failure_gates": [
                    gate.gate_name for gate in artifact.gate_results if gate.status == "fail"
                ],
                "primary_failure_reason": _primary_failure_reason(artifact, gaps),
                "source_ref": source_ref,
            }
        )
    return {
        "gallery_id": "failure-gallery:v0",
        "failed_or_blocked_claims": entries,
        "learning_value": "Dead and blocked claims become training data for faster future falsification.",
        "next_archive_action": (
            f"Capture reviewer notes for {run.get('id', artifact.hypothesis.id)}."
            if entries
            else "No blocked claim is ready for the gallery."
        ),
    }


def _node(
    node_id: str,
    kind: str,
    label: str,
    status: str,
    source_ref: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "id": node_id,
        "kind": kind,
        "label": label,
        "status": status,
        "source_ref": source_ref,
    }
    if extra:
        payload.update(extra)
    return payload


def _edge(source: str, target: str, relation: str, source_ref: str) -> dict[str, str]:
    edge_id = f"{slug(source)}--{relation}--{slug(target)}"
    return {
        "id": edge_id,
        "source": source,
        "target": target,
        "from": source,
        "to": target,
        "relation": relation,
        "relationship": relation,
        "source_ref": source_ref,
    }


def _pack_status(artifact: ResearchRunArtifact, gate_name: str) -> str:
    for gate in artifact.gate_results:
        if gate.gate_name == gate_name:
            return "ready" if gate.status == "pass" else "open"
    return "open"


def _gate_missing_items(artifact: ResearchRunArtifact, gate_name: str) -> list[str]:
    for gate in artifact.gate_results:
        if gate.gate_name == gate_name and gate.status != "pass":
            return [gate.remediation_hint]
    return []


def _primary_failure_reason(
    artifact: ResearchRunArtifact,
    gaps: list[dict[str, Any]],
) -> str:
    for gate in artifact.gate_results:
        if gate.status != "pass":
            return gate.remediation_hint
    if gaps:
        return gaps[0].get("detail", "Evidence gap remains open.")
    return "No failure reason recorded."
