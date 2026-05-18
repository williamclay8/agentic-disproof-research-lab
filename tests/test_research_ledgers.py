from __future__ import annotations

from dataclasses import asdict
import json

from trading_lab.agents import build_agentic_review
from trading_lab.control_plane import build_lab_control_plane
from trading_lab.data import load_price_csv
from trading_lab.evidence import REQUIRED_BASELINES, summarize_evidence_rigor
from trading_lab.example import build_example_hypothesis, resolve_toy_prices_path
from trading_lab.platform import build_platform_overview
from trading_lab.research_ledgers import (
    build_action_guidance,
    build_baseline_pack_ledger,
    build_failure_gallery,
    build_point_in_time_proof,
    build_walk_forward_ledger,
)
from trading_lab.runner import DisproofConfig, run_disproof


def _artifact():
    return run_disproof(
        hypothesis=build_example_hypothesis(),
        dataset_path=resolve_toy_prices_path(),
        config=DisproofConfig(short_window=2, long_window=3),
    )


def test_baseline_pack_ledger_records_every_required_baseline_with_deltas():
    artifact = _artifact()
    rows = load_price_csv(resolve_toy_prices_path())

    ledger = build_baseline_pack_ledger(artifact, rows=rows, source_ref="runs/example-run.json")

    assert ledger["mode"] == "research_only"
    assert ledger["ledger_schema"] == "baseline_pack_ledger.v1"
    assert ledger["summary"]["required_baselines"] == list(REQUIRED_BASELINES)
    assert ledger["summary"]["recorded_baselines"] == list(REQUIRED_BASELINES)
    assert ledger["summary"]["missing_baselines"] == []
    assert ledger["summary"]["strongest_baseline"]
    assert {entry["name"] for entry in ledger["entries"]} == set(REQUIRED_BASELINES)

    buy_and_hold = next(entry for entry in ledger["entries"] if entry["name"] == "buy-and-hold")
    random_control = next(entry for entry in ledger["entries"] if entry["name"] == "random-control")

    assert buy_and_hold["source_metric"] == "result.metrics.baseline_cumulative_return"
    assert buy_and_hold["delta_vs_strategy"] < 0
    assert random_control["seed"] == artifact.manifest.content_hash[:12]
    assert all(entry["research_only"] is True for entry in ledger["entries"])
    assert _has_no_trade_instruction(ledger)


def test_walk_forward_ledger_turns_folds_into_regime_failure_records():
    artifact = _artifact()

    ledger = build_walk_forward_ledger(artifact, source_ref="runs/example-run.json")

    assert ledger["mode"] == "research_only"
    assert ledger["ledger_schema"] == "walk_forward_ledger.v1"
    assert ledger["summary"]["folds"] == 3
    assert ledger["summary"]["passing_folds"] == 0
    assert ledger["summary"]["pass_ratio"] == 0.0
    assert ledger["summary"]["status"] == "blocked_by_fold_fragility"
    assert [fold["fold_id"] for fold in ledger["folds"]] == [
        "fold:toy-moving-average-crossover-52635e40:1",
        "fold:toy-moving-average-crossover-52635e40:2",
        "fold:toy-moving-average-crossover-52635e40:3",
    ]
    assert all(fold["passed"] is False for fold in ledger["folds"])
    assert all(fold["regime_label"].startswith("chronological-window-") for fold in ledger["folds"])
    assert "baseline" in ledger["folds"][0]["primary_failure_reason"]
    assert _has_no_trade_instruction(ledger)


def test_point_in_time_proof_records_source_timestamp_and_field_lineage():
    artifact = _artifact()
    rigor = summarize_evidence_rigor(
        artifact.manifest.columns + ["future_return"],
        baseline_names=["buy-and-hold"],
    )
    snapshot = {
        "metadata": {
            "source_timestamp": "2026-05-02T14:11:53.334284-05:00",
            "provenance": {"source_ref": "Kraken public market data REST ticker"},
        }
    }

    proof = build_point_in_time_proof(
        artifact,
        evidence_summary=rigor,
        snapshot=snapshot,
        source_ref="runs/example-run.json",
    )

    assert proof["mode"] == "research_only"
    assert proof["proof_schema"] == "point_in_time_proof.v1"
    assert proof["source_timestamp"] == "2026-05-02T14:11:53.334284-05:00"
    assert proof["as_of_policy"] == "known-at-time inputs only"
    assert proof["status"] == "needs_review"
    future = next(field for field in proof["fields"] if field["name"] == "future_return")
    assert future["status"] == "leakage_suspect"
    assert future["known_at_time_proof"] == "blocked_until_reviewed"
    assert any(gap["id"] == "leakage_suspect:future_return" for gap in proof["unknown_lineage_escalations"])
    assert _has_no_trade_instruction(proof)


