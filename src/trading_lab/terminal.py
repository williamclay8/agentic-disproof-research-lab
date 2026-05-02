"""Offline terminal command catalog for research workflows."""

from __future__ import annotations

from dataclasses import dataclass
import re
import shlex
from typing import Mapping


_SYMBOL_RE = re.compile(r"^(?=.*[A-Z])[A-Z0-9][A-Z0-9.-]{0,15}$")


@dataclass(frozen=True)
class Component:
    id: str
    title: str
    intent: str
    summary: str
    aliases: tuple[str, ...]
    safety: str


@dataclass(frozen=True)
class TerminalCommand:
    id: str
    aliases: tuple[str, ...]
    component_id: str | None
    guidance: str


@dataclass(frozen=True)
class ParsedInput:
    kind: str
    command_id: str | None
    alias: str | None
    args: tuple[str, ...]
    symbol: str | None
    message: str


def component_catalog() -> tuple[Component, ...]:
    """Return the built-in catalog for research terminal actions."""
    return (
        Component(
            id="symbol-focus",
            title="Symbol focus",
            intent="Research",
            summary=(
                "Treat an uppercase ticker-like token as the current research symbol "
                "for notes, local artifacts, and hypothesis framing."
            ),
            aliases=("SYMBOL",),
            safety="research focus only; no market data is fetched",
        ),
        Component(
            id="hypothesis-register",
            title="Register hypothesis",
            intent="Research",
            summary=(
                "Draft or select a pre-registered hypothesis for local falsification "
                "against explicit fixture data."
            ),
            aliases=("hyp", "hypothesis", "register"),
            safety="requires local datasets; no market-data lookup",
        ),
        Component(
            id="run-local-disproof",
            title="Run local disproof",
            intent="Falsification",
            summary=(
                "Run an offline falsification pass using bundled or user-provided "
                "CSV artifacts and write evidence outputs."
            ),
            aliases=("run", "disprove", "backtest"),
            safety="simulation only; no orders or execution",
        ),
        Component(
            id="dashboard-review",
            title="Review evidence dashboard",
            intent="Review",
            summary=(
                "Open or create a static evidence dashboard for comparing local "
                "research artifacts and limitations."
            ),
            aliases=("dash", "dashboard", "review"),
            safety="static local report; not investment advice",
        ),
        Component(
            id="market-snapshot",
            title="Collect market snapshot",
            intent="Observation",
            summary=(
                "Collect explicit research-only market observations from a fixture "
                "or approved provider into auditable local snapshots."
            ),
            aliases=("market-snapshot", "snapshot", "watch"),
            safety="research data only; no broker or execution actions",
        ),
        Component(
            id="data-source-inspect",
            title="Inspect data sources",
            intent="Observation",
            summary=(
                "List or inspect available market-data sources, freshness labels, "
                "and provenance boundaries."
            ),
            aliases=("data-source", "providers", "provenance"),
            safety="metadata only; credentials are never collected",
        ),
        Component(
            id="safety-status",
            title="Safety status",
            intent="Safety",
            summary=(
                "Show research-mode boundaries, blocked command families, and "
                "network/realtime kill-switch status."
            ),
            aliases=("safety-status", "safety-off"),
            safety="fails closed for advice, broker, and order commands",
        ),
    )


def catalog_by_intent() -> dict[str, list[Component]]:
    grouped: dict[str, list[Component]] = {}
    for component in component_catalog():
        grouped.setdefault(component.intent, []).append(component)
    return grouped


def registered_commands() -> dict[str, TerminalCommand]:
    return {
        "help": TerminalCommand(
            id="help",
            aliases=("?", "help", "catalog"),
            component_id=None,
            guidance="Show the offline component catalog and safety boundaries.",
        ),
        "hypothesis-register": TerminalCommand(
            id="hypothesis-register",
            aliases=("hyp", "hypothesis", "register"),
            component_id="hypothesis-register",
            guidance=(
                "Prepare a local research hypothesis. Args are labels, dataset paths, "
                "or notes; quoted phrases stay together."
            ),
        ),
        "run-local-disproof": TerminalCommand(
            id="run-local-disproof",
            aliases=("run", "disprove", "backtest"),
            component_id="run-local-disproof",
            guidance=(
                "Run offline falsification against local artifacts only. This never "
                "fetches live quotes and never submits broker actions."
            ),
        ),
        "dashboard-review": TerminalCommand(
            id="dashboard-review",
            aliases=("dash", "dashboard", "review"),
            component_id="dashboard-review",
            guidance=(
                "Review static local evidence, caveats, and next tests. Outputs are "
                "research reports, not trading recommendations."
            ),
        ),
        "market-snapshot": TerminalCommand(
            id="market-snapshot",
            aliases=("market-snapshot", "snapshot", "watch"),
            component_id="market-snapshot",
            guidance=(
                "Collect a research-only market observation snapshot with provenance "
                "and freshness labels. No broker or execution actions are available."
            ),
        ),
        "data-source-inspect": TerminalCommand(
            id="data-source-inspect",
            aliases=("data-source", "providers", "provenance", "data-freshness"),
            component_id="data-source-inspect",
            guidance=(
                "Inspect source metadata, freshness, and delay labels. Credentials, "
                "accounts, and broker connections are outside this terminal."
            ),
        ),
        "safety-status": TerminalCommand(
            id="safety-status",
            aliases=("safety-status", "safety-off"),
            component_id="safety-status",
            guidance=(
                "Show or activate research-mode safety boundaries. This disables "
                "observation collection for the current session when requested."
            ),
        ),
    }


