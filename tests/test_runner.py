from __future__ import annotations

from trading_lab.artifacts import ResearchRunArtifact
from trading_lab.gates import choose_verdict
from trading_lab.registry import load_hypothesis
from trading_lab.runner import DisproofConfig, run_disproof


def test_run_disproof_builds_complete_artifact_from_registry():
    hypothesis = load_hypothesis("hypotheses/toy-moving-average-crossover.json")

    artifact = run_disproof(
        hypothesis=hypothesis,
        dataset_path="examples/toy_prices.csv",
        config=DisproofConfig(short_window=2, long_window=3),
    )

    assert isinstance(artifact, ResearchRunArtifact)
    assert artifact.run_id.startswith("toy-moving-average-crossover")
    assert artifact.hypothesis.id == "toy-moving-average-crossover"
    assert artifact.verdict == choose_verdict(artifact.gate_results)
    gate_names = {gate.gate_name for gate in artifact.gate_results}
    assert "walk-forward robustness" in gate_names
    assert "parameter sensitivity" in gate_names
    assert "cost grid robustness" in gate_names
    assert artifact.result.fingerprint
