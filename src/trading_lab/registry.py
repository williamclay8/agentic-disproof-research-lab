"""Hypothesis registry loading for pre-registered offline research claims."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from trading_lab.models import Hypothesis


SCHEMA_VERSION = 1


def load_hypothesis(path: str | Path) -> Hypothesis:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported hypothesis registry schema_version")
    _reject_execution_surface(payload)

    return Hypothesis(
        id=payload["id"],
        thesis=payload["thesis"],
        null_hypothesis=payload["null_hypothesis"],
        asset_universe=list(payload["asset_universe"]),
        time_horizon=payload["time_horizon"],
        signal_definition=payload["signal_definition"],
        expected_failure_modes=list(payload.get("expected_failure_modes", [])),
        falsification_tests=list(payload.get("falsification_tests", [])),
        pre_registered_metrics=list(payload.get("pre_registered_metrics", [])),
        acceptance_thresholds=dict(payload.get("acceptance_thresholds", {})),
        data_requirements=list(payload.get("data_requirements", [])),
        posthoc_edit_policy=payload.get("posthoc_edit_policy", ""),
    )


def validate_hypothesis_registry(path: str | Path) -> list[Hypothesis]:
    registry_path = Path(path)
    files = (
        sorted(registry_path.glob("*.json"))
        if registry_path.is_dir()
        else [registry_path]
    )
    hypotheses = [load_hypothesis(file_path) for file_path in files]

    seen: set[str] = set()
    for hypothesis in hypotheses:
        if hypothesis.id in seen:
            raise ValueError(f"duplicate hypothesis id: {hypothesis.id}")
        seen.add(hypothesis.id)

    return hypotheses


def _reject_execution_surface(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, sort_keys=True).lower()
    forbidden_terms = {
        "broker_api",
        "place_order",
        "submit_order",
        "live_data",
        "paper_trading",
        "credentials",
        "api_key",
        "secret",
        "websocket",
        "alpaca",
        "ibkr",
        "interactive_brokers",
        "coinbase",
        "binance",
    }
    for term in forbidden_terms:
        if term in text:
            raise ValueError(f"execution surface is not allowed: {term}")
