# Trading Lab

Trading Lab is a local-only Python research scaffold for falsifying trading
hypotheses with typed artifacts and deterministic offline workflows.

This project is intentionally limited to research records and local data. It
does not include live trading, broker APIs, paper trading, credentials,
network access, or investment recommendation features.

## Quickstart

```bash
python3 -m pytest -q
python3 -m trading_lab.cli run \
  --registry hypotheses/toy-moving-average-crossover.json \
  --hypothesis toy-moving-average-crossover \
  --data examples/toy_prices.csv \
  --json-output runs/example-run.json \
  --output reports/example.md
python3 -m trading_lab.cli dashboard \
  --run runs/example-run.json \
  --output reports/dashboard.html
```

Open `reports/dashboard.html` in a browser to inspect the local falsification
dashboard.

The JSON file in `runs/` is the durable evidence ledger. Markdown and HTML are
views over that evidence, not separate sources of truth.

## Current Scope

- Define pre-registered research hypotheses.
- Describe local dataset manifests.
- Configure offline backtest specifications.
- Store backtest results, falsification gate outcomes, and research reports.

The bundled example is intentionally skeptical: it can produce an
`inconclusive` verdict when a toy idea fails to beat its baseline after costs.
