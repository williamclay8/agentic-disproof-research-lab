"""Derived control-plane views for operating the research lab.

The helpers in this module do not introduce new evidence. They translate the
current run, review, rigor, and readiness artifacts into lab work objects:
missions, gaps, tasks, lifecycle state, and learning loops.
"""

from __future__ import annotations

from typing import Any

from trading_lab.agents import AGENT_ROLES
from trading_lab.artifacts import ResearchRunArtifact
from trading_lab.models import GateResult
from trading_lab.readiness import MIN_SAMPLE_COUNT
from trading_lab.training import (
    build_experiment_ledger,
    build_mistake_taxonomy,
    build_training_plan,
    research_maturity_score,
)


def build_lab_control_plane(
    artifact: ResearchRunArtifact,
    *,
    run: dict[str, Any],
    snapshot: dict[str, Any],
    readiness: dict[str, Any],
    evidence_rigor: dict[str, Any],
    agentic_review: dict[str, Any],
    blockers: list[str],
    ranked_attention_items: list[dict[str, Any]],
    spread_bps: float | None,
    freshness: dict[str, Any],
) -> dict[str, Any]:
    """Build a research-only operating layer from existing evidence."""

    source_ref = run["source"]
    gaps = build_evidence_gaps(
        artifact,
        readiness=readiness,
        evidence_rigor=evidence_rigor,
        source_ref=source_ref,
    )
    tasks = build_next_falsification_tasks(
        artifact,
        evidence_gaps=gaps,
        readiness=readiness,
        source_ref=source_ref,
    )
    lifecycle = build_claim_lifecycle(
        artifact,
        run=run,
        readiness=readiness,
        agentic_review=agentic_review,
        blockers=blockers,
        source_ref=source_ref,
    )
    return {
        "mode": "research_only",
        "boundary": {
            "label": "standalone research lab",
            "execution": "disabled",
            "advice": "disabled",
            "allowed_output": readiness.get(
                "allowed_output",
                "Show source-labeled market facts and evidence blockers.",
            ),
        },
        "source_refs": {
            "run": source_ref,
            "snapshot": snapshot.get("snapshot"),
            "readiness_artifacts": [
                artifact_payload.get("path")
                for artifact_payload in readiness.get("readiness_artifacts", {}).values()
                if artifact_payload.get("path")
            ],
        },
        "human_brief": build_human_brief(
            run,
            snapshot=snapshot,
            readiness=readiness,
            blockers=blockers,
            ranked_attention_items=ranked_attention_items,
            spread_bps=spread_bps,
            freshness=freshness,
        ),
        "active_mission": build_active_mission(artifact, gaps, source_ref),
        "agent_mission_board": build_agent_mission_board(
            artifact,
            agentic_review=agentic_review,
            evidence_gaps=gaps,
            readiness=readiness,
            source_ref=source_ref,
        ),
        "claim_lifecycle": lifecycle,
        "gate_summaries": build_gate_summaries(artifact),
        "evidence_gaps": gaps,
        "next_falsification_tasks": tasks,
        "lab_scorecard": build_lab_scorecard(
            artifact,
            run=run,
            readiness=readiness,
            evidence_rigor=evidence_rigor,
            evidence_gaps=gaps,
            tasks=tasks,
        ),
        "learning_loop": build_learning_loop(artifact, source_ref),
    }


