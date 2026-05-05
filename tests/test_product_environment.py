from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

from apps.api.server import (
    control_plane_payload,
    health_payload,
    latest_snapshot_payload,
    run_payload,
    terminal_payload,
)
from trading_lab.artifacts import read_run_artifact
from trading_lab.control_plane import build_active_mission


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_product_lane_files_exist_and_keep_trading_lab_standalone():
    expected = [
        ".env.example",
        "Makefile",
        "apps/api/server.py",
        "apps/web/index.html",
        "apps/web/server.py",
        "apps/worker/worker.py",
        "packages/trading_kernel/README.md",
        "packages/contracts/openapi/trading-lab.v0.yaml",
        "infra/docker-compose.yml",
        "docs/architecture/product-environment.md",
    ]

    missing = [path for path in expected if not (PROJECT_ROOT / path).exists()]
    assert missing == []

    boundary = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "standalone Agentic Trading Agent / Trading Lab project" in boundary
    assert "separate from Vanta" in boundary


def test_api_health_payload_has_no_execution_or_advice_surface():
    payload = health_payload()

    assert payload["status"] == "ok"
    assert payload["boundary"] == "standalone research lab"
    assert payload["execution"] == "disabled"
    assert payload["advice"] == "disabled"


def test_api_payloads_read_existing_evidence_artifacts():
    run = run_payload()
    snapshot = latest_snapshot_payload()

    assert run["id"] == "toy-moving-average-crossover"
    assert run["source"] == "runs/example-run.json"
    assert "gate_counts" in run
    assert run["gate_counts"]["warn"] >= 1
    assert any(gate["status"] == "warn" for gate in run["blocking_gates"])
    assert {"threshold", "evidence"} <= set(run["gate_results"][0])
    assert isinstance(run["gate_results"], list)
    assert snapshot["snapshot"] == "runs/live/latest.json"
    assert snapshot["boundary"] == "research observations only"
    assert snapshot["count"] >= 1
    event = snapshot["events"][0]
    assert event["payload"]["symbol"]
    assert event["metadata"]["license_note"] == "research data only"
    assert event["metadata"]["provenance"]["source_ref"]
    assert event["metadata"]["provenance"]["provider"]["name"]
    assert event["observed_at"]
    assert event["source_timestamp"]
    assert event["record_hash"]


def test_terminal_payload_ranks_attention_without_advice_or_execution():
    payload = terminal_payload()

    assert payload["mode"] == "research_only"
    assert payload["readiness_verdict"]["label"] == "Not live-signal ready"
    assert payload["readiness_verdict"]["action_ready"] is False
    assert payload["setup_visibility"]["visibility_stage"] in {
        "hidden",
        "observation_only",
        "research_candidate",
        "preliminary_survivor",
    }
    assert (
        payload["evidence_passport"]["registered_hypothesis_id"]
        == payload["evidence"]["run_id"]
    )
    assert "baseline comparison" in payload["evidence_passport"]["open_warning_gates"]
    assert payload["market"]["spread_abs"] is not None
    assert payload["market"]["spread_bps"] is not None
    assert payload["market"]["last_location"] in {
        "below_bid",
        "at_bid",
        "inside_spread",
        "at_ask",
        "above_ask",
        "unknown",
    }
    assert payload["ranked_attention_items"]
    labels = [item["label"] for item in payload["ranked_attention_items"]]
    assert "Review market-friction context" in labels
    assert "Check execution reality" not in labels
    assert payload["blockers"]
    assert [role["name"] for role in payload["agentic_review"]["roles"]] == [
        "Leak Auditor",
        "Baseline Challenger",
        "Cost Stress Critic",
        "Reproducibility Clerk",
        "Promotion Gatekeeper",
        "Regime Skeptic",
    ]
    assert payload["agentic_review"]["promotion_decision"]["decision"] == "research-only hold"
    assert payload["evidence_rigor"]["summary"]["status"] == "needs_evidence"
    assert "missing_baseline:random-control" in payload["evidence_rigor"]["summary"]["evidence_gaps"]
    assert "paper_ledger_artifact_present" in payload["confidence_readiness"]["completed_checks"]
    assert "live_shadow_drift_artifact_present" in payload["confidence_readiness"]["completed_checks"]
    assert "calibration_history_artifact_present" in payload["confidence_readiness"]["completed_checks"]
    assert "risk_packet_artifact_present" in payload["confidence_readiness"]["completed_checks"]
    assert "paper_ledger_promotion_ready" not in payload["confidence_readiness"]["completed_checks"]
    assert payload["confidence_readiness"]["validation"]["promotion_ready"] is False
    assert payload["confidence_readiness"]["readiness_artifacts"]["paper_ledger"]["status"] == "pass"
    assert payload["human_brief"]["what_matters_now"]
    assert payload["human_brief"]["would_change_our_mind"]
    assert payload["agent_mission_board"]
    assert payload["evidence_gaps"]
    assert payload["next_falsification_tasks"]
    assert payload["claim_lifecycle"]["stage"] == "research_only_hold"
    assert payload["gate_summaries"]["weakest"][0]["name"] == "baseline comparison"
    assert payload["lab_scorecard"]["promotion_ready"] is False
    assert payload["learning_loop"]["current_lesson"] == "Comparator Discipline"
    serialized = json.dumps(payload).lower()
    assert "buy now" not in serialized
    assert "sell now" not in serialized
    assert "submit order" not in serialized


