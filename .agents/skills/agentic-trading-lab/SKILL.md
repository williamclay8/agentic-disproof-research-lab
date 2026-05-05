---
name: agentic-trading-lab
description: Use when working on the standalone Trading Lab, agentic trading research, falsification dashboards, evidence ledgers, readiness gates, or research-only market observation workflows.
---

# Agentic Trading Lab

## Core Posture

Treat Trading Lab as a research falsification lab, not an AI hedge fund,
broker integration, signal service, investment advisor, or Vanta module. The
lab's job is to pressure-test trading claims until weak ideas fail.

## Invariants

- Keep Trading Lab separate from Vanta unless Clay explicitly asks to merge.
- Preserve research-only language. Do not add broker, account, credential,
  order-routing, live-signal, personalized advice, or position-sizing surfaces.
- Treat JSON in `runs/` as durable evidence. Markdown, HTML, and web UI are
  views over artifacts, not separate sources of truth.
- Prefer disproof-first framing: rejected, inconclusive, not live-signal ready,
  open evidence gap, promotion blocker.
- Track Lumi hygiene: local, committed, pushed, and deployed/live status.

## Build Pattern

1. Read `AGENTS.md`, `README.md`, and `docs/architecture/product-environment.md`.
2. Identify the evidence artifact that should be source of truth before editing
   reports or UI.
3. Add tests before behavior changes.
4. Keep agent roles bounded: leak auditor, baseline challenger, cost-stress
   critic, reproducibility clerk, regime skeptic, promotion gatekeeper.
5. Separate artifact presence from promotion readiness.
6. Make point-in-time data, leakage risk, unknown feature lineage, baselines,
   costs, slippage, drift, calibration, and human review visible.
7. Regenerate derived reports only after artifact-producing code is verified.

## Good Output

Good work makes claims harder to trust prematurely and easier to audit later.
It should answer: what was known, what failed, which controls were missing, what
would change our mind, and why the current artifact is not a trade instruction.
