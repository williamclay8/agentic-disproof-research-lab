from __future__ import annotations

import json
from pathlib import Path

from trading_lab.fomo_hypothesis_factory import (
    build_fomo_hypothesis_factory,
    render_fomo_hypothesis_factory_markdown,
)
from trading_lab.fomo_plays import build_985monitor_snapshot_summary


def test_hypothesis_factory_finds_candidate_edge_without_validating_it():
    factory = build_fomo_hypothesis_factory(build_985monitor_snapshot_summary())

    assert factory["mode"] == "research_only"
    assert factory["research_only"] is True
    assert factory["schema_version"] == 1
    assert factory["edge_status"] == "candidate_edge_found_not_validated"
    assert factory["validated_edge_found"] is False
    assert factory["best_candidate_edge_id"] == "pnl_window_persistence"
    assert len(factory["candidate_edges"]) >= 5
    assert all(edge["verdict"] == "candidate_edge_unvalidated" for edge in factory["candidate_edges"])
    assert all(edge["baseline"] for edge in factory["candidate_edges"])
    assert all(edge["falsification_criteria"] for edge in factory["candidate_edges"])
    assert all(edge["next_safe_research_action"].startswith("Research:") for edge in factory["candidate_edges"])
    assert all(edge["promotion_blockers"] for edge in factory["candidate_edges"])


def test_hypothesis_factory_blocks_trade_and_signal_language():
    payload = build_fomo_hypothesis_factory(build_985monitor_snapshot_summary())
    serialized = json.dumps(payload).lower()

    required_blockers = [
        "personalized investment advice",
        "copy-trading instruction",
        "broker or order-routing action",
        "live signal",
        "raw wallet resale without rights review",
    ]
    for blocker in required_blockers:
        assert blocker in serialized

    forbidden_phrases = [
        "buy now",
        "sell now",
        "follow this wallet",
        "submit order",
        "guaranteed alpha",
        "validated edge",
    ]
    assert not any(phrase in serialized for phrase in forbidden_phrases)


def test_hypothesis_factory_markdown_reports_the_strongest_candidate_edge():
    factory = build_fomo_hypothesis_factory(build_985monitor_snapshot_summary())
    markdown = render_fomo_hypothesis_factory_markdown(factory)

    assert "# 985monitor FOMO Hypothesis Factory" in markdown
    assert "Best candidate edge: `pnl_window_persistence`" in markdown
    assert "No validated trading edge was found" in markdown
    assert "not a trade instruction" in markdown.lower()


def test_committed_hypothesis_factory_artifacts_match_contract():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads(
        (root / "runs/985monitor/hypothesis-factory.json").read_text(encoding="utf-8")
    )
    markdown = (root / "reports/985monitor-hypothesis-factory.md").read_text(
        encoding="utf-8"
    )

    assert payload["schema"] == "fomo_hypothesis_factory.v1"
    assert payload["schema_version"] == 1
    assert payload["best_candidate_edge_id"] == "pnl_window_persistence"
    assert payload["validated_edge_found"] is False
    assert payload["promotion_status"]["promotion_ready"] is False
    assert "No validated trading edge was found" in markdown