def test_control_plane_payload_turns_evidence_into_lab_workflows():
    payload = control_plane_payload()

    assert payload["mode"] == "research_only"
    assert payload["boundary"]["execution"] == "disabled"
    assert payload["boundary"]["advice"] == "disabled"
    assert payload["active_mission"]["state"] == "warning_hold"
    assert payload["claim_lifecycle"]["claim_id"] == "toy-moving-average-crossover"
    assert payload["claim_lifecycle"]["stage"] == "research_only_hold"
    assert "baseline comparison" in payload["claim_lifecycle"]["blocking_gate_names"]
    assert "walk-forward robustness" in payload["claim_lifecycle"]["blocking_gate_names"]
    assert [role["name"] for role in payload["agent_mission_board"]] == [
        "Leak Auditor",
        "Baseline Challenger",
        "Cost Stress Critic",
        "Reproducibility Clerk",
        "Promotion Gatekeeper",
        "Regime Skeptic",
    ]
    baseline_mission = next(
        role for role in payload["agent_mission_board"] if role["name"] == "Baseline Challenger"
    )
    assert baseline_mission["status"] == "active"
    assert baseline_mission["top_finding"]["gate_name"] == "baseline comparison"
    assert baseline_mission["source_refs"] == ["runs/example-run.json"]
    assert payload["gate_summaries"]["counts"]["warn"] == 2
    assert [gate["name"] for gate in payload["gate_summaries"]["weakest"][:2]] == [
        "baseline comparison",
        "walk-forward robustness",
    ]
    gap_ids = {gap["id"] for gap in payload["evidence_gaps"]}
    assert "gate:baseline-comparison" in gap_ids
    assert "rigor:missing_baseline:random-control" in gap_ids
    assert "readiness:paper_ledger_sample_count" in gap_ids
    first_task = payload["next_falsification_tasks"][0]
    assert first_task["owner"] == "Baseline Challenger"
    assert first_task["research_only"] is True
    assert "baseline comparison" in first_task["label"]
    assert payload["lab_scorecard"]["research_maturity"]["score"] == 100
    assert payload["lab_scorecard"]["evidence_rigor"]["score"] == 60
    assert payload["learning_loop"]["recurring_mistakes"] == [
        "Comparator weakness",
        "Fold fragility",
    ]
    json.dumps(payload)


def test_active_mission_holds_when_readiness_gaps_remain_after_gate_passes():
    artifact = read_run_artifact(PROJECT_ROOT / "runs" / "example-run.json")
    all_pass_artifact = replace(
        artifact,
        gate_results=[replace(gate, status="pass") for gate in artifact.gate_results],
    )

    mission = build_active_mission(
        all_pass_artifact,
        [{"id": "readiness:paper_ledger_sample_count"}],
        "runs/example-run.json",
    )

    assert mission["state"] == "readiness_hold"


def test_web_copy_blocks_recommendation_and_execution_language():
    html = (PROJECT_ROOT / "apps/web/index.html").read_text(encoding="utf-8")
    banned_phrases = [
        "buy now",
        "sell now",
        "guaranteed",
        "follow this signal",
        "submit order",
        "broker api key",
    ]

    assert "Decision Cockpit" in html
    assert "What matters now" in html
    assert "What this means" in html
    assert "Inspect next" in html
    assert "Why this is still research-only" in html
    assert "Would change our mind" in html
    assert "Static file preview" in html
    assert "Live local view" in html
    assert "Agent council" in html
    assert "Evidence spine" in html
    assert "Claim packet" in html
    assert "Basis panel" in html
    assert "Missing proof" in html
    assert "Mission Control" in html
    assert "Agent mission board" in html
    assert "Evidence Gap Register" in html
    assert "Falsification Task Board" in html
    assert "Claim Lifecycle" in html
    assert "Gate x-ray" in html
    assert "Lab scorecard" in html
    assert "Learning Loop" in html
    assert "Observation tape" in html
    assert "Provenance ledger" in html
    assert "Raw evidence drawer" in html
    assert "Source ref" in html
    assert "How To Use This" not in html
    assert "Promotion Blockers" not in html
    for phrase in banned_phrases:
        assert phrase not in html.lower()


def test_openapi_contract_excludes_order_and_account_routes():
    contract = (PROJECT_ROOT / "packages/contracts/openapi/trading-lab.v0.yaml").read_text(
        encoding="utf-8"
    )

    assert "/health" in contract
    assert "/runs/example" in contract
    assert "/snapshots/latest" in contract
    assert "/terminal/overview" in contract
    assert "/confidence/readiness" in contract
    assert "/readiness/artifacts" in contract
    assert "/agentic/review" in contract
    assert "/evidence/rigor" in contract
    assert "/control-plane/lab" in contract
    assert "/orders" not in contract
    assert "/accounts" not in contract
    assert "execution routes" in contract


def test_compose_has_local_parity_services_without_secrets():
    compose = (PROJECT_ROOT / "infra/docker-compose.yml").read_text(encoding="utf-8")

    assert "postgres:" in compose
    assert "redis:" in compose
    assert "api:" in compose
    assert "web:" in compose
    assert "worker:" in compose
    assert "TRADING_LAB_DISABLE_NETWORK" in compose
    assert "api_key" not in compose.lower()
    assert "secret" not in compose.lower()


def test_ci_workflow_runs_tests_without_deployment_claims():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "python3 -m pytest -q" in workflow
    assert "TRADING_LAB_DISABLE_NETWORK" in workflow
    assert "deploy" not in workflow.lower()


def test_health_payload_remains_json_serializable():
    json.dumps(health_payload())
