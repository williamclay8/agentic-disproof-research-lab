"""Markdown reporting for local-only research falsification runs."""

from __future__ import annotations

from trading_lab.gates import choose_verdict
from trading_lab.models import (
    BacktestResult,
    BacktestSpec,
    DatasetManifest,
    GateResult,
    Hypothesis,
)


def render_markdown_report(
    hypothesis: Hypothesis,
    manifest: DatasetManifest,
    spec: BacktestSpec,
    result: BacktestResult,
    gate_results: list[GateResult],
    limitations: list[str],
    next_tests: list[str],
) -> str:
    verdict = choose_verdict(gate_results)
    lines = [
        "# Research Report",
        "",
        "## Verdict",
        "",
        verdict,
        "",
        "## Hypothesis",
        "",
        f"- ID: {hypothesis.id}",
        f"- Thesis: {hypothesis.thesis}",
        f"- Null hypothesis: {hypothesis.null_hypothesis}",
        f"- Asset universe: {', '.join(hypothesis.asset_universe)}",
        f"- Time horizon: {hypothesis.time_horizon}",
        f"- Signal definition: {hypothesis.signal_definition}",
        f"- Expected failure modes: {_format_list(hypothesis.expected_failure_modes)}",
        f"- Falsification tests: {_format_list(hypothesis.falsification_tests)}",
        f"- Pre-registered metrics: {_format_list(hypothesis.pre_registered_metrics)}",
        f"- Thresholds: {hypothesis.acceptance_thresholds}",
        f"- Data requirements: {_format_list(hypothesis.data_requirements)}",
        f"- Posthoc edit policy: {hypothesis.posthoc_edit_policy}",
        "",
        "## Dataset",
        "",
        f"- Source: {manifest.source}",
        f"- Symbols: {', '.join(manifest.symbols)}",
        f"- Date range: {manifest.start_date} to {manifest.end_date}",
        f"- Columns: {', '.join(manifest.columns)}",
        f"- Content hash: {manifest.content_hash}",
        f"- Warnings: {_format_list(manifest.warnings)}",
        "",
        "## Backtest Metrics",
        "",
    ]

    for name in sorted(result.metrics):
        lines.append(f"- {name}: {result.metrics[name]}")

    lines.extend(
        [
            f"- Fingerprint: {result.fingerprint}",
            f"- Trades: {len(result.trades)}",
            f"- Result warnings: {_format_list(result.warnings)}",
            f"- Spec: short_window={spec.short_window}, "
            f"long_window={spec.long_window}, "
            f"transaction_cost_bps={spec.transaction_cost_bps}, "
            f"slippage_bps={spec.slippage_bps}, "
            f"execution_delay_bars={spec.execution_delay_bars}",
            "",
            "## Falsification Gates",
            "",
        ]
    )

    for gate in gate_results:
        lines.extend(
            [
                f"### {gate.gate_name}",
                "",
                f"- Status: {gate.status}",
                f"- Severity: {gate.severity}",
                f"- Threshold: {gate.threshold}",
                f"- Evidence: {gate.evidence}",
                f"- Remediation: {gate.remediation_hint}",
                "",
            ]
        )

    lines.extend(["## Limitations", ""])
    lines.extend(_bullet_lines(limitations))
    lines.extend(["", "## Next Tests", ""])
    lines.extend(_bullet_lines(next_tests))
    lines.extend(
        [
            "",
            "## Safety Note",
            "",
            "This is not investment advice and no live trading was performed.",
            "",
        ]
    )

    return "\n".join(lines)


def _format_list(values: list[str]) -> str:
    return ", ".join(values) if values else "None listed"


def _bullet_lines(values: list[str]) -> list[str]:
    if not values:
        return ["- None listed"]
    return [f"- {value}" for value in values]
