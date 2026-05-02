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
from trading_lab.training import build_evidence_coverage_matrix
from trading_lab.terminal import power_guidance


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
        "## Power Boundary",
        "",
        "- This report can falsify pre-registered claims, compare local evidence, and expose fragility.",
        "- This report cannot trade, advise, fetch live data, connect brokers, or watch markets.",
        *_bullet_lines(list(power_guidance())),
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

    lines.extend(["## Evidence Coverage", ""])
    for row in build_evidence_coverage_matrix(gate_results):
        lines.append(
            f"- {row['gate_name']}: {row['coverage']} / {row['status']} - {row['meaning']}"
        )

    lines.extend(["", "## Research Action Queue", ""])
    lines.extend(_bullet_lines(_research_actions(gate_results, next_tests)))

    lines.extend(["## Limitations", ""])
    lines.extend(_bullet_lines(limitations))
    lines.extend(["", "## Next Tests", ""])
    lines.extend(_bullet_lines(next_tests))
    lines.extend(
        [
            "",
            "## Safety Note",
            "",
            (
                "This is not investment advice. No live trading, live data, broker "
                "connection, credentials, order routing, or execution action was performed."
            ),
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


def _research_actions(gate_results: list[GateResult], next_tests: list[str]) -> list[str]:
    actions: list[str] = []
    if any(gate.status == "fail" for gate in gate_results):
        actions.append("Reject or quarantine the claim until failure evidence is resolved.")
    if any(gate.status == "warn" for gate in gate_results):
        actions.append("Retest warning evidence against a stricter comparator or robustness control.")
    missing = [
        row["gate_name"]
        for row in build_evidence_coverage_matrix(gate_results)
        if row["coverage"] == "missing"
    ]
    if missing:
        actions.append(f"Record missing evidence controls: {', '.join(missing[:3])}.")
    actions.extend(f"Run next offline test: {test}" for test in next_tests[:2])
    if not actions:
        actions.append("Archive the run as reviewed, then design a harder falsification pass.")
    return actions