def test_failure_gallery_and_action_guidance_make_the_next_move_obvious():
    artifact = _artifact()
    readiness = {
        "current_stage": {"id": "observe_only", "label": "Observe-only"},
        "missing_checks": [{"id": "baseline_beaten", "label": "Comparator beaten"}],
    }
    baseline_ledger = build_baseline_pack_ledger(
        artifact,
        rows=load_price_csv(resolve_toy_prices_path()),
        source_ref="runs/example-run.json",
    )
    walk_forward_ledger = build_walk_forward_ledger(artifact, source_ref="runs/example-run.json")

    gallery = build_failure_gallery(
        artifact,
        baseline_ledger=baseline_ledger,
        walk_forward_ledger=walk_forward_ledger,
        source_ref="runs/example-run.json",
    )
    action = build_action_guidance(
        artifact,
        readiness=readiness,
        baseline_ledger=baseline_ledger,
        walk_forward_ledger=walk_forward_ledger,
        source_ref="runs/example-run.json",
    )

    assert gallery["gallery_schema"] == "failure_gallery.v1"
    assert [card["caught_by"] for card in gallery["cards"][:2]] == [
        "Baseline Challenger",
        "Regime Skeptic",
    ]
    assert all(card["what_would_change_our_mind"] for card in gallery["cards"])
    assert action["guidance_schema"] == "action_guidance.v1"
    assert action["plain_next_action"]["label"].startswith("Retest")
    assert action["expert_next_actions"][0]["source_ref"] == "runs/example-run.json"
    assert action["blocked_outputs"]
    assert _has_no_trade_instruction(gallery)
    assert _has_no_trade_instruction(action)


def test_platform_overview_exposes_research_ledgers_as_source_of_truth():
    artifact = _artifact()
    run = _run_view(artifact)
    snapshot = {
        "snapshot": "runs/live/latest.json",
        "events": [
            {
                "metadata": {
                    "source_timestamp": "2026-05-02T14:11:53.334284-05:00",
                    "provenance": {"source_ref": "Kraken public market data REST ticker"},
                },
                "payload": {"symbol": "BTC/USD"},
            }
        ],
    }
    readiness = _readiness_view()
    evidence_rigor = {
        "summary": asdict(
            summarize_evidence_rigor(artifact.manifest.columns, baseline_names=["buy-and-hold"])
        )
    }
    agentic_review = build_agentic_review(
        artifact.gate_results,
        artifact.next_tests,
        artifact.limitations,
    )
    control_plane = build_lab_control_plane(
        artifact,
        run=run,
        snapshot=snapshot,
        readiness=readiness,
        evidence_rigor=evidence_rigor,
        agentic_review=agentic_review,
        blockers=["Evidence run still has unresolved warnings."],
        ranked_attention_items=[],
        spread_bps=None,
        freshness={"label": "stale", "age_seconds": 1},
    )

    platform = build_platform_overview(
        artifact,
        run=run,
        snapshot=snapshot,
        readiness=readiness,
        evidence_rigor=evidence_rigor,
        agentic_review=agentic_review,
        control_plane=control_plane,
    )

    ledgers = platform["research_ledgers"]
    assert ledgers["baseline_pack_ledger"]["summary"]["missing_baselines"] == []
    assert ledgers["walk_forward_ledger"]["summary"]["status"] == "blocked_by_fold_fragility"
    assert ledgers["point_in_time_proof"]["source_timestamp"] == "2026-05-02T14:11:53.334284-05:00"
    assert ledgers["failure_gallery"]["cards"][0]["caught_by"] == "Baseline Challenger"
    assert ledgers["action_guidance"]["plain_next_action"]["label"].startswith("Retest")
    assert _has_no_trade_instruction(ledgers)


def _run_view(artifact) -> dict:
    gate_results = [
        {
            "name": gate.gate_name,
            "status": gate.status,
            "passed": gate.status == "pass",
            "detail": gate.remediation_hint,
            "severity": gate.severity,
            "threshold": gate.threshold,
            "evidence": gate.evidence,
        }
        for gate in artifact.gate_results
    ]
    return {
        "id": artifact.hypothesis.id,
        "thesis": artifact.hypothesis.thesis,
        "verdict": artifact.verdict,
        "disproof_score": artifact.disproof_score,
        "gate_counts": {
            "pass": sum(1 for gate in gate_results if gate["status"] == "pass"),
            "warn": sum(1 for gate in gate_results if gate["status"] == "warn"),
            "fail": sum(1 for gate in gate_results if gate["status"] == "fail"),
        },
        "gate_results": gate_results,
        "limitations": artifact.limitations,
        "next_tests": artifact.next_tests,
        "source": "runs/example-run.json",
    }


def _readiness_view() -> dict:
    return {
        "current_stage": {"id": "research_candidate", "label": "Research candidate"},
        "allowed_output": "Show source-labeled research evidence.",
        "completed_checks": [],
        "validation": {"promotion_ready": False, "missing_failed_checks": []},
        "readiness_artifacts": {},
        "missing_checks": [{"id": "baseline_beaten", "label": "Comparator beaten"}],
        "not_allowed": [],
    }


def _has_no_trade_instruction(payload: dict) -> bool:
    serialized = json.dumps(payload).lower()
    banned = ["buy now", "sell now", "follow this signal", "submit order", "broker api key"]
    return not any(term in serialized for term in banned)
