from __future__ import annotations

import json
from pathlib import Path

from trading_lab.registry import load_hypothesis
from trading_lab.fomo_plays import (
    PLAY_IDS,
    build_985monitor_snapshot_summary,
    build_fomo_playbook,
    render_fomo_playbook_markdown,
)


def test_fomo_playbook_completes_all_five_research_only_plays():
    summary = build_985monitor_snapshot_summary()
    playbook = build_fomo_playbook(summary)

    assert playbook["mode"] == "research_only"
    assert playbook["research_only"] is True
    assert playbook["source"]["snapshot_timestamp_utc"] == "2026-05-03T12:06:00Z"
    assert playbook["source"]["freshness_status"] == "stale_snapshot"
    assert playbook["dataset_summary"]["pnl_union_unique_identities"] == 116
    assert len(playbook["dataset_summary"]["csv_manifests"]) == 5
    assert [play["id"] for play in playbook["plays"]] == list(PLAY_IDS)
    assert all(play["completion_artifact"] for play in playbook["plays"])
    assert all(play["revenue_mechanism"] for play in playbook["plays"])
    assert all(play["proof_gates"] for play in playbook["plays"])
    assert all(play["blocked_outputs"] for play in playbook["plays"])
    assert all(play["research_only"] is True for play in playbook["plays"])


def test_fomo_playbook_keeps_unsafe_financial_actions_blocked():
    payload = build_fomo_playbook(build_985monitor_snapshot_summary())
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
    ]
    assert not any(phrase in serialized for phrase in forbidden_phrases)


def test_fomo_playbook_markdown_names_each_deliverable_and_gate():
    markdown = render_fomo_playbook_markdown(
        build_fomo_playbook(build_985monitor_snapshot_summary())
    )

    assert "# 985monitor FOMO Research Playbook" in markdown
    assert "Paid KOL Wallet Falsification Report" in markdown
    assert "Anti-Copy Wallet Quality Score" in markdown
    assert "KOL Campaign Forensics Template" in markdown
    assert "Derived Aggregate Dataset Licensing Packet" in markdown
    assert "Trading Lab Hypothesis Factory" in markdown
    assert "not a trade instruction" in markdown.lower()


def test_committed_fomo_playbook_artifacts_match_research_contract():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads(
        (root / "runs/985monitor/fomo-playbook.json").read_text(encoding="utf-8")
    )
    markdown = (root / "docs/985monitor-fomo-research-playbook.md").read_text(
        encoding="utf-8"
    )

    assert payload["mode"] == "research_only"
    assert payload["promotion_status"]["promotion_ready"] is False
    assert payload["promotion_status"]["status"] == "blocked_by_incomplete_provenance"
    assert payload["completed_plays_count"] == 5
    assert len(payload["dataset_summary"]["csv_manifests"]) == 5
    assert all(
        manifest["provenance_status"] == "incomplete"
        for manifest in payload["dataset_summary"]["csv_manifests"]
    )
    assert all(
        manifest["sha256"]
        for manifest in payload["dataset_summary"]["csv_manifests"]
    )
    assert markdown.count("### ") == 10
    assert "Vanta" not in markdown
    assert "Not investment advice" in markdown
    assert "personalized investment advice" in json.dumps(payload)
    paid_play = next(
        play for play in payload["plays"] if play["id"] == "paid_falsification_report"
    )
    assert (
        paid_play["completion_artifact"]
        == "reports/985monitor-paid-kol-wallet-falsification-report.md"
    )


def test_985monitor_hypothesis_registry_loads_and_blocks_promotion_language():
    root = Path(__file__).resolve().parents[1]
    hypothesis = load_hypothesis(
        root / "hypotheses/985monitor-fomo-wallet-falsification.json"
    )

    assert hypothesis.id == "985monitor-fomo-wallet-falsification"
    assert "no live signal horizon" in hypothesis.time_horizon
    assert "provenance_rights_review" in hypothesis.falsification_tests
    assert "order" not in json.dumps(hypothesis.__dict__).lower()


def test_paid_kol_wallet_falsification_report_is_client_ready_and_blocked():
    root = Path(__file__).resolve().parents[1]
    report = (
        root / "reports/985monitor-paid-kol-wallet-falsification-report.md"
    ).read_text(encoding="utf-8")
    packet = json.loads(
        (
            root / "runs/985monitor/paid-kol-wallet-falsification-report.json"
        ).read_text(encoding="utf-8")
    )

    assert packet["mode"] == "research_only"
    assert packet["research_only"] is True
    assert packet["falsification_verdict"]["status"] == "inconclusive_blocked"
    assert packet["falsification_verdict"]["promotion_ready"] is False
    assert packet["deliverable_status"]["complete_as_research_deliverable"] is True
    assert "Buyer-Ready Offer" in report
    assert "Proof Gates Before Stronger Claims" in report
    assert "Not investment advice" in report
    assert "not a current trading edge" in report
    forbidden_phrases = [
        "buy now",
        "sell now",
        "follow this wallet",
        "submit order",
        "guaranteed alpha",
    ]
    assert not any(phrase in report.lower() for phrase in forbidden_phrases)
