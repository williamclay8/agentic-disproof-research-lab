"""Durable JSON artifacts for offline research runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from trading_lab.models import (
    BacktestResult,
    BacktestSpec,
    DatasetManifest,
    GateResult,
    Hypothesis,
    ReportVerdict,
)


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ResearchRunArtifact:
    run_id: str
    verdict: ReportVerdict
    hypothesis: Hypothesis
    manifest: DatasetManifest
    spec: BacktestSpec
    result: BacktestResult
    gate_results: list[GateResult]
    limitations: list[str]
    next_tests: list[str]

    @property
    def disproof_score(self) -> int:
        score = 0
        for gate in self.gate_results:
            if gate.status == "fail" and gate.severity == "critical":
                score += 3
            elif gate.status == "fail":
                score += 2
            elif gate.status == "warn":
                score += 2
        return score


def write_run_artifact(path: Path, artifact: ResearchRunArtifact) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_to_payload(artifact), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def read_run_artifact(path: Path) -> ResearchRunArtifact:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported run artifact schema_version")

    return ResearchRunArtifact(
        run_id=payload["run_id"],
        verdict=payload["verdict"],
        hypothesis=Hypothesis(**payload["hypothesis"]),
        manifest=DatasetManifest(**payload["manifest"]),
        spec=BacktestSpec(**payload["spec"]),
        result=BacktestResult(**payload["result"]),
        gate_results=[GateResult(**gate) for gate in payload["gate_results"]],
        limitations=list(payload["limitations"]),
        next_tests=list(payload["next_tests"]),
    )


def _to_payload(artifact: ResearchRunArtifact) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": artifact.run_id,
        "verdict": artifact.verdict,
        "disproof_score": artifact.disproof_score,
        "hypothesis": asdict(artifact.hypothesis),
        "manifest": asdict(artifact.manifest),
        "spec": asdict(artifact.spec),
        "result": asdict(artifact.result),
        "gate_results": [asdict(gate) for gate in artifact.gate_results],
        "limitations": artifact.limitations,
        "next_tests": artifact.next_tests,
    }
