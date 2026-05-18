# 985monitor FOMO Research Playbook

## Boundary

Research-only, point-in-time falsification asset; not a trade instruction, not personalized investment advice, not a live signal, and not a broker or order-routing action. Not investment advice. Not a live signal. Not copy-trading guidance.

This packet completes the five plays as research and commercialization artifacts. It does not launch a website, signal service, broker workflow, or public data product.

## Source Snapshot

- Source URL: https://985monitor.xyz/fomo/
- Snapshot timestamp: 2026-05-03T12:06:00Z
- Inspected at: 2026-05-13T15:51:00Z
- Freshness status: stale_snapshot
- Provenance status: incomplete
- Safe claim: 985monitor published five FOMO-derived CSV snapshots with aggregate leaderboard and common-follow structure as of the May 3, 2026 snapshot.
- PnL unique identities: 116
- Social rows: 1065

## CSV Manifests

### fomo_24h_leaderboard_real_wallets.csv

- URL: https://985monitor.xyz/fomo/fomo_24h_leaderboard_real_wallets.csv
- Rows: 50
- Bytes: 13800
- SHA256: 51d076aae62f4f0906e068d544ba4a5207205cdc277b76e4bf60af70e0f777a0
- Source timestamp: 2026-05-03T12:06:00Z
- Provenance status: incomplete
- Field label: source-reported leaderboard context
- Schema: rank, handle, name, pnl_period_usd, total_volume_usd, trades, followers, real_solana, real_solana_usd, real_evm, real_evm_usd, sol_count, evm_count, fomo_old_solana, fomo_old_evm, twitter, fomo_id

### fomo_7d_leaderboard_real_wallets.csv

- URL: https://985monitor.xyz/fomo/fomo_7d_leaderboard_real_wallets.csv
- Rows: 50
- Bytes: 14026
- SHA256: f4631f4207025d00ebefe2d5ed9d760dd022a39b10a6142bfc9584a314b229e4
- Source timestamp: 2026-05-03T12:06:00Z
- Provenance status: incomplete
- Field label: source-reported leaderboard context
- Schema: rank, handle, name, pnl_period_usd, total_volume_usd, trades, followers, real_solana, real_solana_usd, real_evm, real_evm_usd, sol_count, evm_count, fomo_old_solana, fomo_old_evm, twitter, fomo_id

### fomo_30d_leaderboard_real_wallets.csv

- URL: https://985monitor.xyz/fomo/fomo_30d_leaderboard_real_wallets.csv
- Rows: 50
- Bytes: 13827
- SHA256: 42f9c5b8ea67b7dc7f747853088016c4edd1c7ad07039af16bfa6668d13cf179
- Source timestamp: 2026-05-03T12:06:00Z
- Provenance status: incomplete
- Field label: source-reported leaderboard context
- Schema: rank, handle, name, pnl_period_usd, total_volume_usd, trades, followers, real_solana, real_solana_usd, real_evm, real_evm_usd, sol_count, evm_count, fomo_old_solana, fomo_old_evm, twitter, fomo_id

### fomo_alltime_leaderboard_real_wallets.csv

- URL: https://985monitor.xyz/fomo/fomo_alltime_leaderboard_real_wallets.csv
- Rows: 25
- Bytes: 7054
- SHA256: cb4f42b92add4f0d12f026d348af072b578440a4340297a0ca369c4cf348519d
- Source timestamp: 2026-05-03T12:06:00Z
- Provenance status: incomplete
- Field label: source-reported leaderboard context
- Schema: rank, handle, name, pnl_period_usd, total_volume_usd, trades, followers, real_solana, real_solana_usd, real_evm, real_evm_usd, sol_count, evm_count, fomo_old_solana, fomo_old_evm, twitter, fomo_id

### fomo_smart_money_FULL_real_wallets.csv

- URL: https://985monitor.xyz/fomo/fomo_smart_money_FULL_real_wallets.csv
- Rows: 1065
- Bytes: 253608
- SHA256: dfc442b58d2b7a36ef095fd72aa09c59a95e88d247da7ae0968b196c624b92da
- Source timestamp: 2026-05-03T12:06:00Z
- Provenance status: incomplete
- Field label: source-reported public/social context
- Schema: rank, handle, name, real_solana, real_solana_usd, real_evm, real_evm_usd, total_volume_usd, followed_by_topN, leaderboard_windows, sol_wallet_count, evm_wallet_count, fomo_old_solana, fomo_old_evm, twitter, fomo_id

