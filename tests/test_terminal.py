from __future__ import annotations

import pytest

from trading_lab.terminal import (
    catalog_by_intent,
    parse_terminal_input,
    power_guidance,
    registered_commands,
)


def test_catalog_groups_offline_research_components_by_intent():
    catalog = catalog_by_intent()

    assert set(catalog) >= {"Research", "Falsification", "Review"}
    assert [component.id for component in catalog["Research"]] == [
        "symbol-focus",
        "hypothesis-register",
    ]
    assert catalog["Research"][0].safety == "research focus only; no market data is fetched"
    assert catalog["Falsification"][0].id == "run-local-disproof"


def test_power_guidance_explains_capabilities_and_safety_boundaries():
    guidance = power_guidance()

    assert any("research lab" in line for line in guidance)
    assert any("explicitly collected" in line for line in guidance)
    assert any("No broker" in line for line in guidance)
    assert any("'?'" in line for line in guidance)


def test_help_parser_returns_catalog_summary_for_question_mark():
    parsed = parse_terminal_input("?")

    assert parsed.kind == "help"
    assert parsed.command_id == "help"
    assert parsed.args == ()
    assert "symbol-focus" in parsed.message
    assert "Market observations must be explicitly collected" in parsed.message


def test_registered_command_alias_with_quoted_args_is_parsed():
    parsed = parse_terminal_input('hyp "mean reversion" --dataset "toy prices.csv"')

    assert parsed.kind == "command"
    assert parsed.command_id == "hypothesis-register"
    assert parsed.alias == "hyp"
    assert parsed.args == ("mean reversion", "--dataset", "toy prices.csv")
    assert "hypothesis-register" in parsed.message


def test_uppercase_ticker_like_token_becomes_research_symbol_focus():
    parsed = parse_terminal_input("MSFT")

    assert parsed.kind == "symbol"
    assert parsed.command_id == "symbol-focus"
    assert parsed.symbol == "MSFT"
    assert parsed.args == ("MSFT",)
    assert "offline research focus" in parsed.message


@pytest.mark.parametrize("token", ["BRK.B", "BTC-USD", "SPY"])
def test_symbol_focus_accepts_common_uppercase_research_tokens(token):
    parsed = parse_terminal_input(token)

    assert parsed.kind == "symbol"
    assert parsed.symbol == token


def test_lowercase_unknown_input_is_not_treated_as_symbol_or_execution():
    parsed = parse_terminal_input("buy msft")

    assert parsed.kind == "blocked"
    assert parsed.command_id is None
    assert "does not support advice" in parsed.message
    assert "order routing" in parsed.message


def test_registered_commands_expose_ids_and_aliases():
    commands = registered_commands()

    assert commands["help"].aliases == ("?", "help", "catalog")
    assert "run" in commands["run-local-disproof"].aliases
    assert "dash" in commands["dashboard-review"].aliases


def test_live_research_commands_are_allowed_without_execution_surface():
    parsed = parse_terminal_input("market-snapshot MSFT --mode simulated")

    assert parsed.kind == "command"
    assert parsed.command_id == "market-snapshot"
    assert "research-only market observation" in parsed.message
    assert "No broker" in parsed.message


@pytest.mark.parametrize(
    "raw_input",
    [
        "sell MSFT",
        "submit-order MSFT",
        "broker-login",
        "position-size MSFT",
        "take-profit MSFT",
        "rebalance portfolio",
    ],
)
def test_forbidden_live_trading_commands_fail_closed(raw_input):
    parsed = parse_terminal_input(raw_input)

    assert parsed.kind == "blocked"
    assert parsed.command_id is None
    assert "does not support advice" in parsed.message
    assert "order routing" in parsed.message
