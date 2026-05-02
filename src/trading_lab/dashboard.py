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
from trading_lab.training import (
    build_evidence_coverage_matrix,
    build_commercial_readiness,
    build_experiment_ledger,
    build_mistake_taxonomy,
    build_training_plan,
    build_workflow_outcomes,
    research_maturity_score,
)
from trading_lab.terminal import catalog_by_intent, power_guidance


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
    maturity = research_maturity_score(gate_results)
    taxonomy = build_mistake_taxonomy(gate_results)

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
            f"<small>{counts['fail']} fail · {counts['warn']} warn · {counts['pass']} pass</small>",
            f"<p>{escape(_verdict_explainer(verdict, counts))}</p>",
            "</div>",
            "</section>",
            '<section class="claim panel">',
            "<h2>Claim Under Test</h2>",
            _definition_list(
                [
                    ("Thesis", hypothesis.thesis),
                    ("Null hypothesis", hypothesis.null_hypothesis),
                    ("Comparator baseline", "buy-and-hold baseline on the offline sample"),
                    *_threshold_rows(hypothesis.acceptance_thresholds),
                    ("Registered before run", "yes"),
                    ("Posthoc edit policy", hypothesis.posthoc_edit_policy),
                ]
            ),
            "</section>",
            '<section class="panel reader-guide">',
            "<h2>Reader Guide</h2>",
            _list(
                [
                    "Start with Outcome Flow to see the usable takeaway.",
                    "Check the evidence cards to see which research controls were recorded.",
                    "Use Mistake Taxonomy to translate warnings into learning objectives.",
                    "Use Falsification Gates only when you need the raw evidence record.",
                ]
            ),
            "</section>",
            '<section class="two-column">',
            _power_boundary_panel(),
            _terminal_catalog_panel(),
            "</section>",
            _research_action_queue(gate_results, next_tests),
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
            _evidence_card(
                "Registry locked",
                "present",
                "Pre-registered fields recorded",
                "The claim was written before evidence review.",
                "It helps separate planned tests from after-the-fact storytelling.",
                "Inspect the Evidence Docket.",
            ),
            _evidence_card(
                "Runner reproducible",
                _gate_status(gate_results, "reproducibility"),
                "Fingerprint comparison",
                "The same inputs produced the same run fingerprint.",
                "Repeatability makes the artifact auditable.",
                "Inspect the Reproducibility panel.",
            ),
            _evidence_card(
                "Walk-forward",
                _gate_status(gate_results, "walk-forward robustness"),
                "Fold evidence",
                "The claim was checked across chronological folds.",
                "Fold weakness shows whether results depend on one small period.",
                "Open the walk-forward gate evidence.",
            ),
            _evidence_card(
                "Parameter sensitivity",
                _gate_status(gate_results, "parameter sensitivity"),
                "Grid evidence",
                "Nearby parameter cells were recorded for comparison.",
                "Stable neighborhoods are more informative than one selected setting.",
                "Inspect the parameter sensitivity gate.",
            ),
            _evidence_card(
                "Cost grid",
                _gate_status(gate_results, "cost grid robustness"),
                "Cost stress evidence",
                "The run records how friction assumptions changed the result.",
                "Cost fragility is often where paper edges disappear.",
                "Inspect the cost grid robustness gate.",
            ),
            "</section>",
            '<section class="panel">',
            "<h2>Evidence Docket</h2>",
            "<p class=\"hint\">This docket shows what was registered before results were interpreted.</p>",
            _definition_list(
                [
                    ("Pre-registered metrics", ", ".join(hypothesis.pre_registered_metrics)),
                    ("Falsification tests", ", ".join(hypothesis.falsification_tests)),
                    ("Data requirements", ", ".join(hypothesis.data_requirements)),
                    ("Dataset hash match", "match" if spec.dataset_hash == manifest.content_hash else "mismatch"),
                    ("Spec hypothesis ID", spec.hypothesis_id),
                ]
            ),
            "</section>",
            _run_comparator(artifacts),
            _outcome_flow(artifacts),
            _commercial_readiness(artifacts),
            _experiment_ledger(artifacts),
            '<section class="two-column">',
            '<section class="panel">',
            "<h2>Research Training Maturity</h2>",
            _definition_list(
                [
                    ("Score", f"{maturity['score']} / 100"),
                    ("Label", maturity["label"]),
                    ("Evidence recorded", ", ".join(maturity["components"])),
                    ("Evidence missing", ", ".join(maturity["missing"])),
                ]
            ),
            "</section>",
            '<section class="panel">',
            "<h2>Mistake Taxonomy</h2>",
            _taxonomy_list(taxonomy),
            "</section>",
            "</section>",
            '<section class="panel">',
            "<h2>Evidence Coverage Matrix</h2>",
            '<p class="hint">A terminal-style status surface for the controls that make this artifact trustworthy.</p>',
            _coverage_matrix_table(gate_results),
            "</section>",
            '<section class="panel">',
            "<h2>Top Evidence Against Claim</h2>",
            _disproof_summary(gate_results),
            "</section>",
            '<section class="panel">',
            "<h2>Current Loop Position</h2>",
            _list(
                [
                    "Warning evidence surfaced before performance metrics.",
                    "The current review focus is the recurring mistake pattern.",
                    "Raw gate evidence remains available for audit.",
                ]
            ),
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
            "<p class=\"hint\">Matching fingerprints indicate the same offline inputs and spec reproduced the same output.</p>",
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
            "<h2>100-Round Training Roadmap</h2>",
            _training_plan_table(build_training_plan()),
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