## Provenance Gaps

- No row-level collection timestamp was present.
- No scrape code or source API contract was published with the snapshot.
- The method for labeling wallets as real owner-controlled wallets is not independently verified.
- USD valuation source and timestamp are unknown.
- The page claims hourly updates, but fetched headers showed the same May 3, 2026 timestamp.

## Completed Plays

### 1. Paid KOL Wallet Falsification Report

- ID: paid_falsification_report
- Completion artifact: reports/985monitor-paid-kol-wallet-falsification-report.md
- Buyer: Research desks, founders, funds, and crypto operators who need a skeptical read on KOL wallet claims.
- Revenue mechanism: Paid monthly report, bespoke diligence memo, or sponsor-free research subscription.
- Status: complete_as_research_artifact
- Blocker: Cannot market as alpha until forward tests, baselines, and friction controls exist.
- Source fields or aggregates:
  - PnL leaderboard rank by window
  - multi-window identity persistence
  - top-10 PnL and volume concentration
  - wallet coverage by chain
  - source provenance gaps
- Deliverable:
  - A recurring report template that asks what survived and what failed.
  - A baseline section comparing persistent winners against one-window winners.
  - A limitations section that leads with timestamp and provenance gaps.
- Proof gates:
  - Keep all outputs delayed or point-in-time.
  - Use aggregate or pseudonymous cohorts by default.
  - State provenance gaps before any monetization claim.
  - Block promotion if users could reasonably treat the output as current trade guidance.
  - Require forward-only rank persistence tests before saying a cohort has predictive value.
  - Require baseline and concentration controls before selling any edge narrative.
- Blocked outputs:
  - personalized investment advice
  - copy-trading instruction
  - broker or order-routing action
  - live signal
  - raw wallet resale without rights review
  - current-balance or ownership claims without source proof

### 2. Anti-Copy Wallet Quality Score

- ID: anti_copy_wallet_quality_score
- Completion artifact: docs/985monitor-fomo-research-playbook.md#2-anti-copy-wallet-quality-score
- Buyer: Wallet-tool builders, Telegram bot teams, trading communities, and diligence teams.
- Revenue mechanism: B2B score API spec, CSV score export, or diligence pack.
- Status: complete_as_research_artifact
- Blocker: Defamation, privacy, and provenance risk if labels are attached to people rather than evidence cohorts.
- Source fields or aggregates:
  - window_count per identity
  - PnL-to-volume ratio
  - PnL-per-trade ratio where trades exist
  - balance-to-volume ratio
  - SOL-only, EVM-only, both-chain, and no-real-wallet coverage flags
  - social followed_by_topN buckets
- Deliverable:
  - A component scorecard: persistence, concentration risk, wallet coverage, social crowding, and provenance risk.
  - Risk labels such as evidence thin, concentration heavy, stale snapshot, and provenance blocked.
  - An appeal/removal and rights-review note for public packaging.
- Proof gates:
  - Keep all outputs delayed or point-in-time.
  - Use aggregate or pseudonymous cohorts by default.
  - State provenance gaps before any monetization claim.
  - Block promotion if users could reasonably treat the output as current trade guidance.
  - Do not score a named person; score dataset rows or pseudonymous cohorts.
  - Require an explanation for every score component.
- Blocked outputs:
  - personalized investment advice
  - copy-trading instruction
  - broker or order-routing action
  - live signal
  - raw wallet resale without rights review
  - current-balance or ownership claims without source proof

### 3. KOL Campaign Forensics Template

- ID: kol_campaign_forensics_template
- Completion artifact: docs/985monitor-fomo-research-playbook.md#3-kol-campaign-forensics-template
- Buyer: Token teams, exchanges, communities, compliance-minded sponsors, and investor relations teams.
- Revenue mechanism: Fixed-scope forensic review, pre-campaign diligence, or post-campaign audit retainer.
- Status: complete_as_research_artifact
- Blocker: Legal and reputational sensitivity if the output implies misconduct without evidence.
- Source fields or aggregates:
  - public handle/identity count as aggregate
  - wallet coverage availability
  - social common-follow clusters
  - leaderboard window metadata
  - volume concentration by cohort