def build_human_brief(
    run: dict[str, Any],
    *,
    snapshot: dict[str, Any],
    readiness: dict[str, Any],
    blockers: list[str],
    ranked_attention_items: list[dict[str, Any]],
    spread_bps: float | None,
    freshness: dict[str, Any],
) -> dict[str, Any]:
    event = snapshot["events"][0] if snapshot.get("events") else {}
    symbol = event.get("payload", {}).get("symbol", "unknown")
    counts = run.get("gate_counts", {})
    next_item = ranked_attention_items[0] if ranked_attention_items else {}
    missing = readiness.get("missing_checks", [])
    return {
        "what_matters_now": (
            f"{symbol} stays in research hold: {freshness.get('label', 'unknown')} "
            f"observation, {run.get('verdict', 'unknown')} evidence, "
            f"{counts.get('warn', 0)} warnings, {len(blockers)} blockers."
        ),
        "why_it_matters": _first_open_gate_text(run)
        or "Promotion evidence is incomplete, so the lab should keep pressure on the proof.",
        "changed_since_last": (
            "No prior comparable packet is loaded; this view shows current evidence state only."
        ),
        "best_next_action": next_item.get("label", "Inspect weakest evidence gap"),
        "would_change_our_mind": [
            check.get("label") or check.get("id")
            for check in missing[:4]
        ],
        "market_context": (
            f"Observed spread is {spread_bps} bps and remains context only."
            if spread_bps is not None
            else "Observed spread is unavailable in the current packet."
        ),
    }


def build_active_mission(
    artifact: ResearchRunArtifact,
    evidence_gaps: list[dict[str, Any]],
    source_ref: str,
) -> dict[str, Any]:
    state = "warning_hold"
    if any(gate.status == "fail" for gate in artifact.gate_results):
        state = "blocked"
    elif not any(gate.status != "pass" for gate in artifact.gate_results):
        state = "readiness_hold" if evidence_gaps else "review_ready"
    return {
        "mission_id": f"mission-{artifact.hypothesis.id}-v0",
        "objective": "Falsify, quarantine, or document the current registered claim.",
        "claim_ids": [artifact.hypothesis.id],
        "state": state,
        "primary_blocker_ids": [gap["id"] for gap in evidence_gaps[:4]],
        "source_refs": [source_ref],
    }


def build_agent_mission_board(
    artifact: ResearchRunArtifact,
    *,
    agentic_review: dict[str, Any],
    evidence_gaps: list[dict[str, Any]],
    readiness: dict[str, Any],
    source_ref: str,
) -> list[dict[str, Any]]:
    findings_by_role: dict[str, list[dict[str, Any]]] = {}
    for finding in agentic_review.get("findings", []):
        findings_by_role.setdefault(finding.get("role", "Promotion Gatekeeper"), []).append(finding)

    rows = []
    for role in AGENT_ROLES:
        name = role["name"]
        role_findings = findings_by_role.get(name, [])
        open_findings = [finding for finding in role_findings if finding.get("status") != "pass"]
        top = open_findings[0] if open_findings else (role_findings[0] if role_findings else None)
        owned_gates = [
            gate.gate_name
            for gate in artifact.gate_results
            if owner_for_gate(gate.gate_name) == name
        ]
        owned_gaps = [gap for gap in evidence_gaps if gap.get("owner") == name]
        status = "active" if open_findings or (name == "Promotion Gatekeeper" and readiness.get("missing_checks")) else "monitoring"
        rows.append(
            {
                "agent_id": role_id(name),
                "name": name,
                "boundary": role["boundary"],
                "mission": _mission_for_role(name),
                "status": status,
                "assigned_claims": [artifact.hypothesis.id],
                "owned_gates": owned_gates,
                "open_findings": len(open_findings),
                "top_finding": top or {
                    "gate_name": "no open gate",
                    "status": "pass",
                    "severity": "info",
                    "summary": "No open finding is assigned to this role.",
                },
                "gap_ids": [gap["id"] for gap in owned_gaps[:5]],
                "next_action": _next_action_for_role(name, top, owned_gaps),
                "source_refs": [source_ref],
            }
        )
    return rows