def _verdict_explainer(verdict: str, counts: dict[str, int]) -> str:
    if verdict == "rejected":
        return "Critical failure evidence is recorded for this claim."
    if verdict == "inconclusive":
        return "The claim was not rejected, but warning gates remain."
    return "No failure or warning gate is recorded; this is not a trading conclusion."


def _threshold_rows(thresholds: dict[str, Any]) -> list[tuple[str, Any]]:
    if not thresholds:
        return [("Pre-registered success condition", "None recorded")]
    return [
        (f"Threshold: {name}", value)
        for name, value in sorted(thresholds.items())
    ]


def _metric_card(label: str, value: Any, caption: str) -> str:
    return (
        '<article class="metric-card">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(str(value))}</strong>"
        f"<small>{escape(caption)}</small>"
        "</article>"
    )


def _evidence_card(
    label: str,
    status: str,
    caption: str,
    meaning: str,
    why_it_matters: str,
    inspect_next: str,
) -> str:
    return (
        f'<article class="metric-card evidence-card evidence-{escape(status)}">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(status)}</strong>"
        f"<small>{escape(caption)}</small>"
        '<dl class="card-explain">'
        f"<dt>What it means</dt><dd>{escape(meaning)}</dd>"
        f"<dt>Why it matters</dt><dd>{escape(why_it_matters)}</dd>"
        f"<dt>Inspect next</dt><dd>{escape(inspect_next)}</dd>"
        "</dl>"
        "</article>"
    )


def _gate_status(gate_results: list[GateResult], gate_name: str) -> str:
    for gate in gate_results:
        if gate.gate_name == gate_name:
            return gate.status
    return "not run"


def _power_boundary_panel() -> str:
    can_items = [
        "Falsify pre-registered research claims.",
        "Compare local evidence artifacts across runs.",
        "Expose leakage, cost fragility, and weak baselines.",
        "Guide the next offline review move.",
    ]
    cannot_items = [
        "Trade, advise, fetch live data, connect brokers, or watch markets.",
        "Turn a non-rejected claim into an allocation or recommendation.",
        "Hide raw evidence behind a polished summary.",
    ]
    return (
        '<section class="panel power-boundary">'
        "<h2>Power Boundary</h2>"
        '<p class="hint">This terminal gives you epistemic power, not execution power.</p>'
        "<h3>Can</h3>"
        + _list(can_items)
        + "<h3>Cannot</h3>"
        + _list(cannot_items)
        + "</section>"
    )


def _terminal_catalog_panel() -> str:
    groups = []
    for intent, components in catalog_by_intent().items():
        labels = ", ".join(component.title for component in components)
        groups.append(f"{intent}: {labels}")
    return (
        '<section class="panel terminal-catalog">'
        "<h2>Offline Terminal Catalog</h2>"
        + _list(list(power_guidance()))
        + '<div class="catalog-groups">'
        + _list(groups)
        + "</div>"
        + "</section>"
    )


