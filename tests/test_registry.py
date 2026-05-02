from __future__ import annotations

import json

import pytest

from trading_lab.registry import load_hypothesis, validate_hypothesis_registry


def test_load_hypothesis_from_registry_json(tmp_path):
    path = tmp_path / "hypothesis.json"
    path.write_text(json.dumps(_payload()), encoding="utf-8")

    hypothesis = load_hypothesis(path)

    assert hypothesis.id == "toy-moving-average-crossover"
    assert hypothesis.asset_universe == ["AAA", "BBB"]
    assert "walk_forward" in hypothesis.falsification_tests


def test_registry_rejects_unknown_schema_version(tmp_path):
    payload = _payload()
    payload["schema_version"] = 999
    path = tmp_path / "hypothesis.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="schema_version"):
        load_hypothesis(path)


def test_registry_validation_rejects_duplicate_hypothesis_ids(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps(_payload()), encoding="utf-8")
    second.write_text(json.dumps(_payload()), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate hypothesis id"):
        validate_hypothesis_registry(tmp_path)


def _payload() -> dict:
    return {
        "schema_version": 1,
        "id": "toy-moving-average-crossover",
        "status": "active",
        "registered_at": "2026-05-02T00:00:00Z",
        "thesis": "A toy moving-average crossover may beat an offline comparator.",
        "null_hypothesis": "The crossover has no edge after costs.",
        "asset_universe": ["AAA", "BBB"],
        "time_horizon": "daily bars over a tiny educational sample",
        "signal_definition": "Moving-average crossover on toy bars.",
        "expected_failure_modes": ["lookahead leakage", "cost fragility"],
        "falsification_tests": [
            "lookahead columns",
            "baseline comparison",
            "walk_forward",
            "parameter_sensitivity",
            "cost_grid",
        ],
        "pre_registered_metrics": [
            "strategy_cumulative_return",
            "baseline_cumulative_return",
        ],
        "acceptance_thresholds": {
            "baseline_comparison": "strategy_cumulative_return > baseline"
        },
        "data_requirements": ["local CSV only"],
        "posthoc_edit_policy": "No edits after observing results.",
    }
