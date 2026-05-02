"""Training views for improving offline falsification discipline."""

from __future__ import annotations

from trading_lab.artifacts import ResearchRunArtifact
from trading_lab.models import GateResult


CORE_EVIDENCE_GATES = [
    "schema columns",
    "chronology",
    "lookahead columns",
    "baseline comparison",
    "cost realism",
    "cost sensitivity",
    "reproducibility",
    "walk-forward robustness",
    "parameter sensitivity",
    "cost grid robustness",
]


def research_maturity_score(gate_results: list[GateResult]) -> dict[str, object]:
    recorded = {gate.gate_name for gate in gate_results}
    covered = [gate for gate in CORE_EVIDENCE_GATES if gate in recorded]
    score = round((len(covered) / len(CORE_EVIDENCE_GATES)) * 100)
    return {
        "score": score,
        "label": _maturity_label(score),
        "components": [f"{gate}: recorded" for gate in covered],
        "missing": [gate for gate in CORE_EVIDENCE_GATES if gate not in recorded],
    }


def build_mistake_taxonomy(gate_results: list[GateResult]) -> list[dict[str, str]]:
    taxonomy: list[dict[str, str]] = []
    for gate in gate_results:
        if gate.status == "pass":
            continue
        taxonomy.append(_taxonomy_item(gate.gate_name))
    return taxonomy


def build_training_plan() -> list[dict[str, object]]:
    phases = [
        ("Pre-registration", "claims, null hypotheses, and edit policies"),
        ("Data Integrity", "schema, chronology, manifests, and hashes"),
        ("Leakage Control", "lookahead scans, feature timing, and embargo notes"),
        ("Comparator Discipline", "same-bar baselines and comparator deltas"),
        ("Cost Friction", "fees, slippage, delay, and cost-grid evidence"),
        ("Fold Robustness", "walk-forward folds and fold-level evidence"),
        ("Parameter Robustness", "neighborhood grids and fragility records"),
        ("Multiple Testing", "trial counts, selection pressure, and p-hacking notes"),
        ("Report Skepticism", "limitations, evidence gaps, and disproof summaries"),
        ("Agent Review", "independent critique, audit trails, and repeatability"),
    ]
    plan = []
    for round_number in range(1, 101):
        phase, focus = phases[(round_number - 1) // 10]
        plan.append(
            {
                "round": round_number,
                "phase": phase,
                "focus": f"{phase}: record {focus} for offline evidence review.",
            }
        )
    return plan


def build_experiment_ledger(
    artifacts: list[ResearchRunArtifact],
) -> list[dict[str, object]]:
    grouped: dict[str, list[ResearchRunArtifact]] = {}
    for artifact in artifacts:
        grouped.setdefault(artifact.hypothesis.id, []).append(artifact)

    rows: list[dict[str, object]] = []
    for hypothesis_id, runs in sorted(grouped.items()):
        mistake_names: list[str] = []
        open_gaps: list[str] = []
        for run in runs:
            mistake_names.extend(
                item["name"] for item in build_mistake_taxonomy(run.gate_results)
            )
            open_gaps.extend(run.next_tests)

        recurring = sorted(set(mistake_names))
        rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "runs": len(runs),
                "latest_verdict": runs[-1].verdict,
                "worst_disproof_score": max(run.disproof_score for run in runs),
                "recurring_mistake_types": ", ".join(recurring) if recurring else "None recorded",
                "open_evidence_gaps": ", ".join(sorted(set(open_gaps))) if open_gaps else "None recorded",
                "next_curriculum_round": _next_curriculum_round(recurring),
            }
        )
    return rows


def _maturity_label(score: int) -> str:
    if score >= 80:
        return "substantial evidence coverage"
    if score >= 50:
        return "partial evidence coverage"
    return "thin evidence coverage"


def _taxonomy_item(gate_name: str) -> dict[str, str]:
    mapping = {
        "baseline comparison": (
            "Comparator weakness",
            "Comparator evidence weakened the claim; focus on same-sample baseline discipline.",
        ),
        "walk-forward robustness": (
            "Fold fragility",
            "Fold evidence weakened the claim; focus on out-of-sample chronology.",
        ),
        "parameter sensitivity": (
            "Parameter fragility",
            "Parameter-grid evidence weakened the claim; focus on neighborhood stability.",
        ),
        "cost grid robustness": (
            "Cost fragility",
            "Cost-grid evidence weakened the claim; focus on friction assumptions.",
        ),
        "lookahead columns": (
            "Leakage risk",
            "Forward-looking evidence was recorded; focus on feature timing.",
        ),
    }
    name, learning_focus = mapping.get(
        gate_name,
        ("Evidence gap", f"{gate_name} recorded a non-pass status for review."),
    )
    return {
        "gate_name": gate_name,
        "name": name,
        "learning_focus": learning_focus,
    }


def _next_curriculum_round(mistake_names: list[str]) -> int:
    if "Comparator weakness" in mistake_names:
        return 31
    if "Cost fragility" in mistake_names:
        return 41
    if "Fold fragility" in mistake_names:
        return 51
    if "Parameter fragility" in mistake_names:
        return 61
    if "Leakage risk" in mistake_names:
        return 21
    return 1
