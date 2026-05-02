"""Static HTML dashboard for offline research falsification runs."""

from __future__ import annotations

import json
from html import escape
from typing import Any

from trading_lab.artifacts import ResearchRunArtifact
from trading_lab.gates import choose_verdict
from trading_lab.models import (
    BacktestResult,
    BacktestSpec,
    DatasetManifest,
    GateResult,
    Hypothesis,
)


def render_dashboard_html(
    hypothesis: Hypothesis,
    manifest: DatasetManifest,
    spec: BacktestSpec,
    result: BacktestResult,
    gate_results: list[GateResult],
    limitations: list[str],
    next_tests: list[str],
    run_artifacts: list[ResearchRunArtifact] | None = None,
) -> str:
    verdict = choose_verdict(gate_results)
    counts = _status_counts(gate_results)
    artifacts = run_artifacts or []

    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>Agentic Trading Research Lab</title>",
            f"<style>{_CSS}</style>",
            "</head>",
            "<body>",
            '<main class="shell">',
            '<section class="topbar">',
            "<div>",
            '<p class="eyebrow">Agentic research lab</p>',
            "<h1>Falsification cockpit</h1>",
            f'<p class="subtitle">{escape(hypothesis.thesis)}</p>',
            "</div>",
            f'<div class="verdict verdict-{escape(verdict.replace(" ", "-"))}">',
            "<span>Falsification result</span>",
            f"<strong>{escape(verdict)}</strong>",
            "</div>",
            "</section>",
            '<section class="claim panel">',
            "<h2>Claim Under Test</h2>",
            _definition_list(
                [
                    ("Thesis", hypothesis.thesis),
                    ("Null hypothesis", hypothesis.null_hypothesis),
                    ("Comparator baseline", "buy-and-hold baseline on the offline sample"),
                    ("Pre-registered success condition", hypothesis.acceptance_thresholds),
                    ("Posthoc edit policy", hypothesis.posthoc_edit_policy),
                ]
            ),
            "</section>",
            '<section class="safety">',
            (
                "offline research artifact only, not investment advice. This page "
                "does not provide trade guidance, live signals, paper "
                "trading, broker connectivity, or execution instructions. Treat "
                "any non-rejected result as a request for harder tests, not as "
                "evidence of a tradable edge. No broker APIs, live trading, or "
                "network data are connected."
            ),
            "</section>",
            '<section class="grid metrics">',
            _evidence_card("Registry locked", "present", "Pre-registered fields recorded"),
            _evidence_card("Runner reproducible", _gate_status(gate_results, "reproducibility"), "Fingerprint comparison"),
            _evidence_card("Walk-forward", _gate_status(gate_results, "walk-forward robustness"), "Fold evidence"),
            _evidence_card("Parameter sensitivity", _gate_status(gate_results, "parameter sensitivity"), "Grid evidence"),
            _evidence_card("Cost grid", _gate_status(gate_results, "cost grid robustness"), "Cost stress evidence"),
            "</section>",
            '<section class="panel">',
            "<h2>Evidence Docket</h2>",
            _definition_list(
                [
                    ("Pre-registered metrics", ", ".join(hypothesis.pre_registered_metrics)),
                    ("Falsification tests", ", ".join(hypothesis.falsification_tests)),
                    ("Data requirements", ", ".join(hypothesis.data_requirements)),
                    ("Dataset hash match", spec.dataset_hash == manifest.content_hash),
                    ("Spec hypothesis ID", spec.hypothesis_id),
                ]
            ),
            "</section>",
            _run_comparator(artifacts),
            '<section class="panel">',
            "<h2>Top Evidence Against Claim</h2>",
            _disproof_summary(gate_results),
            "</section>",
            '<section class="panel">',
            "<h2>Falsification Gates</h2>",
            _gate_table(gate_results),
            "</section>",
            '<section class="two-column">',
            '<section class="panel">',
            "<h2>Backtest Metrics</h2>",
            _metrics_table(result.metrics),
            "</section>",
            '<section class="panel">',
            "<h2>Reproducibility</h2>",
            _definition_list(
                [
                    ("Dataset hash", manifest.content_hash),
                    ("Run fingerprint", result.fingerprint),
                    ("Source", manifest.source),
                    ("Date range", f"{manifest.start_date} to {manifest.end_date}"),
                ]
            ),
            "</section>",
            "</section>",
            '<section class="two-column">',
            '<section class="panel">',
            "<h2>Hypothesis Registry</h2>",
            _definition_list(
                [
                    ("ID", hypothesis.id),
                    ("Null hypothesis", hypothesis.null_hypothesis),
                    ("Asset universe", ", ".join(hypothesis.asset_universe)),
                    ("Time horizon", hypothesis.time_horizon),
                    ("Signal definition", hypothesis.signal_definition),
                    ("Posthoc edit policy", hypothesis.posthoc_edit_policy),
                ]
            ),
            "</section>",
            '<section class="panel">',
            "<h2>Dataset & Spec</h2>",
            _definition_list(
                [
                    ("Columns", ", ".join(manifest.columns)),
                    ("Symbols", ", ".join(manifest.symbols)),
                    ("Short window", spec.short_window),
                    ("Long window", spec.long_window),
                    ("Transaction cost bps", spec.transaction_cost_bps),
                    ("Slippage bps", spec.slippage_bps),
                    ("Execution delay bars", spec.execution_delay_bars),
                ]
            ),
            "</section>",
            "</section>",
            '<section class="two-column">',
            '<section class="panel">',
            "<h2>Expected Failure Modes</h2>",
            _list(hypothesis.expected_failure_modes),
            "</section>",
            '<section class="panel">',
            "<h2>Open Evidence Gaps</h2>",
            _list(next_tests),
            "</section>",
            "</section>",
            '<section class="panel">',
            "<h2>Agentic Disproof Loop</h2>",
            _list(_OPERATING_LOOP),
            "</section>",
            '<section class="panel">',
            "<h2>Limitations</h2>",
            _list(limitations),
            "</section>",
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def _status_counts(gate_results: list[GateResult]) -> dict[str, int]:
    counts = {"fail": 0, "warn": 0, "pass": 0}
    for gate in gate_results:
        counts[gate.status] += 1
    return counts