def power_guidance() -> tuple[str, ...]:
    return (
        "This research lab helps focus symbols, register hypotheses, collect explicit observations, run local falsification, and review evidence.",
        "Market observations must be explicitly collected and labeled with source, freshness, and provenance.",
        "No broker or execution actions are available from this terminal layer.",
        "Type '?' for catalog help, use command aliases, or enter an uppercase ticker-like token such as MSFT.",
    )


def parse_terminal_input(raw_input: str) -> ParsedInput:
    text = raw_input.strip()
    if not text:
        return ParsedInput(
            kind="empty",
            command_id=None,
            alias=None,
            args=(),
            symbol=None,
            message="Enter '?' for the offline research catalog.",
        )

    try:
        tokens = tuple(shlex.split(text))
    except ValueError as error:
        return _unknown(f"Could not parse input: {error}.")

    if not tokens:
        return _unknown("Unknown command.")

    commands = registered_commands()
    aliases = _alias_index(commands)
    first = tokens[0]
    command_id = aliases.get(first) or aliases.get(first.lower())

    if command_id == "help":
        return ParsedInput(
            kind="help",
            command_id="help",
            alias=first,
            args=tokens[1:],
            symbol=None,
            message=_help_message(),
        )

    if command_id is not None:
        command = commands[command_id]
        return ParsedInput(
            kind="command",
            command_id=command.id,
            alias=first,
            args=tokens[1:],
            symbol=None,
            message=f"{command.id}: {command.guidance}",
        )

    if _is_forbidden_command(tokens):
        return ParsedInput(
            kind="blocked",
            command_id=None,
            alias=first,
            args=tokens[1:],
            symbol=None,
            message=(
                "Blocked or unknown command. Trading Lab does not support advice, "
                "broker access, order routing, account actions, or execution. Try '?' "
                "for research-only commands."
            ),
        )

    if len(tokens) == 1 and _SYMBOL_RE.match(first):
        return ParsedInput(
            kind="symbol",
            command_id="symbol-focus",
            alias=None,
            args=(first,),
            symbol=first,
            message=(
                f"{first} is now the offline research focus. "
                "No live market data, recommendations, or broker actions are triggered."
            ),
        )

    return _unknown(f"Unknown command: {first}.")


def _alias_index(commands: Mapping[str, TerminalCommand]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for command in commands.values():
        aliases[command.id] = command.id
        for alias in command.aliases:
            aliases[alias] = command.id
    return aliases


def _help_message() -> str:
    lines = list(power_guidance())
    lines.append("")
    for intent, components in catalog_by_intent().items():
        lines.append(f"{intent}:")
        for component in components:
            alias_list = ", ".join(component.aliases)
            lines.append(
                f"- {component.id} ({alias_list}): {component.summary} Safety: {component.safety}."
            )
    return "\n".join(lines)


def _unknown(prefix: str) -> ParsedInput:
    return ParsedInput(
        kind="unknown",
        command_id=None,
        alias=None,
        args=(),
        symbol=None,
        message=f"{prefix} Type '?' for help. No broker or execution actions are available.",
    )


def _is_forbidden_command(tokens: tuple[str, ...]) -> bool:
    lowered = " ".join(tokens).lower().replace("_", "-")
    forbidden_terms = (
        "buy",
        "sell",
        "hold",
        "short",
        "cover",
        "order",
        "submit-order",
        "cancel-order",
        "replace-order",
        "broker",
        "broker-login",
        "account",
        "portfolio-sync",
        "paper-trade",
        "simulate-fill",
        "position-size",
        "allocation",
        "rebalance",
        "entry",
        "exit",
        "stop-loss",
        "take-profit",
        "execute",
        "copy trade",
        "api-key",
        "credentials",
    )
    return any(term in lowered for term in forbidden_terms)
