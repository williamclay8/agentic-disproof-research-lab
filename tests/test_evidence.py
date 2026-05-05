from trading_lab.evidence import (
    baseline_pack,
    classify_point_in_time_fields,
    summarize_evidence_rigor,
)


def test_point_in_time_contract_flags_future_target_and_forward_leakage():
    contract = classify_point_in_time_fields(
        [
            "date",
            "symbol",
            "open",
            "future_return_5d",
            "target",
            "forward_close",
        ]
    )

    assert contract.allowed == ["date", "open", "symbol"]
    assert contract.leakage_suspect == ["forward_close", "future_return_5d", "target"]
    assert contract.unknown_lineage == []
    assert contract.evidence_gaps == []


def test_point_in_time_contract_treats_unknown_non_ohlcv_columns_as_evidence_gaps():
    contract = classify_point_in_time_fields(
        ["date", "symbol", "open", "close", "sentiment_score", "vendor_factor"],
        known_point_in_time_fields=["sentiment_score"],
    )

    assert contract.allowed == ["close", "date", "open", "sentiment_score", "symbol"]
    assert contract.leakage_suspect == []
    assert contract.unknown_lineage == ["vendor_factor"]
    assert contract.evidence_gaps == ["unknown_lineage:vendor_factor"]


def test_baseline_pack_contains_required_research_only_descriptors():
    pack = baseline_pack()

    assert list(pack) == [
        "buy-and-hold",
        "equal-weight",
        "naive-momentum",
        "naive-mean-reversion",
        "random-control",
    ]
    for descriptor in pack.values():
        text = " ".join(
            [
                descriptor.name,
                descriptor.description,
                descriptor.contract,
                descriptor.research_only_wording,
            ]
        ).lower()
        assert "research-only" in text
        assert "offline" in text
        assert "not investment advice" in text
        assert "broker" not in text
        assert "order" not in text
        assert "execute" not in text


def test_evidence_rigor_summary_is_deterministic_and_counts_gaps():
    first = summarize_evidence_rigor(
        ["mystery_factor", "close", "target_return", "date", "symbol", "future_label"],
        baseline_names=["random-control", "buy-and-hold"],
    )
    second = summarize_evidence_rigor(
        ["future_label", "symbol", "date", "target_return", "close", "mystery_factor"],
        baseline_names=["buy-and-hold", "random-control"],
    )

    assert first == second
    assert first.allowed_fields == ["close", "date", "symbol"]
    assert first.leakage_suspect_fields == ["future_label", "target_return"]
    assert first.unknown_lineage_fields == ["mystery_factor"]
    assert first.evidence_gaps == [
        "leakage_suspect:future_label",
        "leakage_suspect:target_return",
        "unknown_lineage:mystery_factor",
        "missing_baseline:equal-weight",
        "missing_baseline:naive-mean-reversion",
        "missing_baseline:naive-momentum",
    ]
    assert first.score == 40
    assert first.status == "needs_evidence"
    assert "research-only" in first.wording
    assert "not investment advice" in first.wording
