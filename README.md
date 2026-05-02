# Trading Lab

Trading Lab is a local-only Python research scaffold for falsifying trading
hypotheses with typed artifacts and deterministic offline workflows.

This repository is intentionally separate from Vanta and the Vanta privacy
suite. Dashboard articles, reports, ledgers, and research narratives should stay
here unless Clay explicitly asks to merge or cross-link them. See
`docs/project-boundary.md`.

This project is intentionally limited to research records, local data, and
explicitly collected market-observation snapshots. It does not include live
trading, broker APIs, paper trading, credentials, order routing, or investment
recommendation features.

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
python3 -m trading_lab.cli terminal MSFT
python3 -m trading_lab.cli collect-live \
  --provider fixture \
  --symbols MSFT AAPL \
  --max-events 2 \
  --snapshot runs/live/latest.json
# Optional public market-data observation, still research-only:
python3 -m trading_lab.cli collect-live \
  --provider kraken-public-rest \
  --symbols BTC/USD \
  --max-events 1 \
  --snapshot runs/live/kraken-latest.json
python3 -m trading_lab.cli snapshot-dashboard \
  --snapshot runs/live/latest.json \
  --output reports/live-snapshot.html
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
- Use a research terminal catalog to focus symbols, discover research actions,
  and explain power boundaries without adding execution.
- Share local research snapshots through an in-memory topic hub for future
  dashboard/workflow components.
- Collect fixture-backed market observations into auditable local snapshots
  with source, freshness, and provenance labels.
- Optionally collect public Kraken ticker observations, gated by explicit CLI
  invocation and the same safety kill switches.

The bundled example is intentionally skeptical: it can produce an
`inconclusive` verdict when a toy idea fails to beat its baseline after costs.

## Power Boundary

The terminal layer is for epistemic power: finding what a claim cannot survive.
It can focus a ticker-like symbol, route local commands, compare evidence
artifacts, collect explicitly requested research observations, and surface
missing controls. It cannot trade, advise, connect brokers, watch accounts,
handle credentials, route orders, or submit orders.

Kill switches:

```bash
TRADING_LAB_DISABLE_NETWORK=1 python3 -m trading_lab.cli collect-live ...
TRADING_LAB_DISABLE_REALTIME=1 python3 -m trading_lab.cli collect-live ...
```

Either switch blocks observation collection before a snapshot is written.
