"""Deterministic agent-role review for offline research evidence."""

from __future__ import annotations

import re
from typing import Any

from trading_lab.models import GateResult


AGENT_ROLES = [
    {
        "name": "Leak Auditor",
        "reviewer_id": "leak_auditor",
        "focus": "Feature timing, chronology, schema, and forward-looking evidence.",
        "boundary": "offline research evidence only",
        "owned_artifact_types": ["point_in_time_contract", "leakage_audit"],
    },
    {
        "name": "Baseline Challenger",
        "reviewer_id": "baseline_challenger",
        "focus": "Same-sample comparator discipline and baseline weakness.",
        "boundary": "offline research evidence only",
        "owned_artifact_types": ["baseline_pack_result"],
    },
    {
        "name": "Cost Stress Critic",
        "reviewer_id": "cost_stress_critic",
        "focus": "Fees, slippage, delay, and cost-stress fragility.",
        "boundary": "offline research evidence only",
        "owned_artifact_types": ["cost_stress_packet"],
    },
    {
        "name": "Reproducibility Clerk",
        "reviewer_id": "reproducibility_clerk",
        "focus": "Fingerprints, repeatability, manifests, and missing evidence records.",
        "boundary": "offline research evidence only",
        "owned_artifact_types": ["reproducibility_manifest"],
    },
    {
        "name": "Promotion Gatekeeper",
        "reviewer_id": "promotion_gatekeeper",
        "focus": "Research-only promotion state from recorded gate evidence.",
        "boundary": "offline research evidence only",
        "owned_artifact_types": ["readiness_packet"],
    },
    {
        "name": "Regime Skeptic",
        "reviewer_id": "regime_skeptic",
        "focus": "Walk-forward, parameter, and regime-fragility evidence.",
        "boundary": "offline research evidence only",
        "owned_artifact_types": ["walk_forward_regime_pack"],
    },
]


