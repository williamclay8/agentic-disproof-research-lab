from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

from apps.api.server import (
    ALLOWED_WEB_ORIGINS,
    claim_payload,
    claims_payload,
    control_plane_payload,
    health_payload,
    latest_snapshot_payload,
    platform_payload,
    research_development_pass_payload,
    run_payload,
    strategy_import_preview_payload,
    terminal_payload,
)
from trading_lab.artifacts import read_run_artifact
from trading_lab.control_plane import build_active_mission


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_RULE_KEYS = {
    "current_research_state",
    "plain_english_meaning",
    "missing_proof",
    "next_safe_research_action",
}
CLAIM_JOURNEY_STEP_IDS = [
    "what_are_we_testing",
    "simple_baseline",
    "fooling_risks",
    "evidence_origin",
    "research_readiness",
    "next_research_test",
]
R_AND_D_STEP_IDS = [
    "action_native_first_move",
    "baseline_ledger",
    "walk_forward_ledger",
    "point_in_time_proof",
    "agent_reviewer_artifacts",
    "failure_gallery",
    "readiness_evidence",
    "hardened_response_schemas",
]
R_AND_D_STEP_REQUIRED_FIELDS = {
    "id",
    "title",
    "status",
    "owner",
    "current_research_state",
    "visible_api_fields",
    "source_refs",
    "missing_proof",
    "next_safe_research_action",
    "response_schema",
}


def assert_release_rule_answers(rule: dict) -> None:
    assert RELEASE_RULE_KEYS <= set(rule)
    for key in RELEASE_RULE_KEYS:
        assert isinstance(rule[key], str)
        assert rule[key].strip()
    serialized = json.dumps(rule).lower()
    assert "buy now" not in serialized
    assert "sell now" not in serialized
    assert "submit order" not in serialized
    assert "position size" not in serialized


def assert_claim_journey_steps(journey: dict) -> None:
    assert journey["mode"] == "research_only"
    assert [step["id"] for step in journey["steps"]] == CLAIM_JOURNEY_STEP_IDS
    for index, step in enumerate(journey["steps"], start=1):
        assert step["step_number"] == index
        assert step["title"].strip()
        assert step["question"].strip().endswith("?")
        assert step["current_research_state"].strip()
        assert step["plain_english_meaning"].strip()
        assert step["missing_proof"].strip()
        assert step["next_safe_research_action"].startswith("Research:")
        assert step["source_ref"].strip()
        serialized = json.dumps(step).lower()
        assert "buy now" not in serialized
        assert "sell now" not in serialized
        assert "submit order" not in serialized
        assert "broker api key" not in serialized


def assert_research_development_pass(pass_payload: dict) -> None:
    assert pass_payload["mode"] == "research_only"
    assert pass_payload["schema_version"] == "research_development_pass.v1"
    assert pass_payload["boundary"] == "offline R&D evidence only; not a trade instruction"
    assert [step["id"] for step in pass_payload["steps"]] == R_AND_D_STEP_IDS
    assert pass_payload["response_schema"]["required_fields"] == [
        "mode",
        "schema_version",
        "boundary",
        "steps",
        "forbidden_outputs",
    ]
    assert "ResearchDevelopmentPass" in pass_payload["response_schema"]["openapi_refs"]
    assert "ResearchDevelopmentStep" in pass_payload["response_schema"]["openapi_refs"]
    assert "personalized recommendation" in pass_payload["forbidden_outputs"]
    assert "broker/account/order route" in pass_payload["forbidden_outputs"]

    for index, step in enumerate(pass_payload["steps"], start=1):
        assert R_AND_D_STEP_REQUIRED_FIELDS <= set(step)
        assert step["step_number"] == index
        assert step["title"].strip()
        assert step["status"] in {"ready", "open", "blocked", "needs_review"}
        assert step["owner"].strip()
        assert step["current_research_state"].strip()
        assert isinstance(step["visible_api_fields"], list)
        assert step["visible_api_fields"]
        assert isinstance(step["source_refs"], list)
        assert step["source_refs"]
        assert step["missing_proof"].strip()
        assert step["next_safe_research_action"].startswith("Research:")
        assert step["response_schema"]["name"].strip()
        assert step["response_schema"]["required_fields"]
        assert "source_refs" in step["response_schema"]["required_fields"]
        assert step["response_schema"]["forbidden_outputs"] == pass_payload["forbidden_outputs"]

    by_id = {step["id"]: step for step in pass_payload["steps"]}
    assert by_id["action_native_first_move"]["native_action"]["route"] == "/strategy-import/preview"
    assert by_id["action_native_first_move"]["native_action"]["method"] == "POST"
    assert by_id["action_native_first_move"]["native_action"]["default_state"] == "quarantine_until_evidence_exists"
    assert "baseline_pack" in by_id["baseline_ledger"]["visible_api_fields"]
    assert "baseline comparison" in by_id["baseline_ledger"]["current_research_state"]
    assert "walk_forward_fold_ledger" in by_id["walk_forward_ledger"]["expected_artifacts"]
    assert by_id["point_in_time_proof"]["source_payload"] == "/point-in-time-contract/current"
    assert "point_in_time_contract.v1" in by_id["point_in_time_proof"]["contract_refs"]
    assert "open_finding_count" in by_id["agent_reviewer_artifacts"]["measurement_fields"]
    assert by_id["failure_gallery"]["source_payload"] == "/failure-gallery"
    assert by_id["readiness_evidence"]["source_payload"] == "/readiness/ledger"
    assert "append_only_entries" in by_id["readiness_evidence"]["visible_api_fields"]
    assert "ProductReleaseRule" in by_id["hardened_response_schemas"]["schema_refs"]
    assert "ClaimJourney" in by_id["hardened_response_schemas"]["schema_refs"]

    serialized = json.dumps(pass_payload).lower()
    assert "buy now" not in serialized
    assert "sell now" not in serialized
    assert "submit order" not in serialized
    assert "broker api key" not in serialized


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