- Deliverable:
  - A campaign intake checklist that requests token, campaign window, disclosed relationships, and public source links.
  - A forensics memo layout: evidence observed, what cannot be proven, disclosure questions, and dump-risk indicators.
  - A no-harassment and no-deanonymization handling policy.
- Proof gates:
  - Keep all outputs delayed or point-in-time.
  - Use aggregate or pseudonymous cohorts by default.
  - State provenance gaps before any monetization claim.
  - Block promotion if users could reasonably treat the output as current trade guidance.
  - Require campaign date windows and public source citations before making any campaign finding.
  - Separate disclosure questions from misconduct conclusions.
- Blocked outputs:
  - personalized investment advice
  - copy-trading instruction
  - broker or order-routing action
  - live signal
  - raw wallet resale without rights review
  - current-balance or ownership claims without source proof

### 4. Derived Aggregate Dataset Licensing Packet

- ID: derived_aggregate_dataset_licensing_packet
- Completion artifact: docs/985monitor-fomo-research-playbook.md#4-derived-aggregate-dataset-licensing-packet
- Buyer: Dashboard builders, data startups, research desks, and market-intelligence vendors.
- Revenue mechanism: Monthly derived dataset license, aggregate feed, or private research data room.
- Status: complete_as_research_artifact
- Blocker: Redistribution rights and wallet-label provenance remain unresolved.
- Source fields or aggregates:
  - row counts by source file
  - identity overlap counts
  - wallet coverage counts
  - top-N concentration
  - followed_by_topN distribution buckets
  - provenance and rights-review status
- Deliverable:
  - A license packet for aggregate metrics only.
  - A data dictionary that excludes raw wallet-handle mappings unless rights review approves them.
  - A buyer-safe redaction policy and refresh cadence note.
- Proof gates:
  - Keep all outputs delayed or point-in-time.
  - Use aggregate or pseudonymous cohorts by default.
  - State provenance gaps before any monetization claim.
  - Block promotion if users could reasonably treat the output as current trade guidance.
  - Complete source rights review before redistribution.
  - Ship aggregates first; keep raw wallet maps out of commercial packages by default.
- Blocked outputs:
  - personalized investment advice
  - copy-trading instruction
  - broker or order-routing action
  - live signal
  - raw wallet resale without rights review
  - current-balance or ownership claims without source proof

### 5. Trading Lab Hypothesis Factory

- ID: trading_lab_hypothesis_factory
- Completion artifact: hypotheses/985monitor-fomo-wallet-falsification.json
- Buyer: Internal Trading Lab research, workshops, and founder-facing falsification demos.
- Revenue mechanism: Paid workshop, implementation kit, or research operating-system demo.
- Status: complete_as_research_artifact
- Blocker: Historical snapshots and executable friction data are missing.
- Source fields or aggregates:
  - point-in-time event timing
  - leaderboard persistence
  - cluster convergence
  - crowding or fade behavior
  - category-specific skill
  - monetization after fees, slippage, delay, and capacity limits
- Deliverable:
  - A pre-registered hypothesis registry entry.
  - A ranked backlog of falsification tests.
  - A promotion gate that keeps the result not live-signal ready until forward tests pass.
- Proof gates:
  - Keep all outputs delayed or point-in-time.
  - Use aggregate or pseudonymous cohorts by default.
  - State provenance gaps before any monetization claim.
  - Block promotion if users could reasonably treat the output as current trade guidance.
  - Require row-level timestamps before event-impact claims.
  - Require fees, slippage, delay, and capacity checks before monetization claims.
  - Reject any hypothesis whose value disappears after baseline or leakage controls.
- Blocked outputs:
  - personalized investment advice
  - copy-trading instruction
  - broker or order-routing action
  - live signal
  - raw wallet resale without rights review
  - current-balance or ownership claims without source proof

## Promotion Status

- Status: blocked_by_incomplete_provenance
- Promotion ready: False
- Reason: Point-in-time snapshot lacks row-level timing, independent wallet verification, live execution evidence, legal rights review, and forward-tested monetization proof.

## Global Blocked Outputs

- personalized investment advice
- copy-trading instruction
- broker or order-routing action
- live signal
- raw wallet resale without rights review
- current-balance or ownership claims without source proof