def build_agentic_review(
    gate_results: list[GateResult],
    next_tests: list[str],
    limitations: list[str],
    *,
    source_ref: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic research-only review from recorded gate evidence."""

    ordered_gates = _ordered_gates(gate_results)
    repeat_counts = _repeat_counts(ordered_gates)
    findings = [
        _finding(
            sequence=sequence,
            gate=gate,
            repeated_finding_count=repeat_counts[gate.gate_name],
            source_ref=source_ref,
        )
        for sequence, gate in enumerate(ordered_gates, start=1)
    ]
    ranked_next_actions = _ranked_next_actions(gate_results, next_tests, limitations)
    return {
        "roles": [dict(role) for role in AGENT_ROLES],
        "findings": findings,
        "reviewer_scorecard": _reviewer_scorecard(findings),
        "repeated_findings": _repeated_findings(repeat_counts),
        "ranked_next_actions": ranked_next_actions,
        "promotion_decision": _promotion_decision(gate_results),
    }


def _ordered_gates(gate_results: list[GateResult]) -> list[GateResult]:
    return sorted(
        gate_results,
        key=lambda gate: (
            {"fail": 0, "warn": 1, "pass": 2}.get(gate.status, 3),
            {"critical": 0, "warning": 1, "info": 2}.get(gate.severity, 3),
            gate.gate_name,
        ),
    )


def _finding(
    *,
    sequence: int,
    gate: GateResult,
    repeated_finding_count: int,
    source_ref: str | None,
) -> dict[str, Any]:
    role = _role_for_gate(gate.gate_name)
    role_record = _role_record(role)
    reviewer_id = str(role_record["reviewer_id"])
    gate_slug = _slug(gate.gate_name)
    return {
        "reviewer_artifact_id": (
            f"review-artifact-{reviewer_id.replace('_', '-')}-{gate_slug}-{sequence}"
        ),
        "reviewer_id": reviewer_id,
        "role": role,
        "owned_artifact_type": role_record["owned_artifact_types"][0],
        "gate_name": gate.gate_name,
        "status": gate.status,
        "severity": gate.severity,
        "score": _finding_score(gate),
        "repeated_finding_count": repeated_finding_count,
        "source_refs": _source_refs(gate, source_ref),
        "finding": _finding_text(gate),
        "remediation_hint": gate.remediation_hint,
    }


def _finding_text(gate: GateResult) -> str:
    if gate.status == "pass":
        return "Recorded evidence satisfied this offline research control."
    if gate.status == "warn":
        return "Recorded evidence raised a warning that needs harder offline review."
    return "Recorded evidence failed this control and weighs against promotion."


def _ranked_next_actions(
    gate_results: list[GateResult],
    next_tests: list[str],
    limitations: list[str],
) -> list[str]:
    actions: list[str] = []
    for gate in _ordered_gates(gate_results):
        if gate.status == "fail":
            actions.append(
                f"Quarantine {gate.gate_name} until critical failure evidence is resolved."
            )
        elif gate.status == "warn":
            actions.append(
                f"Retest {gate.gate_name} against stricter offline evidence."
            )

    actions.extend(f"Run next offline test: {test}" for test in next_tests)
    actions.extend(f"Document limitation before promotion: {item}" for item in limitations)

    if not actions:
        actions.append(
            "Archive the run as reviewed, then design a harder falsification pass."
        )
    return actions


def _reviewer_scorecard(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scorecard: list[dict[str, Any]] = []
    for role in AGENT_ROLES:
        role_findings = [
            finding for finding in findings if finding["role"] == role["name"]
        ]
        scores = [int(finding["score"]) for finding in role_findings]
        source_refs = sorted(
            {
                source_ref
                for finding in role_findings
                for source_ref in finding.get("source_refs", [])
            }
        )
        repeated_count = sum(
            1
            for finding in role_findings
            if int(finding.get("repeated_finding_count", 0)) > 1
        )
        scorecard.append(
            {
                "reviewer_id": role["reviewer_id"],
                "role": role["name"],
                "owned_artifact_types": list(role["owned_artifact_types"]),
                "finding_count": len(role_findings),
                "open_finding_count": sum(
                    1 for finding in role_findings if finding["status"] != "pass"
                ),
                "repeated_finding_count": repeated_count,
                "max_score": max(scores) if scores else 0,
                "average_score": round(sum(scores) / len(scores), 2)
                if scores
                else 0,
                "source_refs": source_refs,
            }
        )
    return scorecard


def _repeated_findings(repeat_counts: dict[str, int]) -> list[dict[str, int | str]]:
    return [
        {"gate_name": gate_name, "count": count}
        for gate_name, count in sorted(repeat_counts.items())
        if count > 1
    ]


def _repeat_counts(gate_results: list[GateResult]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for gate in gate_results:
        counts[gate.gate_name] = counts.get(gate.gate_name, 0) + 1
    return counts


def _promotion_decision(gate_results: list[GateResult]) -> dict[str, str]:
    boundary = (
        "Not investment advice; no live trading, broker connection, account action, "
        "allocation, or execution action."
    )
    if any(gate.status == "fail" for gate in gate_results):
        return {
            "decision": "research-only blocked",
            "reason": "Failure evidence remains open; quarantine the claim for offline review.",
            "boundary": boundary,
        }
    if any(gate.status == "warn" for gate in gate_results):
        return {
            "decision": "research-only hold",
            "reason": "Warning evidence remains open; continue offline falsification before promotion.",
            "boundary": boundary,
        }
    return {
        "decision": "passed preliminary research gates",
        "reason": "All recorded gates passed; promote only as an offline research artifact.",
        "boundary": boundary,
    }


def _role_for_gate(gate_name: str) -> str:
    normalized = gate_name.lower()
    if any(term in normalized for term in ("lookahead", "chronology", "schema")):
        return "Leak Auditor"
    if "baseline" in normalized or "comparator" in normalized:
        return "Baseline Challenger"
    if "cost" in normalized or "slippage" in normalized or "delay" in normalized:
        return "Cost Stress Critic"
    if "reproduc" in normalized or "fingerprint" in normalized:
        return "Reproducibility Clerk"
    if any(term in normalized for term in ("walk-forward", "parameter", "regime")):
        return "Regime Skeptic"
    return "Promotion Gatekeeper"


def _role_record(role_name: str) -> dict[str, Any]:
    for role in AGENT_ROLES:
        if role["name"] == role_name:
            return role
    return AGENT_ROLES[4]


def _finding_score(gate: GateResult) -> int:
    severity_weight = {"critical": 40, "warning": 25, "info": 10}[gate.severity]
    status_weight = {"fail": 60, "warn": 35, "pass": 0}[gate.status]
    return min(status_weight + severity_weight, 100)


def _source_refs(gate: GateResult, source_ref: str | None) -> list[str]:
    refs: list[str] = []
    for key in ("source_refs", "evidence_refs"):
        values = gate.evidence.get(key)
        if isinstance(values, list):
            refs.extend(str(value) for value in values if str(value).strip())
    direct = gate.evidence.get("source_ref")
    if isinstance(direct, str) and direct.strip():
        refs.append(direct)
    if source_ref:
        refs.append(f"{source_ref}#gate:{_slug(gate.gate_name)}")
    if not refs:
        refs.append(f"gate:{_slug(gate.gate_name)}")
    return _dedupe(refs)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
