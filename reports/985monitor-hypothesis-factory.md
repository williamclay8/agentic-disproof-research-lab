# 985monitor FOMO Hypothesis Factory

## Boundary

Research-only, point-in-time falsification asset; not a trade instruction, not personalized investment advice, not a live signal, and not a broker or order-routing action. Not investment advice. Not a live signal. Not copy-trading guidance.

No validated trading edge was found. The factory found ranked candidate edge hypotheses for offline falsification only.

## Source

- URL: https://985monitor.xyz/fomo/
- Snapshot timestamp: 2026-05-03T12:06:00Z
- Freshness status: stale_snapshot
- Provenance status: incomplete

## Edge Verdict

- Edge status: `candidate_edge_found_not_validated`
- Validated edge found: `False`
- Best candidate edge: `pnl_window_persistence`
- Summary: The strongest candidate is multi-window PnL persistence: identities that recur across source-reported leaderboard windows may be a less fragile cohort than one-window leaderboard rows. This is not a validated trading edge because the snapshot lacks row-level timing, forward outcomes, baselines, and friction evidence.

## Candidate Edges

### 1. Multi-Window PnL Persistence Candidate

- ID: `pnl_window_persistence`
- Verdict: `candidate_edge_unvalidated`
- Score: `88`
- Evidence hook: 44 of 116 PnL identities appear in at least two leaderboard windows, and 13 appear in at least three windows.
- Hypothesis: Multi-window leaderboard recurrence may identify a cohort that is less fragile than one-window source-reported winners.
- Null hypothesis: Recurring leaderboard membership has no forward value after survivorship, concentration, and baseline controls.
- Aggregate support:
  - unique_pnl_identities: `116`
  - appears_in_two_or_more_windows: `44`
  - appears_in_three_or_more_windows: `13`
  - four_window_identities: `2`
  - largest_pairwise_overlap: `22`
- Required next data:
  - historical leaderboard snapshots with inclusion timestamps
  - forward wallet outcomes after inclusion
  - active-wallet universe for random and volume-weighted controls
  - fees, slippage, latency, spread, and capacity assumptions
- Baselines:
  - random active-wallet cohort
  - volume-weighted active-wallet cohort
  - one-window-only leaderboard cohort
- Falsification criteria:
  - Reject if recurring cohorts do not beat one-window and random baselines in forward-only windows.
  - Reject if edge disappears after removing top-10 concentrated identities.
  - Reject if returns are positive only before costs, latency, slippage, or capacity limits.
- Why it might fail:
  - source-reported PnL may be backward-looking survivorship bias
  - a small head cohort may dominate the apparent pattern
  - wallet labels may not represent controlled current wallets
- Promotion blockers:
  - incomplete provenance
  - stale point-in-time snapshot
  - no row-level source timestamp
  - no forward-only outcome test
  - no baseline challenge
  - no fee/slippage/latency/capacity model
  - no rights review
  - no human review

### 2. Leaderboard Concentration Fade Candidate

- ID: `concentration_fade`
- Verdict: `candidate_edge_unvalidated`
- Score: `76`
- Evidence hook: Top-10 concentration is high across PnL and volume windows, suggesting crowding or head-cohort fragility may be testable.
- Hypothesis: Highly concentrated leaderboard windows may be more fragile than diversified cohorts in forward tests.
- Null hypothesis: Top-heavy concentration has no independent relationship with future cohort decay after activity and volume controls.
- Aggregate support:
  - pnl_top10_share: `{'24h': 58.4, '7d': 52.9, '30d': 41.3, 'all_time': 71.6}`
  - volume_top10_share: `{'24h': 84.7, '7d': 79.4, '30d': 77.4, 'all_time': 79.4}`
- Required next data:
  - forward outcomes by leaderboard window
  - cohort concentration over time
  - liquidity and spread context
- Baselines:
  - same-window low-concentration cohorts
  - volume-matched non-leaderboard cohorts
  - market beta or token-sector movement
- Falsification criteria:
  - Reject if top-heavy cohorts do not decay faster than matched cohorts.
  - Reject if concentration adds no explanatory value beyond volume.
- Why it might fail:
  - concentration may reflect genuine skill or capital rather than fragility
  - forward sample may be too small
  - token-level regime effects may dominate wallet effects
- Promotion blockers:
  - incomplete provenance
  - stale point-in-time snapshot
  - no row-level source timestamp
  - no forward-only outcome test
  - no baseline challenge
  - no fee/slippage/latency/capacity model
  - no rights review
  - no human review

### 3. Efficiency-Adjusted Leaderboard Candidate

- ID: `efficiency_adjusted_leaderboard`
- Verdict: `candidate_edge_unvalidated`
- Score: `72`
- Evidence hook: Source-reported PnL divided by volume is highly dispersed, creating a testable normalized cohort distinct from gross PnL rank.
- Hypothesis: Efficiency-adjusted leaderboard rows may identify different research cohorts than gross PnL or raw volume rank.
- Null hypothesis: PnL-to-volume efficiency has no forward value after trade count, liquidity, costs, and outlier controls.
- Aggregate support:
  - pnl_to_volume_median_pct: `{'24h': 4.4, '7d': 9.7, '30d': 8.2}`
  - pnl_to_volume_p90_pct: `{'24h': 38.6, '7d': 121.4, '30d': 726.6}`
- Required next data:
  - trade-level timing and token exposure
  - forward outcomes after inclusion
  - liquidity, spread, and minimum-volume filters
  - trade count controls
- Baselines:
  - raw PnL rank
  - raw volume rank
  - volume-matched leaderboard cohorts
  - minimum-volume-filtered random active wallets
