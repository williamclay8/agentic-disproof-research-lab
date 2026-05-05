# Trading Lab Product Environment

Trading Lab is now shaped as a standalone product lane around the existing
Python research kernel. It must not be mounted into Vanta pages, docs, routes,
or privacy-suite messaging unless Clay explicitly asks for that merge.

## Target Shape

```text
apps/
  api/        local HTTP API wrapper around research artifacts
  web/        product UI shell that reads from the API
  worker/     bounded job runner for ingestion, backtests, and report renders
packages/
  trading_kernel/   boundary marker for src/trading_lab
  contracts/        API contracts and generated clients later
infra/
  docker-compose.yml
```

The current API and web servers use the Python standard library so this repo can
stay runnable with the existing dependency surface. The intended production
backend is FastAPI after dependency management, migrations, auth, and deployment
are introduced intentionally.

## Local Commands

```bash
make test
make worker-example
make worker-snapshot
make api
make web
make dev
docker compose -f infra/docker-compose.yml up --build
```

CI runs `python3 -m pytest -q` with network and realtime collection disabled.
No public deployment target is configured yet; live status remains local-only
until a deployment provider and health check are added intentionally.

Local URLs:

- Web: `http://127.0.0.1:5199`
- API health: `http://127.0.0.1:5299/health`
- Example run evidence: `http://127.0.0.1:5299/runs/example`
- Latest snapshot: `http://127.0.0.1:5299/snapshots/latest`
- Terminal overview: `http://127.0.0.1:5299/terminal/overview`
- Confidence readiness: `http://127.0.0.1:5299/confidence/readiness`
- Agentic review: `http://127.0.0.1:5299/agentic/review`
- Evidence rigor: `http://127.0.0.1:5299/evidence/rigor`

## Product Rules

- The kernel remains deterministic, local-first, and artifact-backed.
- API routes expose evidence and snapshots, not investment recommendations.
- The first screen operates as a ranked falsification terminal: attention queue,
  agent review, evidence rigor, weakest gates, bounded observation, provenance,
  confidence readiness, and raw evidence drawer.
- Readiness artifacts can be present without being promotion-ready. Minimum
  sample thresholds, drift/calibration metrics, risk controls, and human review
  govern promotion language.
- Future setup visibility is governed by evidence maturity, not language
  confidence: observe-only, research candidate, validated setup note, shadow
  confidence, and limited live review.
- Long-running ingestion and backtests belong in workers, not request handlers.
- Provider collection belongs server-side with provenance and license metadata.
- Generated reports and `runs/` are durable evidence artifacts, not the product
  database.
- Postgres and Redis are present in Compose as the next local-parity base, but
  code should not depend on them until migrations and adapters exist.

## Promotion Gates

The lab can show research artifacts today. It cannot show confident trade
guidance, live signals, setup recommendations, broker actions, or personalized
advice until these exist and pass:

- point-in-time data integrity
- leakage tests
- realistic fee and slippage assumptions
- walk-forward validation
- paper-trading ledger
- live-shadow drift monitor
- confidence calibration
- policy and copy guardrails
- human approval gates
- counsel-reviewed product language

Live setup information also needs a setup visibility gate, evidence passport,
live observation quality, execution reality context, setup fragility fields,
paper ledger, live-shadow drift monitor, calibration history, risk packet, and
human review packet. Until those exist, the terminal should say `not
live-signal ready`.

Default product language is `research only`.
