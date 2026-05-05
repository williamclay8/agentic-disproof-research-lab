from __future__ import annotations

from trading_lab.agents import build_agentic_review
from trading_lab.models import GateResult


def test_agentic_review_returns_the_six_named_research_roles() -> None:
    review = build_agentic_review(
        gate_results=[_gate("chronology", "pass", "info")],
        next_tests=[],
        limitations=[],
    )

    assert [role["name"] for role in review["roles"]] == [
        "Leak Auditor",
        "Baseline Challenger",
        "Cost Stress Critic",
        "Reproducibility Clerk",
        "Promotion Gatekeeper",
        "Regime Skeptic",
    ]
    assert all(role["boundary"] == "offline research evidence only" for role in review["roles"])


def test_agentic_review_prioritizes_fails_then_warnings_deterministically() -> None:
    review = build_agentic_review(
        gate_results=[
            _gate("baseline comparison", "warn", "warning"),
            _gate("cost realism", "fail", "critical"),
            _gate("chronology", "pass", "info"),
            _gate("lookahead columns", "fail", "critical"),
            _gate("cost sensitivity", "warn", "warning"),
        ],
        next_tests=["replay with higher costs", "repeat walk-forward folds"],
        limitations=["small local sample"],
    )

    assert [(item["status"], item["gate_name"]) for item in review["findings"][:4]] == [
        ("fail", "cost realism"),
        ("fail", "lookahead columns"),
        ("warn", "baseline comparison"),
        ("warn", "cost sensitivity"),
    ]
    assert review["ranked_next_actions"][:4] == [
        "Quarantine cost realism until critical failure evidence is resolved.",
        "Quarantine lookahead columns until critical failure evidence is resolved.",
        "Retest baseline comparison against stricter offline evidence.",
        "Retest cost sensitivity against stricter offline evidence.",
    ]


def test_agentic_review_language_stays_research_only_and_non_actionable() -> None:
    review = build_agentic_review(
        gate_results=[_gate("baseline comparison", "warn", "warning")],
        next_tests=["add parameter sensitivity grid"],
        limitations=["single offline fixture"],
    )

    assert review["promotion_decision"] == {
        "decision": "research-only hold",
        "reason": "Warning evidence remains open; continue offline falsification before promotion.",
        "boundary": "Not investment advice; no live trading, broker connection, account action, allocation, or execution action.",
    }

    text = str(review).lower()
    for forbidden in [
        "buy now",
        "sell now",
        "place order",
        "submit order",
        "position-size",
        "position sizing",
        "recommended allocation",
        "trade recommendation",
        "broker api",
    ]:
        assert forbidden not in text


def test_agentic_review_promotes_only_as_preliminary_research_when_all_gates_pass() -> None:
    review = build_agentic_review(
        gate_results=[
            _gate("chronology", "pass", "info"),
            _gate("baseline comparison", "pass", "info"),
            _gate("reproducibility", "pass", "info"),
        ],
        next_tests=[],
        limitations=[],
    )

    assert review["promotion_decision"]["decision"] == "passed preliminary research gates"
    assert "harder falsification" in review["ranked_next_actions"][0]


def _gate(name: str, status: str, severity: str) -> GateResult:
    return GateResult(
        gate_name=name,
        status=status,
        evidence={"recorded": True},
        threshold="evidence recorded",
        remediation_hint=f"Resolve {name} evidence gap.",
        severity=severity,
    )
