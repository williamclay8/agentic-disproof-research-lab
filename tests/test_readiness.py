from trading_lab.readiness import validate_readiness


def test_placeholder_artifacts_are_present_but_not_promotion_ready():
    result = validate_readiness(
        paper_ledger={
            "status": "pass",
            "sample_count": 6,
            "limits": ["sample-limited research artifact"],
        },
        live_shadow_drift={
            "status": "pass",
            "drift": {"expected_vs_observed_return_delta": 0.0042},
        },
        calibration_history={
            "status": "pass",
            "brier_score": 0.246,
            "buckets": [{"sample_count": 3}, {"sample_count": 2}],
        },
        risk_packet={
            "status": "pass",
            "invalidation_evidence": ["baseline remains unresolved"],
            "friction_context": {"requires_spread_bps": True},
        },
    )

    assert result["artifact_present"] == {
        "paper_ledger": True,
        "live_shadow_drift": True,
        "calibration_history": True,
        "risk_packet": True,
    }
    assert result["promotion_ready"] is False
    assert "paper_ledger_artifact_present" in result["completed_checks"]
    assert "paper_ledger_promotion_ready" not in result["completed_checks"]
    assert "risk_packet_human_review" in {
        check["id"] for check in result["missing_failed_checks"]
    }
    assert result["promotion_verdict"]["level"] == "research_candidate"
    verdict_text = " ".join(str(value) for value in result["promotion_verdict"].values()).lower()
    assert "research" in verdict_text
    assert "buy" not in verdict_text
    assert "sell" not in verdict_text
    assert "order" not in verdict_text
    assert "position" not in verdict_text


def test_all_thresholds_and_human_review_allow_review_packet_verdict():
    result = validate_readiness(
        paper_ledger={
            "status": "pass",
            "sample_count": 30,
            "limits": ["research-only observation ledger"],
        },
        live_shadow_drift={
            "status": "pass",
            "sample_count": 42,
            "drift": {
                "expected_vs_observed_return_delta": 0.001,
                "max_allowed_delta": 0.01,
            },
        },
        calibration_history={
            "status": "pass",
            "brier_score": 0.19,
            "sample_count": 35,
        },
        risk_packet={
            "status": "pass",
            "invalidation_evidence": ["comparator failure invalidates display"],
            "risk_controls": ["freshness expiry", "drift review"],
            "human_review": True,
        },
    )

    assert result["promotion_ready"] is True
    assert {
        "paper_ledger_promotion_ready",
        "live_shadow_drift_promotion_ready",
        "calibration_history_promotion_ready",
        "risk_packet_promotion_ready",
        "risk_packet_human_review",
    }.issubset(result["completed_checks"])
    assert result["missing_failed_checks"] == []
    assert result["promotion_verdict"] == {
        "level": "human_reviewed_research_packet",
        "summary": "Promotion checks passed for a human-reviewed research packet; execution remains disabled.",
    }


def test_missing_payloads_are_reported_without_counting_artifacts_present():
    result = validate_readiness(
        paper_ledger={},
        live_shadow_drift={},
        calibration_history={},
        risk_packet={},
    )

    assert result["artifact_present"] == {
        "paper_ledger": False,
        "live_shadow_drift": False,
        "calibration_history": False,
        "risk_packet": False,
    }
    assert result["completed_checks"] == []
    assert result["promotion_ready"] is False
    assert {check["id"] for check in result["missing_failed_checks"]} >= {
        "paper_ledger_artifact_present",
        "live_shadow_drift_artifact_present",
        "calibration_history_artifact_present",
        "risk_packet_artifact_present",
    }