def build_claim_lifecycle(
    artifact: ResearchRunArtifact,
    *,
    run: dict[str, Any],
    readiness: dict[str, Any],
    agentic_review: dict[str, Any],
    blockers: list[str],
    source_ref: str,
) -> dict[str, Any]:
    blocking_gate_names = [
        gate.gate_name for gate in artifact.gate_results if gate.status != "pass"
    ]
    stage = claim_lifecycle_stage(artifact, readiness)
    passport = {
        "artifact": source_ref,
        "dataset_hash": artifact.manifest.content_hash,
        "run_fingerprint": _first_gate_evidence(
            artifact.gate_results,
            "reproducibility",
            "first_fingerprint",
        ),
    }
    lifecycle = ["pre_registered", "offline_tested", "agent_reviewed"]
    if stage == "research_only_blocked":
        lifecycle.append("blocked")
    elif stage == "research_only_hold":
        lifecycle.append("warning_hold")
    else:
        lifecycle.append("offline_reviewed")
    return {
        "claim_id": artifact.hypothesis.id,
        "run_id": artifact.run_id,
        "thesis": artifact.hypothesis.thesis,
        "stage": stage,
        "state_reason": _stage_reason(blocking_gate_names, readiness),
        "verdict": artifact.verdict,
        "promotion_decision": agentic_review.get("promotion_decision", {}).get("decision"),
        "disproof_score": artifact.disproof_score,
        "gate_counts": run.get("gate_counts", {}),
        "blocking_gate_names": blocking_gate_names,
        "evidence_refs": passport,
        "blocked_by": blockers[:4]
        + [check.get("label", check.get("id", "readiness check")) for check in readiness.get("missing_checks", [])[:4]],
        "allowed_outputs": [
            "claim under test",
            "next falsification task",
            "evidence blockers",
            "source-labeled observations",
        ],
        "blocked_outputs": [
            "personalized recommendation",
            "directional live call",
            "position sizing guidance",
            "account route",
            "autonomous execution",
        ],
        "lifecycle": lifecycle,
    }


def claim_lifecycle_stage(
    artifact: ResearchRunArtifact,
    readiness: dict[str, Any],
) -> str:
    if any(gate.status == "fail" for gate in artifact.gate_results):
        return "research_only_blocked"
    if any(gate.status == "warn" for gate in artifact.gate_results):
        return "research_only_hold"
    if not readiness.get("validation", {}).get("promotion_ready"):
        return "research_only_hold"
    return "offline_reviewed_research_packet"


def build_gate_summaries(artifact: ResearchRunArtifact) -> dict[str, Any]:
    sorted_gates = sorted(
        artifact.gate_results,
        key=lambda gate: (
            {"fail": 0, "warn": 1, "pass": 2}.get(gate.status, 3),
            {"critical": 0, "warning": 1, "info": 2}.get(gate.severity, 3),
            gate.gate_name,
        ),
    )
    return {
        "counts": _gate_counts(artifact.gate_results),
        "weakest": [
            {
                "name": gate.gate_name,
                "status": gate.status,
                "severity": gate.severity,
                "threshold": gate.threshold,
                "evidence_summary": gate_evidence_summary(gate),
                "plain_english": _plain_english_gate(gate),
                "remediation_hint": gate.remediation_hint,
                "owner": owner_for_gate(gate.gate_name),
                "source_path": f"gate_results.{slug(gate.gate_name)}",
            }
            for gate in sorted_gates[:8]
        ],
    }