def _metric_card(label: str, value: Any, caption: str) -> str:
    return (
        '<article class="metric-card">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(str(value))}</strong>"
        f"<small>{escape(caption)}</small>"
        "</article>"
    )


def _evidence_card(label: str, status: str, caption: str) -> str:
    return (
        f'<article class="metric-card evidence-card evidence-{escape(status)}">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(status)}</strong>"
        f"<small>{escape(caption)}</small>"
        "</article>"
    )


def _gate_status(gate_results: list[GateResult], gate_name: str) -> str:
    for gate in gate_results:
        if gate.gate_name == gate_name:
            return gate.status
    return "not run"


def _run_comparator(artifacts: list[ResearchRunArtifact]) -> str:
    if not artifacts:
        return ""

    ordered = sorted(artifacts, key=lambda artifact: artifact.disproof_score, reverse=True)
    rows = []
    for artifact in ordered:
        metrics = artifact.result.metrics
        strategy_return = metrics.get("strategy_cumulative_return", "missing")
        baseline_return = metrics.get("baseline_cumulative_return", "missing")
        delta = _return_delta(metrics)
        rows.append(
            "<tr>"
            f"<td>{escape(artifact.run_id)}</td>"
            f"<td>{escape(artifact.verdict)}</td>"
            f"<td>{artifact.disproof_score}</td>"
            f"<td>{escape(artifact.spec.dataset_hash[:12])}</td>"
            f"<td>{escape(artifact.result.fingerprint[:12])}</td>"
            f"<td>{escape(str(artifact.spec.transaction_cost_bps))}</td>"
            f"<td>{escape(str(artifact.spec.slippage_bps))}</td>"
            f"<td>{escape(str(artifact.spec.execution_delay_bars))}</td>"
            f"<td>{escape(str(strategy_return))}</td>"
            f"<td>{escape(str(baseline_return))}</td>"
            f"<td>{escape(str(delta))}</td>"
            f"<td>{escape(_score_label(artifact.disproof_score))}</td>"
            "</tr>"
        )

    return (
        '<section class="panel">'
        "<h2>Runner Evidence</h2>"
        '<p class="hint">Sorted by disproof score; higher values indicate more '
        "failed or warning gates, not a trading instruction.</p>"
        '<div class="table-wrap"><table>'
        "<thead><tr><th>Run</th><th>Verdict</th><th>Disproof score</th>"
        "<th>Dataset hash</th><th>Fingerprint</th><th>Cost bps</th>"
        "<th>Slippage bps</th><th>Delay bars</th>"
        "<th>Strategy return</th><th>Baseline return</th><th>Delta</th>"
        "<th>Evidence strength</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
        "</section>"
    )


