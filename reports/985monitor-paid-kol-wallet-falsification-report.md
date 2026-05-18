# Paid KOL Wallet Falsification Report

Report ID: `985monitor-fomo-paid-kol-wallet-falsification-2026-05-13`

Source packet: `runs/985monitor/paid-kol-wallet-falsification-report.json`

## Boundary

This is a research-only, point-in-time falsification report. Not investment advice. Not a live signal. Not copy-trading guidance. It does not include broker, account, credential, order, fill, execution, position sizing, entry, exit, target, or stop-loss instructions.

The report is designed to help a buyer decide whether a source-reported KOL wallet dataset deserves deeper diligence. It can support paid research, diligence, and falsification workflows. It cannot support current trading decisions or claims about wallet ownership, current balances, or future returns.

## Executive Verdict

Verdict: `inconclusive_blocked`

The 985monitor FOMO packet is commercially useful as a paid falsification report seed. It has enough structure to support a buyer-ready diligence memo: five CSV manifests, a clear source timestamp, cross-window identity overlap, wallet coverage, concentration metrics, and a broad social/common-follow sheet.

It does not pass promotion gates for live signals, copy-trading, or predictive-performance claims. The blockers are stale source timing, incomplete provenance, missing row-level lineage, no forward-only outcome test, no baseline comparison, no execution-friction model, and no redistribution rights review.

## Buyer

Best-fit buyers:

- Research desks that need a skeptical read on KOL wallet claims.
- Funds or crypto operators evaluating whether a wallet dataset is worth deeper diligence.
- Founders building wallet-intelligence products who need a safe evidence packet.
- Market-intelligence teams that want aggregate KOL-wallet research without raw targeting lists.

## Source Snapshot

- Source URL: `https://985monitor.xyz/fomo/`
- Source timestamp: `2026-05-03T12:06:00Z`
- Inspected at: `2026-05-13T15:51:00Z`
- Freshness status: `stale_snapshot`
- Provenance status: `incomplete`
- Safe source claim: 985monitor published five FOMO-derived CSV snapshots with aggregate leaderboard and common-follow structure as of the May 3, 2026 snapshot.

## Evidence Inventory

| File | Rows | Field Label | SHA256 |
| --- | ---: | --- | --- |
| `fomo_24h_leaderboard_real_wallets.csv` | 50 | source-reported leaderboard context | `51d076aae62f4f0906e068d544ba4a5207205cdc277b76e4bf60af70e0f777a0` |
| `fomo_7d_leaderboard_real_wallets.csv` | 50 | source-reported leaderboard context | `f4631f4207025d00ebefe2d5ed9d760dd022a39b10a6142bfc9584a314b229e4` |
| `fomo_30d_leaderboard_real_wallets.csv` | 50 | source-reported leaderboard context | `42f9c5b8ea67b7dc7f747853088016c4edd1c7ad07039af16bfa6668d13cf179` |
| `fomo_alltime_leaderboard_real_wallets.csv` | 25 | source-reported leaderboard context | `cb4f42b92add4f0d12f026d348af072b578440a4340297a0ca369c4cf348519d` |
| `fomo_smart_money_FULL_real_wallets.csv` | 1065 | source-reported public/social context | `dfc442b58d2b7a36ef095fd72aa09c59a95e88d247da7ae0968b196c624b92da` |

Aggregate shape:

- Total CSV rows: `1240`
- PnL leaderboard rows: `175`
- Unique PnL identities across 24h, 7d, 30d, and all-time sheets: `116`
- Social/common-follow rows: `1065`
- PnL union wallet coverage: `115/116` with real Solana, `75/116` with real EVM, `74/116` with both
- Social wallet coverage: `921/1065` with Solana, `391/1065` with EVM, `368/1065` with both, `121/1065` with neither

## Falsification Findings

### 1. Freshness Blocks Promotion

The page claimed hourly updates, but the inspected page and all five CSV files showed the same May 3, 2026 source timestamp.

Meaning: this can be sold only as a historical falsification packet until a refresh and archive process exists.

Next safe action: set up point-in-time snapshot capture with source timestamp, ingest timestamp, schema hash, and content hash.

### 2. Provenance Is Incomplete

No scrape code, source API contract, row-level collection timestamp, wallet-linkage method, or USD valuation source was included.