def test_api_cors_allows_localhost_and_loopback_web_shells():
    assert "http://127.0.0.1:5199" in ALLOWED_WEB_ORIGINS
    assert "http://localhost:5199" in ALLOWED_WEB_ORIGINS


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
    assert_release_rule_answers(payload["product_release_rule"])
    assert_claim_journey_steps(payload["claim_journey"])
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


def test_platform_payload_exposes_same_product_release_rule():
    payload = platform_payload()

    assert_release_rule_answers(payload["product_release_rule"])
    assert_claim_journey_steps(payload["claim_journey"])
    assert payload["product_release_rule"]["current_research_state"]
    assert "research" in payload["product_release_rule"]["next_safe_research_action"].lower()
    json.dumps(payload)


def test_research_development_pass_exposes_eight_hardened_steps():
    payload = research_development_pass_payload()

    assert_research_development_pass(payload)
    json.dumps(payload)


def test_platform_payload_exposes_research_development_pass():
    payload = platform_payload()

    assert_research_development_pass(payload["research_development_pass"])
    assert payload["research_development_pass"]["steps"][0]["native_action"]["route"] == "/strategy-import/preview"
    json.dumps(payload)


def test_platform_payload_owns_agentic_claim_disproof_wedge():
    payload = platform_payload()

    assert payload["mode"] == "research_only"
    assert (
        payload["wedge_sentence"]
        == "The agentic trading lab that kills weak strategies faster than anyone else, and only lets surviving claims advance through auditable evidence gates."
    )
    assert payload["claim_registry"]["claims"][0]["claim_id"] == "toy-moving-average-crossover"
    assert payload["claim_registry"]["runs"][0]["source_ref"] == "runs/example-run.json"
    assert payload["evidence_graph"]["nodes"]
    assert payload["evidence_graph"]["edges"]
    assert "gate:baseline-comparison" in {
        node["id"] for node in payload["evidence_graph"]["nodes"]
    }
    assert payload["point_in_time_contract"]["status"] == "needs_review"
    assert payload["point_in_time_contract"]["as_of_policy"] == "known-at-time inputs only"
    assert "missing_baseline:random-control" in {
        gap["id"] for gap in payload["point_in_time_contract"]["gaps"]
    }
    assert payload["falsification_engine"]["packs"][0]["pack_id"] == "baseline-pack"
    assert payload["falsification_engine"]["packs"][0]["status"] == "open"
    assert payload["agent_contracts"][0]["agent"] == "Leak Auditor"
    assert payload["agent_contracts"][0]["output_schema"] == "agent_finding.v1"
    assert payload["readiness_ledger"]["promotion_ready"] is False
    assert payload["trust_packet"]["claim_id"] == "toy-moving-average-crossover"
    assert payload["trust_packet"]["verdict"] == "inconclusive"
    assert payload["trust_packet"]["export_status"] == "ready_for_research_review"
    assert payload["strategy_import"]["supported_sources"] == [
        "plain_language_claim",
        "csv_backtest",
        "pine_script",
        "lean_algorithm",
        "notebook_summary",
    ]
    assert payload["failure_gallery"]["failed_or_blocked_claims"]
    serialized = json.dumps(payload).lower()
    assert "buy now" not in serialized
    assert "sell now" not in serialized
    assert "submit order" not in serialized


