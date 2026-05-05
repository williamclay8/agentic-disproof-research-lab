"""Deterministic agent-role review for offline research evidence."""

from __future__ import annotations

from typing import Any

from trading_lab.models import GateResult


AGENT_ROLES = [
    {
        "name": "Leak Auditor",
        "focus": "Feature timing, chronology, schema, and forward-looking evidence.",
        "boundary": "offline research evidence only",
    },
    {
        "name": "Baseline Challenger",
        "focus": "Same-sample comparator discipline and baseline weakness.",
        "boundary": "offline research evidence only",
    },
    {
        "name": "Cost Stress Critic",
        "focus": "Fees, slippage, delay, and cost-stress fragility.",
        "boundary": "offline research evidence only",
    },
    {
        "name": "Reproducibility Clerk",
        "focus": "Fingerprints, repeatability, manifests, and missing evidence records.",
        "boundary": "offline research evidence only",
    },
    {
        "name": "Promotion Gatekeeper",
        "focus": "Research-only promotion state from recorded gate evidence.",
        "boundary": "offline research evidence only",
    },
    {
        "name": "Regime Skeptic",
        "focus": "Walk-forward, parameter, and regime-fragility evidence.",
        "boundary": "offline research evidence only",
    },
]


def build_agentic_review(
    gate_results: list[GateResult],
    next_tests: list[str],
    limitations: list[str],
) -> dict[str, Any]:
    """Build a deterministic research-only review from recorded gate evidence."""

    findings = [_finding(gate) for gate in _ordered_gates(gate_results)]
    ranked_next_actions = _ranked_next_actions(gate_results, next_tests, limitations)
    return {
        "roles": [dict(role) for role in AGENT_ROLES],
        "findings": findings,
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


def _finding(gate: GateResult) -> dict[str, str]:
    return {
        "role": _role_for_gate(gate.gate_name),
        "gate_name": gate.gate_name,
        "status": gate.status,
        "severity": gate.severity,
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
    if "baseline" in normalized:
        return "Baseline Challenger"
    if "cost" in normalized or "slippage" in normalized or "delay" in normalized:
        return "Cost Stress Critic"
    if "reproduc" in normalized or "fingerprint" in normalized:
        return "Reproducibility Clerk"
    if any(term in normalized for term in ("walk-forward", "parameter", "regime")):
        return "Regime Skeptic"
    return "Promotion Gatekeeper"
