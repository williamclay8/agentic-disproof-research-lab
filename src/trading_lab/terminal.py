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
    """Return the built-in catalog for local-only research terminal actions."""
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
            safety="offline research focus only",
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
    }


def power_guidance() -> tuple[str, ...]:
    return (
        "This offline research lab helps focus symbols, register hypotheses, run local falsification, and review evidence.",
        "No live market data is requested or implied; use local CSVs and generated artifacts only.",
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