def _return_delta(metrics: dict[str, Any]) -> Any:
    strategy_return = metrics.get("strategy_cumulative_return")
    baseline_return = metrics.get("baseline_cumulative_return")
    if not isinstance(strategy_return, (int, float)) or not isinstance(
        baseline_return, (int, float)
    ):
        return "missing"
    return strategy_return - baseline_return


def _score_label(score: int) -> str:
    if score >= 5:
        return "5+ disproof points"
    if score >= 2:
        return "2-4 disproof points"
    return "0-1 disproof points"


def _disproof_summary(gate_results: list[GateResult]) -> str:
    pressure = [gate for gate in gate_results if gate.status in ("fail", "warn")]
    if not pressure:
        return (
            "<p>No failure or warning gate is recorded for this run.</p>"
        )

    items = [
        (
            f"<strong>{escape(gate.gate_name)}</strong>: "
            f"{escape(gate.status)} against threshold "
            f"<code>{escape(gate.threshold)}</code>"
        )
        for gate in pressure
    ]
    return _list(items, already_escaped=True)


def _gate_table(gate_results: list[GateResult]) -> str:
    ordered = sorted(gate_results, key=lambda gate: _status_sort_key(gate.status))
    rows = []
    for gate in ordered:
        evidence = json.dumps(gate.evidence, sort_keys=True, default=str)
        rows.append(
            "<tr>"
            f'<td><span class="pill pill-{escape(gate.status)}">'
            f"{escape(gate.status)}</span></td>"
            f"<td>{escape(gate.gate_name)}</td>"
            f"<td>{escape(gate.severity)}</td>"
            f"<td><code>{escape(gate.threshold)}</code></td>"
            f"<td><pre>{escape(evidence)}</pre></td>"
            f"<td>{escape(gate.remediation_hint)}</td>"
            "</tr>"
        )

    return (
        '<div class="table-wrap"><table>'
        "<thead><tr>"
        "<th>Status</th><th>Gate</th><th>Severity</th><th>Threshold</th>"
        "<th>Evidence</th><th>Evidence gap</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
    )


def _status_sort_key(status: str) -> int:
    return {"fail": 0, "warn": 1, "pass": 2}.get(status, 3)


def _metrics_table(metrics: dict[str, Any]) -> str:
    rows = [
        "<tr>"
        f"<td>{escape(name)}</td>"
        f"<td>{escape(str(metrics[name]))}</td>"
        "</tr>"
        for name in sorted(metrics)
    ]
    return (
        '<div class="table-wrap"><table>'
        "<thead><tr><th>Metric</th><th>Value</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
    )


def _definition_list(items: list[tuple[str, Any]]) -> str:
    pairs = [
        f"<dt>{escape(label)}</dt><dd>{escape(str(value))}</dd>"
        for label, value in items
    ]
    return f"<dl>{''.join(pairs)}</dl>"


def _list(values: list[str], *, already_escaped: bool = False) -> str:
    if not values:
        return "<p>None listed.</p>"
    items = [f"<li>{value if already_escaped else escape(value)}</li>" for value in values]
    return f"<ul>{''.join(items)}</ul>"