def test_platform_payload_sections_are_source_referenced_and_research_only():
    payload = platform_payload()

    assert payload["mode"] == "research_only"
    assert payload["claim_registry"]["claims"][0]["source_ref"] == "runs/example-run.json"
    assert payload["evidence_graph"]["nodes"][0]["source_ref"]
    assert payload["evidence_graph"]["edges"][0]["source_ref"]
    assert payload["point_in_time_contract"]["source_refs"]["run"] == "runs/example-run.json"
    assert payload["falsification_engine"]["queue"]
    assert payload["agent_contracts"][0]["source_refs"] == ["runs/example-run.json"]
    assert payload["readiness_ledger"]["write_policy"] == "append_only"
    assert payload["readiness_ledger"]["append_only_entries"]
    assert payload["trust_packet"]["research_only"] is True
    assert payload["trust_packet"]["source_refs"]["run"] == "runs/example-run.json"
    assert payload["failure_gallery"]["failed_or_blocked_claims"][0]["source_ref"] == "runs/example-run.json"

    serialized = json.dumps(payload).lower()
    assert "autonomous execution actor" not in serialized
    assert "buy now" not in serialized
    assert "sell now" not in serialized
    assert "submit order" not in serialized


def test_platform_subpayload_helpers_project_current_claim():
    registry = claims_payload()
    claim = claim_payload("toy-moving-average-crossover")
    missing = claim_payload("missing-claim")

    assert registry["claims"][0]["claim_id"] == "toy-moving-average-crossover"
    assert claim["claim"]["claim_id"] == "toy-moving-average-crossover"
    assert claim["runs"][0]["source_ref"] == "runs/example-run.json"
    assert claim["trust_packet_ref"] == "/trust-packet/current"
    assert missing["error"] == "claim_not_found"


def test_evidence_graph_links_claim_run_dataset_gates_and_readiness():
    graph = platform_payload()["evidence_graph"]
    node_ids = {node["id"] for node in graph["nodes"]}
    edge_pairs = {(edge["from"], edge["to"], edge["relationship"]) for edge in graph["edges"]}

    assert "claim:toy-moving-average-crossover" in node_ids
    assert "run:toy-moving-average-crossover-52635e40" in node_ids
    assert any(node_id.startswith("dataset:") for node_id in node_ids)
    assert "gate:baseline-comparison" in node_ids
    assert "readiness:current" in node_ids
    assert (
        "claim:toy-moving-average-crossover",
        "run:toy-moving-average-crossover-52635e40",
        "tested_by",
    ) in edge_pairs
    assert any(edge["relationship"] == "uses_dataset" for edge in graph["edges"])
    assert any(edge["relationship"] == "blocks_promotion" for edge in graph["edges"])


def test_point_in_time_contract_and_import_contract_block_promotion_surfaces():
    payload = platform_payload()
    pit = payload["point_in_time_contract"]
    strategy_import = payload["strategy_import"]

    assert pit["status"] == "needs_review"
    assert pit["fields"]
    assert "random-control" in pit["missing_baselines"]
    assert "missing_baseline:random-control" in {gap["id"] for gap in pit["gaps"]}
    assert strategy_import["intake_contract"]["default_state"] == "quarantine_until_evidence_exists"
    assert "broker" in strategy_import["blocked_fields"]
    assert "order" in strategy_import["blocked_fields"]
    assert "live_signal" in strategy_import["blocked_fields"]


