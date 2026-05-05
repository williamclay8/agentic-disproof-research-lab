from __future__ import annotations

import json

from trading_lab.intake import build_strategy_import_preview


def test_strategy_import_preview_turns_plain_language_into_quarantined_draft():
    preview = build_strategy_import_preview(
        source_type="plain_language_claim",
        raw_text=(
            "Thesis: BTC/USD daily moving-average crossover may beat buy-and-hold "
            "after costs. Null: no edge after costs. Universe: BTC/USD. "
            "Horizon: daily bars. Signal: close crosses above the 20 day average. "
            "Data: local OHLCV CSV. Baseline: buy-and-hold."
        ),
        source_ref="manual:intake:test",
    )

    claim = preview["candidate_claim"]

    assert preview["mode"] == "research_only"
    assert preview["source_type"] == "plain_language_claim"
    assert preview["status"] == "quarantine_until_evidence_exists"
    assert preview["promotion_allowed"] is False
    assert preview["draft_id"].startswith("intake:")
    assert claim["claim_id"].startswith("draft-btc-usd-daily-moving-average")
    assert claim["asset_universe"] == ["BTC/USD"]
    assert claim["time_horizon"] == "daily bars"
    assert "moving-average crossover" in claim["thesis"]
    assert claim["null_hypothesis"] == "no edge after costs"
    assert claim["signal_definition"] == "close crosses above the 20 day average"
    assert "baseline comparison" in claim["falsification_tests"]
    assert preview["missing_fields"] == []
    assert [task["pack_id"] for task in preview["first_falsification_tasks"][:3]] == [
        "point-in-time-pack",
        "baseline-pack",
        "walk-forward-pack",
    ]
    assert preview["source_refs"] == ["manual:intake:test"]
    assert _has_no_trade_instruction(preview)


def test_strategy_import_preview_blocks_execution_terms_but_keeps_disproof_plan():
    preview = build_strategy_import_preview(
        source_type="plain_language_claim",
        raw_text=(
            "Thesis: ETH breakout strategy may beat a naive momentum baseline. "
            "Universe: ETH/USD. Horizon: 4h bars. Signal: close above prior range. "
            "Use broker API key to submit order when condition appears."
        ),
        source_ref="manual:intake:unsafe",
    )

    assert preview["status"] == "blocked_by_execution_terms"
    assert preview["promotion_allowed"] is False
    assert {"broker", "api_key", "order"} <= set(preview["blocked_terms"])
    assert "null_hypothesis" in preview["missing_fields"]
    assert preview["first_falsification_tasks"][0]["pack_id"] == "boundary-scrub-pack"
    assert preview["first_falsification_tasks"][0]["owner"] == "Promotion Gatekeeper"
    assert preview["candidate_claim"]["claim_id"].startswith("draft-eth-breakout")
    assert _has_no_trade_instruction(preview)


def test_strategy_import_preview_rejects_unknown_source_type():
    preview = build_strategy_import_preview(
        source_type="broker_connector",
        raw_text="Thesis: test",
    )

    assert preview["status"] == "unsupported_source_type"
    assert preview["promotion_allowed"] is False
    assert preview["supported_sources"] == [
        "plain_language_claim",
        "csv_backtest",
        "pine_script",
        "lean_algorithm",
        "notebook_summary",
    ]


def _has_no_trade_instruction(payload: dict) -> bool:
    serialized = json.dumps(payload).lower()
    banned = ["buy now", "sell now", "follow this signal", "submit order"]
    return not any(term in serialized for term in banned)
