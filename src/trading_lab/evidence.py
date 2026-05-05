"""Evidence rigor helpers for offline research falsification workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


BASE_POINT_IN_TIME_FIELDS = frozenset(
    {
        "date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }
)
LEAKAGE_MARKERS = ("future", "forward", "target", "label")
REQUIRED_BASELINES = (
    "buy-and-hold",
    "equal-weight",
    "naive-momentum",
    "naive-mean-reversion",
    "random-control",
)
RESEARCH_ONLY_WORDING = (
    "research-only offline falsification contract; not investment advice; "
    "no live account activity."
)


@dataclass(frozen=True)
class PointInTimeFieldContract:
    allowed: list[str]
    leakage_suspect: list[str]
    unknown_lineage: list[str]
    evidence_gaps: list[str]


@dataclass(frozen=True)
class BaselineDescriptor:
    name: str
    description: str
    contract: str
    research_only_wording: str = RESEARCH_ONLY_WORDING


@dataclass(frozen=True)
class EvidenceRigorSummary:
    score: int
    status: str
    allowed_fields: list[str]
    leakage_suspect_fields: list[str]
    unknown_lineage_fields: list[str]
    present_baselines: list[str]
    missing_baselines: list[str]
    evidence_gaps: list[str]
    wording: str = RESEARCH_ONLY_WORDING


def classify_point_in_time_fields(
    columns: Iterable[str],
    *,
    known_point_in_time_fields: Iterable[str] = (),
) -> PointInTimeFieldContract:
    """Classify dataset columns by point-in-time evidence risk."""

    allowed_fields = BASE_POINT_IN_TIME_FIELDS | set(known_point_in_time_fields)
    allowed: set[str] = set()
    leakage_suspect: set[str] = set()
    unknown_lineage: set[str] = set()

    for column in columns:
        normalized = column.strip()
        if not normalized:
            continue
        key = normalized.lower()

        if key in allowed_fields:
            allowed.add(normalized)
        elif any(marker in key for marker in LEAKAGE_MARKERS):
            leakage_suspect.add(normalized)
        else:
            unknown_lineage.add(normalized)

    return PointInTimeFieldContract(
        allowed=sorted(allowed),
        leakage_suspect=sorted(leakage_suspect),
        unknown_lineage=sorted(unknown_lineage),
        evidence_gaps=[f"unknown_lineage:{field}" for field in sorted(unknown_lineage)],
    )


def baseline_pack() -> Mapping[str, BaselineDescriptor]:
    """Return deterministic descriptor contracts for required research baselines."""

    return {
        "buy-and-hold": BaselineDescriptor(
            name="buy-and-hold",
            description="Research-only offline comparator for holding the universe through the sample.",
            contract="Defines a passive sample baseline for falsification; not investment advice.",
        ),
        "equal-weight": BaselineDescriptor(
            name="equal-weight",
            description="Research-only offline comparator with equal allocation across eligible symbols.",
            contract="Defines a simple cross-sectional baseline for falsification; not investment advice.",
        ),
        "naive-momentum": BaselineDescriptor(
            name="naive-momentum",
            description="Research-only offline comparator that ranks recent relative strength.",
            contract="Defines a minimal momentum baseline for falsification; not investment advice.",
        ),
        "naive-mean-reversion": BaselineDescriptor(
            name="naive-mean-reversion",
            description="Research-only offline comparator that ranks recent relative weakness.",
            contract="Defines a minimal reversion baseline for falsification; not investment advice.",
        ),
        "random-control": BaselineDescriptor(
            name="random-control",
            description="Research-only offline comparator for seeded random selection controls.",
            contract="Defines a deterministic null-control baseline for falsification; not investment advice.",
        ),
    }


def summarize_evidence_rigor(
    columns: Iterable[str],
    *,
    baseline_names: Iterable[str] = (),
    known_point_in_time_fields: Iterable[str] = (),
) -> EvidenceRigorSummary:
    contract = classify_point_in_time_fields(
        columns,
        known_point_in_time_fields=known_point_in_time_fields,
    )
    present_baselines = sorted(set(baseline_names) & set(REQUIRED_BASELINES))
    missing_baselines = sorted(set(REQUIRED_BASELINES) - set(present_baselines))
    evidence_gaps = [
        *(f"leakage_suspect:{field}" for field in contract.leakage_suspect),
        *(f"unknown_lineage:{field}" for field in contract.unknown_lineage),
        *(f"missing_baseline:{name}" for name in missing_baselines),
    ]
    score = max(0, 100 - (10 * len(evidence_gaps)))

    return EvidenceRigorSummary(
        score=score,
        status="ready" if not evidence_gaps else "needs_evidence",
        allowed_fields=contract.allowed,
        leakage_suspect_fields=contract.leakage_suspect,
        unknown_lineage_fields=contract.unknown_lineage,
        present_baselines=present_baselines,
        missing_baselines=missing_baselines,
        evidence_gaps=evidence_gaps,
    )
