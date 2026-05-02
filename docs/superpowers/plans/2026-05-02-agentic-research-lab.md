# Agentic Research Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-only Python falsification kernel for agentic trading research ideas.

**Architecture:** The package centers on typed research artifacts, deterministic offline backtests, falsification gates, and markdown reporting. V1 uses local CSV data only and deliberately excludes live trading, broker APIs, credentials, and autonomous execution.

**Tech Stack:** Python 3.11+, `pytest`, standard-library dataclasses, `csv`, `argparse`, and `pathlib`.

---

## File Structure

- `pyproject.toml`: package metadata and pytest configuration.
- `README.md`: project purpose, safety boundaries, and quickstart.
- `src/trading_lab/models.py`: core dataclasses and validation.
- `src/trading_lab/data.py`: CSV loading, row validation, manifest creation.
- `src/trading_lab/metrics.py`: return, drawdown, turnover, exposure metrics.
- `src/trading_lab/backtest.py`: moving-average style signal and offline backtest engine.
- `src/trading_lab/gates.py`: falsification gates and verdict selection.
- `src/trading_lab/reports.py`: markdown report generation.
- `src/trading_lab/cli.py`: `run-example` command.
- `examples/toy_prices.csv`: deterministic toy dataset.
- `tests/`: focused tests for each module and CLI smoke behavior.

### Task 1: Scaffold Package And Models

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/trading_lab/__init__.py`
- Create: `src/trading_lab/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing model tests**

Create `tests/test_models.py` with tests that require strict hypothesis and spec validation.

- [ ] **Step 2: Run tests to verify failure**

Run: `python3 -m pytest tests/test_models.py -q`
Expected: fail because `trading_lab` does not exist.

- [ ] **Step 3: Implement package metadata and dataclasses**

Create `pyproject.toml`, `README.md`, `src/trading_lab/__init__.py`, and `src/trading_lab/models.py` with validated dataclasses for `Hypothesis`, `DatasetManifest`, `BacktestSpec`, `BacktestResult`, `GateResult`, and `ResearchReport`.

- [ ] **Step 4: Run tests to verify pass**

Run: `python3 -m pytest tests/test_models.py -q`
Expected: all model tests pass.

### Task 2: Data Loading And Manifest Hashes

**Files:**
- Create: `src/trading_lab/data.py`
- Create: `examples/toy_prices.csv`
- Test: `tests/test_data.py`

- [ ] **Step 1: Write failing data tests**

Test CSV loading, required columns, chronology validation, duplicate date rejection, and stable manifest hashes.

- [ ] **Step 2: Run tests to verify failure**

Run: `python3 -m pytest tests/test_data.py -q`
Expected: fail because `trading_lab.data` does not exist.

- [ ] **Step 3: Implement CSV loader and toy dataset**

Implement standard-library CSV loading into dictionaries with parsed dates and floats. Add deterministic toy prices in `examples/toy_prices.csv`.

- [ ] **Step 4: Run tests to verify pass**

Run: `python3 -m pytest tests/test_data.py -q`
Expected: all data tests pass.

### Task 3: Metrics And Offline Backtest

**Files:**
- Create: `src/trading_lab/metrics.py`
- Create: `src/trading_lab/backtest.py`
- Test: `tests/test_metrics.py`
- Test: `tests/test_backtest.py`

- [ ] **Step 1: Write failing metrics and backtest tests**

Test max drawdown, turnover, one-bar execution delay, cost drag, baseline comparison fields, and deterministic fingerprints.

- [ ] **Step 2: Run tests to verify failure**

Run: `python3 -m pytest tests/test_metrics.py tests/test_backtest.py -q`
Expected: fail because metrics and backtest modules do not exist.

- [ ] **Step 3: Implement metrics and backtest**

Implement simple moving-average crossover signals, delayed positions, per-change transaction costs, returns, trades, and deterministic result fingerprints.

- [ ] **Step 4: Run tests to verify pass**

Run: `python3 -m pytest tests/test_metrics.py tests/test_backtest.py -q`
Expected: all metrics and backtest tests pass.

### Task 4: Falsification Gates And Reports

**Files:**
- Create: `src/trading_lab/gates.py`
- Create: `src/trading_lab/reports.py`
- Test: `tests/test_gates.py`
- Test: `tests/test_reports.py`

- [ ] **Step 1: Write failing gate and report tests**

Test lookahead column rejection, missing cost evidence, baseline warnings, cost sensitivity, verdict selection, and report sections.

- [ ] **Step 2: Run tests to verify failure**

Run: `python3 -m pytest tests/test_gates.py tests/test_reports.py -q`
Expected: fail because gates and reports modules do not exist.

- [ ] **Step 3: Implement gates and markdown reporting**

Implement fail-closed gates and report generation with hypothesis, data, metrics, gate evidence, verdict, limitations, and next tests.

- [ ] **Step 4: Run tests to verify pass**

Run: `python3 -m pytest tests/test_gates.py tests/test_reports.py -q`
Expected: all gate and report tests pass.

### Task 5: CLI End-To-End Example

**Files:**
- Create: `src/trading_lab/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI smoke test**

Test that `python3 -m trading_lab.cli run-example --output <tmp>` writes a markdown report and prints the verdict from the repo root.

- [ ] **Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_cli.py -q`
Expected: fail because CLI module does not exist.

- [ ] **Step 3: Implement CLI**

Implement `run-example` with `argparse`, local toy data, the educational hypothesis, backtest spec, falsification gates, and report writing.

- [ ] **Step 4: Run focused and full verification**

Run: `python3 -m pytest tests/test_cli.py -q`
Expected: CLI test passes.

Run: `python3 -m pytest -q`
Expected: full suite passes.

Run: `python3 -m trading_lab.cli run-example --output reports/example.md`
Expected: report is written and the command prints a verdict.

## Self-Review

- Spec coverage: V1 implements local data loading, typed hypotheses, offline backtest, falsification gates, markdown report, and CLI smoke flow.
- Placeholder scan: no task depends on unspecified live trading, broker keys, paper trading, or dashboard work.
- Type consistency: model names are shared across tasks and are defined before use.