def _research_action_queue(
    gate_results: list[GateResult],
    next_tests: list[str],
) -> str:
    return (
        '<section class="panel action-queue">'
        "<h2>Research Action Queue</h2>"
        '<p class="hint">Research-only next moves generated from recorded evidence.</p>'
        + _list(_research_actions(gate_results, next_tests))
        + "</section>"
    )


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


def _coverage_matrix_table(gate_results: list[GateResult]) -> str:
    rows = []
    for item in build_evidence_coverage_matrix(gate_results):
        rows.append(
            "<tr>"
            f"<td>{escape(item['gate_name'])}</td>"
            f"<td>{escape(item['coverage'])}</td>"
            f"<td>{escape(item['status'])}</td>"
            f"<td>{escape(item['meaning'])}</td>"
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table>'
        "<thead><tr><th>Control</th><th>Coverage</th><th>Status</th><th>Meaning</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
    )


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
        pressure = _score_label(artifact.disproof_score)
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
            f"<td>{escape(pressure)}</td>"
            f"<td>{escape(_next_research_move(artifact.gate_results, artifact.next_tests))}</td>"
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
        "<th>Disproof pressure</th><th>Next research move</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
        "</section>"
    )


def _experiment_ledger(artifacts: list[ResearchRunArtifact]) -> str:
    ledger = build_experiment_ledger(artifacts)
    if not ledger:
        return (
            '<section class="panel">'
            "<h2>Experiment Ledger</h2>"
            "<p>No multi-run artifact ledger is recorded yet.</p>"
            "</section>"
        )

    rows = [
        "<tr>"
        f"<td>{escape(str(row['hypothesis_id']))}</td>"
        f"<td>{row['runs']}</td>"
        f"<td>{escape(str(row['latest_verdict']))}</td>"
        f"<td>{row['worst_disproof_score']}</td>"
        f"<td>{escape(str(row['recurring_mistake_types']))}</td>"
        f"<td>{escape(str(row['open_evidence_gaps']))}</td>"
        f"<td>{row['next_curriculum_round']}</td>"
        "</tr>"
        for row in ledger
    ]
    return (
        '<section class="panel">'
        "<h2>Experiment Ledger</h2>"
        '<p class="hint">Multi-run memory for recurring evidence gaps and curriculum state.</p>'
        '<div class="table-wrap"><table>'
        "<thead><tr><th>Hypothesis</th><th>Runs</th><th>Latest verdict</th>"
        "<th>Worst disproof score</th><th>Recurring mistake types</th>"
        "<th>Open evidence gaps</th><th>Next curriculum round</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
        "</section>"
    )


def _outcome_flow(artifacts: list[ResearchRunArtifact]) -> str:
    rows = [
        "<tr>"
        f"<td>{escape(item['label'])}</td>"
        f"<td>{escape(item['outcome'])}</td>"
        f"<td>{escape(item['why'])}</td>"
        "</tr>"
        for item in build_workflow_outcomes(artifacts)
    ]
    return (
        '<section class="panel outcome-panel">'
        "<h2>Outcome Flow</h2>"
        '<p class="hint">The dashboard starts with what the research process can use now.</p>'
        '<div class="table-wrap"><table>'
        "<thead><tr><th>Flow Step</th><th>Usable Outcome</th><th>Reason</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
        "</section>"
    )


def _commercial_readiness(artifacts: list[ResearchRunArtifact]) -> str:
    readiness = build_commercial_readiness(artifacts)
    return (
        '<section class="panel">'
        "<h2>Commercial Readiness</h2>"
        + _definition_list(
            [
                ("Audience", readiness["audience"]),
                ("Paid data asset", readiness["paid_data_asset"]),
                ("Current packaging", readiness["current_packaging"]),
                ("Next packaging step", readiness["next_packaging_step"]),
                ("Trust boundary", readiness["trust_boundary"]),
            ]
        )
        + "</section>"
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
            f"{_evidence_sentence(gate)}"
        )
        for gate in pressure
    ]
    return _list(items, already_escaped=True)