def test_strategy_import_preview_payload_keeps_new_ideas_in_quarantine():
    payload = strategy_import_preview_payload(
        {
            "source_type": "plain_language_claim",
            "raw_text": (
                "Thesis: BTC/USD daily momentum may beat buy-and-hold after costs. "
                "Null: no edge after costs. Universe: BTC/USD. Horizon: daily bars. "
                "Signal: close above 20 day high. Data: local OHLCV CSV."
            ),
        }
    )

    assert payload["mode"] == "research_only"
    assert payload["status"] == "quarantine_until_evidence_exists"
    assert payload["promotion_allowed"] is False
    assert payload["candidate_claim"]["claim_id"].startswith("draft-btc-usd-daily-momentum")
    assert payload["first_falsification_tasks"][0]["pack_id"] == "point-in-time-pack"
    assert payload["next_action"]["label"] == "Create offline evidence packet"


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
    assert "Product Release Rule" in html
    assert 'id="product-release-rule-grid"' in html
    assert "renderProductReleaseRule" in html
    assert "current_research_state" in html
    assert "Claim Journey" in html
    assert 'id="claim-journey-steps"' in html
    assert "renderClaimJourney" in html
    assert "What are we testing?" in html
    assert "Can it beat a simple baseline?" in html
    assert "What could be fooling us?" in html
    assert "Where did this evidence come from?" in html
    assert "Is this ready for more research?" in html
    assert "What should we test next?" in html
    assert "Guided Lab" in html
    assert "Claim Card" in html
    assert "Plain-English controls" in html
    assert "Research Desk" in html
    assert "Professional audit map" in html
    assert "Agentic trading without the money-machine myth" in html
    assert "R&D Pass" in html
    assert 'id="research-development-pass"' in html
    assert "renderResearchDevelopmentPass" in html
    assert "Action-native first move" in html
    assert "Baseline ledger" in html
    assert "Walk-forward ledger" in html
    assert "Point-in-time proof" in html
    assert "Measurable agent reviewer artifacts" in html
    assert "Readiness evidence" in html
    assert "Hardened response schemas" in html
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
    assert "Claim Registry" in html
    assert "Evidence Graph" in html
    assert "Point-in-Time Contract" in html
    assert 'id="claim-registry"' in html
    assert 'id="evidence-graph"' in html
    assert 'id="point-in-time-contract"' in html
    assert 'id="falsification-engine"' in html
    assert 'id="agent-contracts"' in html
    assert 'id="readiness-ledger"' in html
    assert 'id="trust-packet"' in html
    assert 'id="strategy-import"' in html
    assert 'id="strategy-import-preview"' in html
    assert 'id="strategy-import-text"' in html
    assert 'id="strategy-import-run"' in html
    assert 'id="failure-gallery"' in html
    assert "loadPlatform" in html
    assert "renderPlatform" in html
    assert "runStrategyImportPreview" in html
    assert "/platform/overview" in html
    assert "/strategy-import/preview" in html
    assert "Agent Contracts" in html
    assert "Readiness Ledger" in html
    assert "Trust Packet" in html
    assert "Strategy Import" in html
    assert "Failure Gallery" in html
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
    assert "/platform/overview" in contract
    assert "/claims" in contract
    assert "/claims/{claim_id}" in contract
    assert "/evidence-graph/current" in contract
    assert "/point-in-time-contract/current" in contract
    assert "/falsification-engine/current" in contract
    assert "/agent-contracts" in contract
    assert "/readiness/ledger" in contract
    assert "/trust-packet/current" in contract
    assert "/strategy-import/contract" in contract
    assert "/strategy-import/preview" in contract
    assert "/failure-gallery" in contract
    assert "/research-development/pass" in contract
    assert "product_release_rule" in contract
    assert "claim_journey" in contract
    assert "research_development_pass" in contract
    assert "ResearchDevelopmentPass" in contract
    assert "ResearchDevelopmentStep" in contract
    assert "action_native_first_move" in contract
    assert "baseline_ledger" in contract
    assert "walk_forward_ledger" in contract
    assert "point_in_time_proof" in contract
    assert "agent_reviewer_artifacts" in contract
    assert "hardened_response_schemas" in contract
    assert "what_are_we_testing" in contract
    assert "current_research_state" in contract
    assert "next_safe_research_action" in contract
    assert "/orders" not in contract
    assert "/accounts" not in contract
    assert "execution routes" in contract


def test_product_environment_documents_release_rule_gate():
    doc = (PROJECT_ROOT / "docs/architecture/product-environment.md").read_text(
        encoding="utf-8"
    )

    assert "Product Release Rule" in doc
    assert "current research state" in doc
    assert "plain English" in doc
    assert "missing proof" in doc
    assert "next safe research action" in doc
    assert "Claim Journey" in doc
    assert "What are we testing?" in doc
    assert "What should we test next?" in doc


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