def build_evidence_gaps(
    artifact: ResearchRunArtifact,
    *,
    readiness: dict[str, Any],
    evidence_rigor: dict[str, Any],
    source_ref: str,
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for gate in sorted(
        [gate for gate in artifact.gate_results if gate.status != "pass"],
        key=lambda item: {"fail": 0, "warn": 1}.get(item.status, 2),
    ):
        owner = owner_for_gate(gate.gate_name)
        gaps.append(
            {
                "id": evidence_gap_id("gate", gate.gate_name),
                "kind": "failure_gate" if gate.status == "fail" else "warning_gate",
                "category": _category_for_gap(gate.gate_name),
                "status": "open",
                "severity": gate.severity,
                "owner": owner,
                "claim_id": artifact.hypothesis.id,
                "detail": gate.remediation_hint,
                "blocks_stage": _stage_blocked_by_gate(gate.gate_name),
                "required_artifact": _required_artifact_for_gate(gate.gate_name),
                "acceptance_test": gate.threshold,
                "source_ref": source_ref,
                "evidence_path": f"gate_results.{slug(gate.gate_name)}",
            }
        )

    for gap in evidence_rigor.get("summary", {}).get("evidence_gaps", []):
        owner = _owner_for_rigor_gap(gap)
        gaps.append(
            {
                "id": evidence_gap_id("rigor", gap),
                "kind": gap.split(":", 1)[0],
                "category": _category_for_gap(gap),
                "status": "open",
                "severity": "warning",
                "owner": owner,
                "claim_id": artifact.hypothesis.id,
                "detail": _rigor_gap_detail(gap),
                "blocks_stage": "validated_setup_note",
                "required_artifact": _required_artifact_for_rigor_gap(gap),
                "acceptance_test": "record the missing offline evidence with source references",
                "source_ref": evidence_rigor.get("source", source_ref),
                "evidence_path": f"evidence_rigor.summary.evidence_gaps.{slug(gap)}",
            }
        )

    for check in readiness.get("missing_checks", []):
        check_id = check.get("id", "readiness_check")
        gaps.append(
            {
                "id": evidence_gap_id("readiness", check_id),
                "kind": "promotion_blocker",
                "category": "readiness",
                "status": "open",
                "severity": "warning",
                "owner": "Promotion Gatekeeper",
                "claim_id": artifact.hypothesis.id,
                "detail": check.get("why") or check.get("detail", "Readiness proof is missing."),
                "blocks_stage": _blocks_stage_for_check(check_id),
                "required_artifact": check_id,
                "acceptance_test": check.get("label", check_id),
                "source_ref": _readiness_source_ref(readiness, check_id) or source_ref,
                "evidence_path": f"confidence_readiness.missing_checks.{slug(check_id)}",
            }
        )

    return gaps


def build_next_falsification_tasks(
    artifact: ResearchRunArtifact,
    *,
    evidence_gaps: list[dict[str, Any]],
    readiness: dict[str, Any],
    source_ref: str,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    priority = 1
    for gate in [gate for gate in artifact.gate_results if gate.status != "pass"]:
        label = f"Retest {gate.gate_name} against stricter offline evidence."
        if gate.gate_name == "walk-forward robustness":
            label = "Record additional offline walk-forward folds."
        tasks.append(
            _task(
                task_id=f"task:{slug(gate.gate_name)}:retest",
                priority=priority,
                owner=owner_for_gate(gate.gate_name),
                claim_id=artifact.hypothesis.id,
                label=label,
                source="gate_review",
                gap_ids=[evidence_gap_id("gate", gate.gate_name)],
                expected_artifact=_required_artifact_for_gate(gate.gate_name),
                source_ref=source_ref,
            )
        )
        priority += 1

    for next_test in artifact.next_tests:
        tasks.append(
            _task(
                task_id=f"task:next-test:{slug(next_test)}",
                priority=priority,
                owner=owner_for_gate(next_test),
                claim_id=artifact.hypothesis.id,
                label=f"Run offline test: {next_test}.",
                source="run.next_tests",
                gap_ids=_gap_ids_for_text(evidence_gaps, next_test),
                expected_artifact="offline_research_artifact",
                source_ref=source_ref,
            )
        )
        priority += 1

    for gap in evidence_gaps:
        if gap["id"].startswith("gate:"):
            continue
        tasks.append(
            _task(
                task_id=f"task:{slug(gap['id'])}:collect",
                priority=priority,
                owner=gap["owner"],
                claim_id=artifact.hypothesis.id,
                label=f"Collect proof for {gap['acceptance_test']}.",
                source=gap["kind"],
                gap_ids=[gap["id"]],
                expected_artifact=gap["required_artifact"],
                source_ref=gap["source_ref"],
            )
        )
        priority += 1

    return tasks[:12]


def build_lab_scorecard(
    artifact: ResearchRunArtifact,
    *,
    run: dict[str, Any],
    readiness: dict[str, Any],
    evidence_rigor: dict[str, Any],
    evidence_gaps: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    rigor = evidence_rigor.get("summary", {})
    return {
        "claim_count": 1,
        "readiness_stage": readiness.get("current_stage", {}).get("id", "unknown"),
        "promotion_ready": readiness.get("validation", {}).get("promotion_ready", False),
        "disproof_pressure": artifact.disproof_score,
        "research_maturity": research_maturity_score(artifact.gate_results),
        "evidence_rigor": {
            "score": rigor.get("score"),
            "status": rigor.get("status"),
            "missing_baselines": rigor.get("missing_baselines", []),
            "present_baselines": rigor.get("present_baselines", []),
        },
        "open_gate_counts": {
            "warn": run.get("gate_counts", {}).get("warn", 0),
            "fail": run.get("gate_counts", {}).get("fail", 0),
        },
        "open_gap_count": len(evidence_gaps),
        "open_task_count": len(tasks),
        "readiness_samples": _readiness_samples(readiness),
        "not_allowed": readiness.get("not_allowed", []),
    }


def build_learning_loop(
    artifact: ResearchRunArtifact,
    source_ref: str,
) -> dict[str, Any]:
    mistakes = build_mistake_taxonomy(artifact.gate_results)
    names = [mistake["name"] for mistake in mistakes]
    ledger = build_experiment_ledger([artifact])[0]
    next_round = int(ledger["next_curriculum_round"])
    plan = build_training_plan()
    lesson = _lesson_for_mistake(names[0] if names else "")
    return {
        "current_lesson": lesson,
        "recurring_mistakes": names,
        "next_curriculum_round": next_round,
        "training_focus": plan[next_round - 1]["focus"],
        "lab_memory": [
            {
                "pattern": mistake["learning_focus"],
                "evidence_refs": [source_ref],
                "next_behavior": _next_behavior_for_mistake(mistake["name"]),
            }
            for mistake in mistakes[:4]
        ],
    }


def role_id(role_name: str) -> str:
    return slug(role_name).replace("-", "_")


def owner_for_gate(gate_name: str) -> str:
    normalized = gate_name.lower()
    if any(term in normalized for term in ("lookahead", "chronology", "schema", "lineage")):
        return "Leak Auditor"
    if "baseline" in normalized or "comparator" in normalized:
        return "Baseline Challenger"
    if "cost" in normalized or "slippage" in normalized or "delay" in normalized:
        return "Cost Stress Critic"
    if "reproduc" in normalized or "fingerprint" in normalized or "manifest" in normalized:
        return "Reproducibility Clerk"
    if any(term in normalized for term in ("walk-forward", "parameter", "regime", "fold")):
        return "Regime Skeptic"
    return "Promotion Gatekeeper"


def evidence_gap_id(kind: str, label: str) -> str:
    if kind == "rigor":
        return f"rigor:{label}"
    if kind == "readiness":
        return f"readiness:{label}"
    return f"{kind}:{slug(label)}"


def gate_evidence_summary(gate: GateResult) -> str:
    evidence = gate.evidence
    if "strategy_cumulative_return" in evidence and "baseline_cumulative_return" in evidence:
        return (
            f"strategy {evidence['strategy_cumulative_return']} vs "
            f"baseline {evidence['baseline_cumulative_return']}"
        )
    if "passing_folds" in evidence and "folds" in evidence:
        return (
            f"{evidence['passing_folds']} / {evidence['folds']} folds passed; "
            f"pass_ratio {evidence.get('pass_ratio')}"
        )
    if "first_fingerprint" in evidence:
        return f"fingerprints match: {evidence.get('first_fingerprint') == evidence.get('second_fingerprint')}"
    values = [f"{key}={value}" for key, value in evidence.items() if not isinstance(value, list)]
    return "; ".join(values[:3]) or "recorded evidence payload"


def slug(value: str) -> str:
    text = str(value).lower().replace(":", "-").replace("_", "-")
    chars = [char if char.isalnum() else "-" for char in text]
    return "-".join(part for part in "".join(chars).split("-") if part)


def _gate_counts(gates: list[GateResult]) -> dict[str, int]:
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for gate in gates:
        counts[gate.status] += 1
    return counts


def _first_open_gate_text(run: dict[str, Any]) -> str:
    for gate in run.get("gate_results", []):
        if gate.get("status") != "pass":
            return f"{gate.get('name')} is unresolved: {gate.get('detail')}"
    return ""


def _mission_for_role(role_name: str) -> str:
    missions = {
        "Leak Auditor": "Protect point-in-time lineage, schema, and chronology.",
        "Baseline Challenger": "Attack comparator discipline and missing baseline evidence.",
        "Cost Stress Critic": "Stress friction, delay, and cost-grid assumptions.",
        "Reproducibility Clerk": "Keep source hashes, manifests, and reruns auditable.",
        "Promotion Gatekeeper": "Hold the display ladder until readiness proof clears.",
        "Regime Skeptic": "Attack fold, parameter, and regime fragility.",
    }
    return missions.get(role_name, "Review offline evidence gaps.")


def _next_action_for_role(
    role_name: str,
    top_finding: dict[str, Any] | None,
    owned_gaps: list[dict[str, Any]],
) -> str:
    if top_finding and top_finding.get("status") != "pass":
        return f"Resolve {top_finding.get('gate_name')} with harder offline proof."
    if owned_gaps:
        return f"Collect proof for {owned_gaps[0]['acceptance_test']}."
    if role_name == "Promotion Gatekeeper":
        return "Keep stage rules visible and require human review before promotion."
    return "Keep this control observable in the evidence ledger."


def _stage_reason(blocking_gate_names: list[str], readiness: dict[str, Any]) -> str:
    if blocking_gate_names:
        return f"Open warning gates: {', '.join(blocking_gate_names)}."
    if not readiness.get("validation", {}).get("promotion_ready"):
        return "Readiness artifacts are present but not promotion-ready."
    return "Recorded research gates and readiness checks are clear."


def _first_gate_evidence(gates: list[GateResult], gate_name: str, key: str) -> Any:
    for gate in gates:
        if gate.gate_name == gate_name:
            return gate.evidence.get(key)
    return None


def _plain_english_gate(gate: GateResult) -> str:
    if gate.gate_name == "baseline comparison":
        strategy = gate.evidence.get("strategy_cumulative_return")
        baseline = gate.evidence.get("baseline_cumulative_return")
        return f"The strategy value {strategy} did not clear the baseline value {baseline}."
    if gate.gate_name == "walk-forward robustness":
        return gate_evidence_summary(gate)
    if gate.status == "pass":
        return "This control has recorded passing evidence."
    return gate.remediation_hint


def _category_for_gap(label: str) -> str:
    normalized = label.lower()
    if "baseline" in normalized:
        return "comparator_discipline"
    if "walk" in normalized or "fold" in normalized or "regime" in normalized:
        return "regime_robustness"
    if "cost" in normalized or "slippage" in normalized:
        return "friction"
    if "lineage" in normalized or "leakage" in normalized or "schema" in normalized:
        return "data_integrity"
    if "readiness" in normalized or "ledger" in normalized or "calibration" in normalized:
        return "readiness"
    return "evidence_quality"


def _stage_blocked_by_gate(gate_name: str) -> str:
    if gate_name in {"baseline comparison", "walk-forward robustness"}:
        return "validated_setup_note"
    return "research_candidate"


def _required_artifact_for_gate(gate_name: str) -> str:
    if gate_name == "baseline comparison":
        return "baseline_pack_result"
    if gate_name == "walk-forward robustness":
        return "walk_forward_fold_ledger"
    return "gate_evidence_record"


def _owner_for_rigor_gap(gap: str) -> str:
    if gap.startswith("missing_baseline"):
        return "Baseline Challenger"
    if gap.startswith("leakage") or gap.startswith("unknown_lineage"):
        return "Leak Auditor"
    return "Reproducibility Clerk"


def _rigor_gap_detail(gap: str) -> str:
    kind, _, value = gap.partition(":")
    if kind == "missing_baseline":
        return f"Missing required baseline: {value}."
    if kind == "unknown_lineage":
        return f"Column lineage is unknown: {value}."
    if kind == "leakage_suspect":
        return f"Potential leakage field needs review: {value}."
    return f"Evidence rigor gap: {gap}."


def _required_artifact_for_rigor_gap(gap: str) -> str:
    if gap.startswith("missing_baseline"):
        return "baseline_pack_result"
    if gap.startswith(("unknown_lineage", "leakage_suspect")):
        return "point_in_time_lineage_note"
    return "evidence_rigor_record"


def _blocks_stage_for_check(check_id: str) -> str:
    if "human_review" in check_id:
        return "limited_live_review"
    if "promotion_ready" in check_id or "sample_count" in check_id:
        return "shadow_confidence"
    return "research_candidate"


def _readiness_source_ref(readiness: dict[str, Any], check_id: str) -> str | None:
    artifacts = readiness.get("readiness_artifacts", {})
    for name, payload in artifacts.items():
        if check_id.startswith(name):
            return payload.get("path")
    return None


def _task(
    *,
    task_id: str,
    priority: int,
    owner: str,
    claim_id: str,
    label: str,
    source: str,
    gap_ids: list[str],
    expected_artifact: str,
    source_ref: str,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "priority": priority,
        "owner": owner,
        "claim_id": claim_id,
        "label": label,
        "kind": "offline_retest",
        "status": "open",
        "source": source,
        "gap_ids": gap_ids,
        "expected_artifact": expected_artifact,
        "completion_criteria": "Record source-referenced offline evidence and rerun the gate review.",
        "source_ref": source_ref,
        "research_only": True,
    }


def _gap_ids_for_text(evidence_gaps: list[dict[str, Any]], text: str) -> list[str]:
    normalized = text.lower()
    matches = [
        gap["id"]
        for gap in evidence_gaps
        if any(part in gap["id"] or part in gap.get("detail", "").lower() for part in normalized.split())
    ]
    return matches[:3]


def _readiness_samples(readiness: dict[str, Any]) -> dict[str, Any]:
    artifacts = readiness.get("readiness_artifacts", {})
    payloads = {
        name: artifact.get("payload", {})
        for name, artifact in artifacts.items()
    }
    risk_packet = payloads.get("risk_packet", {})
    return {
        "paper_ledger": {
            "current": _sample_count(payloads.get("paper_ledger", {})),
            "required": MIN_SAMPLE_COUNT,
        },
        "live_shadow_drift": {
            "current": _sample_count(payloads.get("live_shadow_drift", {})),
            "required": MIN_SAMPLE_COUNT,
        },
        "calibration_history": {
            "current": _sample_count(payloads.get("calibration_history", {})),
            "required": MIN_SAMPLE_COUNT,
        },
        "human_review": {
            "recorded": bool(risk_packet.get("human_review")),
            "required": True,
        },
    }


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
        return _int_value(summary.get("sample_count") or summary.get("hypothetical_setups_recorded"))
    return 0


def _int_value(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return max(parsed, 0)


def _lesson_for_mistake(mistake_name: str) -> str:
    mapping = {
        "Comparator weakness": "Comparator Discipline",
        "Fold fragility": "Fold Robustness",
        "Cost fragility": "Cost Friction",
        "Parameter fragility": "Parameter Robustness",
        "Leakage risk": "Leakage Control",
    }
    return mapping.get(mistake_name, "Evidence Discipline")


def _next_behavior_for_mistake(mistake_name: str) -> str:
    mapping = {
        "Comparator weakness": "Run full baseline packs before interpreting any upside.",
        "Fold fragility": "Require fold-level proof before promoting a claim narrative.",
        "Cost fragility": "Stress cost assumptions before writing the report headline.",
        "Parameter fragility": "Check neighboring parameter cells before trusting the selected variant.",
        "Leakage risk": "Verify point-in-time lineage before accepting model inputs.",
    }
    return mapping.get(mistake_name, "Turn the evidence gap into a repeatable review habit.")