def _evidence_sentence(gate: GateResult) -> str:
    evidence = gate.evidence
    if {
        "strategy_cumulative_return",
        "baseline_cumulative_return",
    }.issubset(evidence):
        return (
            " — "
            f"strategy {_format_percent(evidence['strategy_cumulative_return'])} "
            f"vs baseline {_format_percent(evidence['baseline_cumulative_return'])}"
        )
    if "passing_folds" in evidence and "folds" in evidence:
        return f" — {evidence['passing_folds']} / {evidence['folds']} folds passed"
    return ""


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
            f"<td>{escape(_gate_evidence_summary(gate))}</td>"
            f"<td><pre>{escape(evidence)}</pre></td>"
            f"<td>{escape(gate.remediation_hint)}</td>"
            "</tr>"
        )

    return (
        '<div class="table-wrap"><table>'
        "<thead><tr>"
        "<th>Status</th><th>Gate</th><th>Severity</th><th>Threshold</th>"
        "<th>What this evidence says</th><th>Raw evidence</th><th>Evidence gap</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
    )


def _gate_evidence_summary(gate: GateResult) -> str:
    evidence = gate.evidence
    if {
        "strategy_cumulative_return",
        "baseline_cumulative_return",
    }.issubset(evidence):
        return (
            f"Strategy returned {_format_percent(evidence['strategy_cumulative_return'])} "
            f"vs baseline {_format_percent(evidence['baseline_cumulative_return'])}."
        )
    if "passing_folds" in evidence and "folds" in evidence:
        return f"{evidence['passing_folds']} / {evidence['folds']} folds passed."
    if "flagged_columns" in evidence:
        return f"Potential forward-looking fields recorded: {evidence['flagged_columns']}."
    if gate.status == "pass":
        return "Recorded evidence satisfied this control."
    if gate.status == "warn":
        return "Recorded evidence raised a warning for further review."
    return "Recorded evidence failed this control."


def _next_research_move(gate_results: list[GateResult], next_tests: list[str]) -> str:
    return _research_actions(gate_results, next_tests)[0]


def _status_sort_key(status: str) -> int:
    return {"fail": 0, "warn": 1, "pass": 2}.get(status, 3)


def _metrics_table(metrics: dict[str, Any]) -> str:
    rows = [
        "<tr>"
        f"<td>{escape(_metric_label(name))}</td>"
        f"<td>{escape(_format_metric(name, metrics[name]))}</td>"
        "</tr>"
        for name in sorted(metrics)
    ]
    return (
        '<div class="table-wrap"><table>'
        "<thead><tr><th>Metric</th><th>Value</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
    )


def _metric_label(name: str) -> str:
    labels = {
        "average_exposure": "Average exposure",
        "bars": "Offline bars",
        "baseline_cumulative_return": "Baseline cumulative return",
        "max_drawdown": "Max drawdown",
        "strategy_cumulative_return": "Strategy cumulative return",
        "symbols": "Symbols",
        "total_cost": "Total cost",
        "turnover": "Turnover",
    }
    return labels.get(name, name.replace("_", " ").title())


def _format_metric(name: str, value: Any) -> str:
    if name in {
        "strategy_cumulative_return",
        "baseline_cumulative_return",
        "max_drawdown",
        "total_cost",
        "turnover",
        "average_exposure",
    } and isinstance(value, (int, float)):
        return _format_percent(value)
    if name == "bars":
        return f"{value} offline bars"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _format_percent(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return str(value)
    return f"{value * 100:.2f}%"


def _taxonomy_list(items: list[dict[str, str]]) -> str:
    if not items:
        return "<p>No non-pass evidence items recorded.</p>"
    rows = [
        "<tr>"
        f"<td>{escape(item['name'])}</td>"
        f"<td>{escape(item['gate_name'])}</td>"
        f"<td>{escape(item['learning_focus'])}</td>"
        "</tr>"
        for item in items
    ]
    return (
        '<div class="table-wrap"><table>'
        "<thead><tr><th>Mistake Type</th><th>Gate</th><th>Learning Focus</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
    )


def _training_plan_table(plan: list[dict[str, object]]) -> str:
    preview = plan[:10]
    rows = [
        "<tr>"
        f"<td>{item['round']}</td>"
        f"<td>{escape(str(item['phase']))}</td>"
        f"<td>{escape(str(item['focus']))}</td>"
        "</tr>"
        for item in preview
    ]
    return (
        '<p class="hint">100 offline review rounds; showing the first 10 as the current training preview.</p>'
        '<div class="table-wrap training-scroll"><table>'
        "<thead><tr><th>Round</th><th>Phase</th><th>Focus</th></tr></thead>"
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