Meaning: the report can evaluate source-reported claims but cannot certify wallet ownership, current balances, or future edge.

Next safe action: require provenance review before external paid distribution beyond aggregate research.

### 3. PnL Persistence Is Unproven

The four PnL leaderboards contain 116 unique identities. Membership distribution:

- One window: `72`
- Two windows: `31`
- Three windows: `11`
- Four windows: `2`

Meaning: persistence is the first paid-research hook, but the current snapshot cannot prove repeatable skill.

Next safe action: test forward-only rank persistence against random active-wallet and volume-weighted baselines.

### 4. Concentration Risk Is High

Top-10 concentration is material:

| Window | PnL Top-10 Share | Volume Top-10 Share |
| --- | ---: | ---: |
| 24h | 58.4% | 84.7% |
| 7d | 52.9% | 79.4% |
| 30d | 41.3% | 77.4% |
| All-time | 71.6% | 79.4% |

Meaning: a small head cohort may dominate apparent results, making the dataset useful for concentration-risk reporting.

Next safe action: run leave-top-10-out and identity-cluster stress tests before claiming cohort robustness.

### 5. Social/Common-Follow Data Is Context Only

The social/common-follow sheet has 1,065 rows. It includes 44 rows followed by at least 10 top accounts and 121 rows without a real wallet populated.

Meaning: the common-follow sheet can support aggregate social-context research, not targeting, contact lists, or coordination claims.

Next safe action: keep social fields aggregate or pseudonymous and separate them from any misconduct conclusion.

## Buyer-Ready Offer

Product: KOL Wallet Falsification Memo

Scope:

- One source packet or campaign window.
- CSV manifest review.
- Provenance and freshness audit.
- Aggregate concentration review.
- PnL persistence screen.
- Social/common-follow context screen.
- Baseline and forward-test plan.
- Promotion decision: reject, quarantine, or advance to deeper diligence.

Delivery format:

- Markdown or PDF memo.
- Machine-readable JSON companion.
- Appendix with source manifests and blocked outputs.
- Optional follow-up research backlog.

Commercial packaging:

- One-off memo: fixed-scope diligence.
- Retainer: recurring KOL wallet falsification reports.
- Workshop: teach a team how to run the falsification workflow.
- Internal tool seed: convert the packet into a private dashboard after rights review.

## Proof Gates Before Stronger Claims

The report must remain `inconclusive_blocked` until these gates pass:

- Source timestamp and ingest timestamp recorded for every future snapshot.
- Every CSV manifest includes filename, row count, schema, byte size, hash, source URL, and provenance status.
- Leaderboard fields remain labeled source-reported context, not performance proof.
- Common-follow fields remain labeled social context, not identity or coordination proof.
- Forward-only outcomes beat random active-wallet and volume-weighted baselines before any edge language is allowed.
- Fees, slippage, latency, spread, and capacity stress tests are recorded before monetization claims are increased.
- Human and rights review happens before any external sale of derived data.

## Blocked Outputs

Do not ship or sell this report as:

- Personalized investment advice.
- Copy-trading instruction.
- Broker or order-routing action.
- Live signal.
- Raw wallet resale without rights review.
- Current-balance or ownership claims without source proof.
- Identity targeting or contact list.
- Coordination or insider claim without independent evidence.

## What Would Change Our Mind

Confidence could increase only if a future packet adds:

- Archived historical snapshots with row-level timing.
- Source and ingest timestamps.
- Verified schema and content hashes for each refresh.
- Clear wallet-linkage method.
- USD valuation source and timestamp.
- Baseline tests against random active-wallet and volume-weighted cohorts.
- Walk-forward tests after inclusion.
- Cost, slippage, latency, spread, and capacity assumptions.
- Rights review for any commercial redistribution.

## Final Client Summary

The 985monitor FOMO packet is worth turning into a paid research product because it exposes a buyer-relevant question: do KOL wallet leaderboards survive basic falsification, or are they stale, concentrated, and provenance-thin?

The answer for this snapshot is cautious: it is a useful diligence seed, not a current trading edge. The strongest commercial deliverable is a paid falsification memo that helps buyers avoid overtrusting source-reported KOL wallet claims before they spend capital, build products, or publish narratives around them.
