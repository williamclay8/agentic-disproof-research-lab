# Agentic Research Lab Design

## Goal

Build a local-only agentic trading research lab that is better at disproving ideas than proving them. The lab must make weak trading hypotheses fail quickly, preserve evidence, and avoid any live trading or broker integration.

## Product Shape

The first version is a Python CLI/package. It loads local example data, validates a pre-registered hypothesis, runs an offline backtest with realistic frictions, applies falsification gates, and writes a markdown report.

The lab is educational tooling only. It does not provide investment advice, trade recommendations, broker connectivity, live credentials, paper trading, autonomous execution, leverage, derivatives, or portfolio management.

## Architecture

The core is a falsification kernel:

- `trading_lab.models`: typed dataclasses for hypotheses, dataset manifests, backtest specs, results, gate results, and reports.
- `trading_lab.data`: local CSV loading, schema validation, date ordering, and immutable data hashing.
- `trading_lab.backtest`: deterministic offline backtest with one-bar execution delay, costs, and simple bounded exposure.
- `trading_lab.metrics`: return, drawdown, turnover, exposure, and cost-aware metric helpers.
- `trading_lab.gates`: hygiene and anti-overfitting checks that fail closed where evidence is missing.
- `trading_lab.reports`: markdown report generation with verdicts and evidence.
- `trading_lab.cli`: command entry point for running the example experiment.

Agents are represented in V1 as deterministic critique prompts and gate outputs, not LLM-driven autonomous actors. LLM agents can be added later only after the evaluation substrate is reliable.

## Data Flow

1. Load a local CSV from `examples/`.
2. Create a `DatasetManifest` with source, symbols, date range, required columns, warnings, and a content hash.
3. Define one educational hypothesis in code or config.
4. Build a `BacktestSpec` that declares cost, slippage, execution delay, and baseline.
5. Run the backtest.
6. Run falsification gates.
7. Generate a markdown report with verdict, metrics, gate evidence, limitations, and next tests.

## Verdicts

The lab avoids the word "accepted" for trading ideas.

- `rejected`: at least one critical falsification gate fails.
- `inconclusive`: no critical failure, but evidence is too weak or incomplete.
- `passed preliminary gates`: the idea survived V1 gates, but this is not a trade recommendation.

## V1 Gates

- Data schema gate: required columns exist.
- Chronology gate: timestamps are sorted and unique.
- Lookahead naming gate: reject columns whose names imply future or target leakage.
- Cost realism gate: results must include non-negative cost and slippage assumptions.
- Baseline comparison gate: compare strategy return to buy-and-hold after costs.
- Cost sensitivity gate: rerun or inspect performance under higher cost assumptions.
- Reproducibility gate: identical data and spec produce the same fingerprint.

## Testing Strategy

Use TDD for the kernel:

- Dataclass validation tests.
- Tiny hand-checkable data fixtures.
- CSV loading and manifest hash tests.
- Backtest tests for one-bar delay, cost drag, and position behavior.
- Metric tests for drawdown and turnover.
- Gate tests for lookahead leakage and missing cost evidence.
- Report tests for required sections and verdict language.
- CLI smoke test for a complete toy experiment.

## Non-Goals

- No live trading.
- No broker APIs.
- No account keys or secrets.
- No paper trading.
- No web dashboard.
- No autonomous order creation.
- No advice or recommendations.
- No complex portfolio optimizer.
- No paid market data integration.

## Lumi Hygiene

V1 changes are local code/content changes until committed. Nothing is pushed or deployed by default. Since there is no live website in V1, deployment status is not applicable.