_CSS = """
:root {
  color-scheme: light;
  --bg: #f6f7f4;
  --ink: #18201d;
  --muted: #59645f;
  --line: #d8ddd6;
  --panel: #ffffff;
  --pass: #285f6b;
  --warn: #94620d;
  --fail: #a33a35;
  --note: #e9f0ed;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
  line-height: 1.45;
}

.shell {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 28px 0 44px;
}

.topbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line);
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

h1,
h2,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 8px;
  font-size: clamp(2rem, 5vw, 4rem);
  letter-spacing: 0;
}

h2 {
  margin-bottom: 14px;
  font-size: 1rem;
}

.subtitle {
  max-width: 760px;
  margin-bottom: 0;
  color: var(--muted);
  font-size: 1rem;
}

.verdict {
  min-width: 230px;
  border-left: 4px solid var(--muted);
  padding: 14px 16px;
  background: var(--panel);
}

.verdict span,
.metric-card span,
.metric-card small {
  display: block;
  color: var(--muted);
  font-size: 0.78rem;
}

.verdict strong,
.metric-card strong {
  display: block;
  margin-top: 4px;
  font-size: 1.25rem;
}

.verdict-rejected {
  border-color: var(--fail);
}

.verdict-inconclusive {
  border-color: var(--warn);
}

.verdict-passed-preliminary-gates {
  border-color: var(--pass);
}

.safety,
.panel,
.metric-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}

.safety {
  margin: 18px 0;
  padding: 12px 14px;
  background: var(--note);
  color: #33423b;
  font-size: 0.92rem;
}

.grid {
  display: grid;
  gap: 12px;
}

.metrics {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.metric-card {
  min-height: 116px;
  padding: 16px;
}

.metric-card strong {
  margin: 12px 0 8px;
  font-size: 2rem;
}

.two-column {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.panel,
.two-column {
  margin-top: 14px;
}

.panel {
  padding: 18px;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 680px;
}

th,
td {
  border-bottom: 1px solid var(--line);
  padding: 10px 8px;
  text-align: left;
  vertical-align: top;
  font-size: 0.88rem;
}

th {
  color: var(--muted);
  font-size: 0.76rem;
  text-transform: uppercase;
}

code,
pre {
  margin: 0;
  color: #25302c;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  white-space: pre-wrap;
}

.pill {
  display: inline-flex;
  min-width: 52px;
  justify-content: center;
  border-radius: 999px;
  padding: 3px 8px;
  color: #fff;
  font-size: 0.76rem;
  font-weight: 700;
}

.pill-pass {
  background: var(--pass);
}

.pill-warn {
  background: var(--warn);
}

.pill-fail {
  background: var(--fail);
}

dl {
  display: grid;
  grid-template-columns: minmax(140px, 0.35fr) minmax(0, 1fr);
  gap: 10px 14px;
  margin: 0;
}

dt {
  color: var(--muted);
  font-size: 0.82rem;
}

dd {
  margin: 0;
}

ul {
  margin: 0;
  padding-left: 18px;
}

li + li {
  margin-top: 7px;
}

@media (max-width: 820px) {
  .topbar,
  .two-column {
    grid-template-columns: 1fr;
    display: grid;
  }

  .metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .verdict {
    width: 100%;
  }
}

@media (max-width: 520px) {
  .shell {
    width: min(100% - 20px, 1180px);
    padding-top: 18px;
  }

  .metrics {
    grid-template-columns: 1fr;
  }

  dl {
    grid-template-columns: 1fr;
  }
}
""".strip()


_OPERATING_LOOP = [
    "Pre-register the claim before seeing results.",
    "Assume the idea is wrong until evidence survives harder checks.",
    "Run the weakest baseline first, then promote stronger baselines.",
    "Treat missing evidence as a critical failure, not as neutral.",
    "Surface the strongest evidence against the claim above performance metrics.",
    "Stress costs, delays, windows, datasets, and comparators before adding complexity.",
    "Record every run as JSON so later dashboards compare evidence, not memory.",
    "Use non-rejected results only to design harsher falsification tests.",
]