- Falsification criteria:
  - Reject if efficiency is driven by tiny-volume outliers.
  - Reject if efficiency-adjusted cohorts do not beat raw-rank baselines forward-only.
  - Reject if edge disappears after liquidity, trade count, cost, and slippage filters.
- Why it might fail:
  - small denominators can inflate PnL-to-volume ratios
  - source-reported PnL may include stale or backward-looking outcomes
  - liquidity constraints may make apparent efficiency non-monetizable
- Promotion blockers:
  - incomplete provenance
  - stale point-in-time snapshot
  - no row-level source timestamp
  - no forward-only outcome test
  - no baseline challenge
  - no fee/slippage/latency/capacity model
  - no rights review
  - no human review

### 4. Common-Follow Social Consensus Candidate

- ID: `social_consensus_filter`
- Verdict: `candidate_edge_unvalidated`
- Score: `69`
- Evidence hook: The social sheet has 44 rows followed by at least 10 top accounts, creating an aggregate social-context bucket to test.
- Hypothesis: High common-follow buckets may help prioritize which KOL-wallet claims deserve diligence before lower-consensus rows.
- Null hypothesis: Common-follow count adds no value beyond simple activity, volume, or leaderboard-window metadata.
- Aggregate support:
  - social_rows: `1065`
  - followed_by_topN_at_least_5: `134`
  - followed_by_topN_at_least_10: `44`
  - social_rows_without_real_wallet: `121`
- Required next data:
  - historical common-follow snapshots
  - activity and volume controls
  - forward outcomes and source refresh history
- Baselines:
  - random social rows
  - volume-matched social rows
  - leaderboard-window-only rows
- Falsification criteria:
  - Reject if common-follow buckets do not improve forward diligence hit-rate over controls.
  - Reject if signal vanishes when rows without verified wallet coverage are excluded.
- Why it might fail:
  - common-follow may measure popularity rather than trading value
  - social context may be stale or incomplete
  - using social fields can drift into targeting or identity claims
- Promotion blockers:
  - incomplete provenance
  - stale point-in-time snapshot
  - no row-level source timestamp
  - no forward-only outcome test
  - no baseline challenge
  - no fee/slippage/latency/capacity model
  - no rights review
  - no human review

### 5. Cross-Chain Wallet Coverage Candidate

- ID: `cross_chain_coverage_filter`
- Verdict: `candidate_edge_unvalidated`
- Score: `61`
- Evidence hook: 74 of 116 PnL identities have both SOL and EVM coverage, making wallet coverage a possible quality-control filter.
- Hypothesis: Rows with broader source-reported wallet coverage may produce more auditable research cohorts than rows with sparse coverage.
- Null hypothesis: Chain coverage does not improve auditability or forward evidence quality after activity controls.
- Aggregate support:
  - pnl_union_wallet_coverage: `{'unique_identities': 116, 'real_solana': 115, 'real_evm': 75, 'both_chains': 74}`
  - social_wallet_coverage: `{'unique_rows': 1065, 'real_solana': 921, 'real_evm': 391, 'both_chains': 368, 'neither_chain': 121}`
- Required next data:
  - wallet-linkage provenance
  - chain-specific activity history
  - coverage completeness by refresh
- Baselines:
  - SOL-only rows
  - EVM-only rows
  - rows with no real-wallet field
- Falsification criteria:
  - Reject if both-chain rows do not produce cleaner lineage or better forward evidence coverage.
  - Reject if wallet coverage is an artifact of source labeling rather than verifiable activity.
- Why it might fail:
  - more coverage may simply mean more source enrichment, not more edge
  - wallet ownership may be incorrectly inferred
- Promotion blockers:
  - incomplete provenance
  - stale point-in-time snapshot
  - no row-level source timestamp
  - no forward-only outcome test
  - no baseline challenge
  - no fee/slippage/latency/capacity model
  - no rights review
  - no human review

### 6. Freshness Arbitrage Candidate

- ID: `freshness_arbitrage_rejected`
- Verdict: `candidate_edge_unvalidated`
- Score: `34`
- Evidence hook: The inspected snapshot was stale despite an hourly-update claim, so freshness itself is a research risk and possible data-product gap.
- Hypothesis: A reliable point-in-time archive could have monetizable research value because stale public snapshots are not enough.
- Null hypothesis: Freshness capture adds no actionable research value after rights, provenance, and refresh costs.
- Aggregate support:
  - freshness_status: `stale_snapshot`
  - snapshot_timestamp_utc: `2026-05-03T12:06:00Z`
  - inspected_at_utc: `2026-05-13T15:51:00Z`
- Required next data:
  - scheduled refresh archive
  - source availability logs
  - change detection and content hashes
- Baselines:
  - manual snapshot checks
  - static public page
  - random refresh cadence
- Falsification criteria:
  - Reject if archived refreshes rarely change or cannot be licensed.
  - Reject if refresh latency is too high for even delayed research workflows.
- Why it might fail:
  - source may not update reliably
  - rights review may block redistribution
  - freshness is operational value, not a trading edge
- Promotion blockers:
  - incomplete provenance
  - stale point-in-time snapshot
  - no row-level source timestamp
  - no forward-only outcome test
  - no baseline challenge
  - no fee/slippage/latency/capacity model
  - no rights review
  - no human review

## Promotion Status

- Status: `not_live_signal_ready`
- Promotion ready: `False`
- Reason: Candidate edges are hypothesis seeds only. No candidate has passed point-in-time lineage, baseline, leakage, cost, slippage, latency, capacity, rights, or human-review gates.

## Blocked Outputs

- personalized investment advice
- copy-trading instruction
- broker or order-routing action
- live signal
- raw wallet resale without rights review
- current-balance or ownership claims without source proof
