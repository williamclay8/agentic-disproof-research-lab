"""Research-only 985monitor/FOMO playbook artifacts.

This module turns a point-in-time third-party wallet leaderboard snapshot into
bounded research assets. It intentionally avoids raw wallet resale, live
signals, personalized advice, broker actions, or copy-trading instructions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PLAY_IDS = (
    "paid_falsification_report",
    "anti_copy_wallet_quality_score",
    "kol_campaign_forensics_template",
    "derived_aggregate_dataset_licensing_packet",
    "trading_lab_hypothesis_factory",
)

RESEARCH_BOUNDARY = (
    "Research-only, point-in-time falsification asset; not a trade instruction, "
    "not personalized investment advice, not a live signal, and not a broker or "
    "order-routing action. Not investment advice. Not a live signal. Not "
    "copy-trading guidance."
)

GLOBAL_BLOCKED_OUTPUTS = (
    "personalized investment advice",
    "copy-trading instruction",
    "broker or order-routing action",
    "live signal",
    "raw wallet resale without rights review",
    "current-balance or ownership claims without source proof",
)


@dataclass(frozen=True)
class FomoSnapshotSummary:
    source_url: str
    snapshot_timestamp_utc: str
    inspected_at_utc: str
    freshness_status: str
    row_counts: dict[str, int]
    csv_manifests: list[dict[str, Any]]
    pnl_union_unique_identities: int
    pnl_membership_distribution: dict[str, int]
    pairwise_overlap: dict[str, int]
    wallet_coverage: dict[str, dict[str, int]]
    concentration: dict[str, dict[str, float]]
    efficiency: dict[str, dict[str, float]]
    social_segments: dict[str, int]
    schema_notes: list[str]
    provenance_gaps: list[str]
    safe_claim: str


@dataclass(frozen=True)
class FomoPlay:
    id: str
    title: str
    completion_artifact: str
    buyer: str
    revenue_mechanism: str
    source_fields_or_aggregates: list[str]
    deliverable: list[str]
    proof_gates: list[str]
    blocker: str
    blocked_outputs: list[str]
    completion_status: str = "complete_as_research_artifact"
    research_only: bool = True


def build_985monitor_snapshot_summary() -> FomoSnapshotSummary:
    """Return the verified aggregate snapshot facts used by the playbook."""

    return FomoSnapshotSummary(
        source_url="https://985monitor.xyz/fomo/",
        snapshot_timestamp_utc="2026-05-03T12:06:00Z",
        inspected_at_utc="2026-05-13T15:51:00Z",
        freshness_status="stale_snapshot",
        row_counts={
            "24h": 50,
            "7d": 50,
            "30d": 50,
            "all_time": 25,
            "social": 1065,
            "total_rows": 1240,
        },
        csv_manifests=[
            {
                "filename": "fomo_24h_leaderboard_real_wallets.csv",
                "url": "https://985monitor.xyz/fomo/fomo_24h_leaderboard_real_wallets.csv",
                "row_count": 50,
                "content_length_bytes": 13800,
                "sha256": "51d076aae62f4f0906e068d544ba4a5207205cdc277b76e4bf60af70e0f777a0",
                "source_timestamp_utc": "2026-05-03T12:06:00Z",
                "provenance_status": "incomplete",
                "field_label": "source-reported leaderboard context",
                "schema": _pnl_schema(),
            },
            {
                "filename": "fomo_7d_leaderboard_real_wallets.csv",
                "url": "https://985monitor.xyz/fomo/fomo_7d_leaderboard_real_wallets.csv",
                "row_count": 50,
                "content_length_bytes": 14026,
                "sha256": "f4631f4207025d00ebefe2d5ed9d760dd022a39b10a6142bfc9584a314b229e4",
                "source_timestamp_utc": "2026-05-03T12:06:00Z",
                "provenance_status": "incomplete",
                "field_label": "source-reported leaderboard context",
                "schema": _pnl_schema(),
            },
            {
                "filename": "fomo_30d_leaderboard_real_wallets.csv",
                "url": "https://985monitor.xyz/fomo/fomo_30d_leaderboard_real_wallets.csv",
                "row_count": 50,
                "content_length_bytes": 13827,
                "sha256": "42f9c5b8ea67b7dc7f747853088016c4edd1c7ad07039af16bfa6668d13cf179",
                "source_timestamp_utc": "2026-05-03T12:06:00Z",
                "provenance_status": "incomplete",
                "field_label": "source-reported leaderboard context",
                "schema": _pnl_schema(),
            },
            {
                "filename": "fomo_alltime_leaderboard_real_wallets.csv",
                "url": "https://985monitor.xyz/fomo/fomo_alltime_leaderboard_real_wallets.csv",
                "row_count": 25,
                "content_length_bytes": 7054,
                "sha256": "cb4f42b92add4f0d12f026d348af072b578440a4340297a0ca369c4cf348519d",
                "source_timestamp_utc": "2026-05-03T12:06:00Z",
                "provenance_status": "incomplete",
                "field_label": "source-reported leaderboard context",
                "schema": _pnl_schema(),
            },
            {
                "filename": "fomo_smart_money_FULL_real_wallets.csv",
                "url": "https://985monitor.xyz/fomo/fomo_smart_money_FULL_real_wallets.csv",
                "row_count": 1065,
                "content_length_bytes": 253608,
                "sha256": "dfc442b58d2b7a36ef095fd72aa09c59a95e88d247da7ae0968b196c624b92da",
                "source_timestamp_utc": "2026-05-03T12:06:00Z",
                "provenance_status": "incomplete",
                "field_label": "source-reported public/social context",
                "schema": _social_schema(),
            },
        ],
        pnl_union_unique_identities=116,
        pnl_membership_distribution={
            "one_window": 72,
            "two_windows": 31,
            "three_windows": 11,
            "four_windows": 2,
        },
        pairwise_overlap={
            "24h_7d": 21,
            "24h_30d": 17,
            "24h_all_time": 5,
            "7d_30d": 22,
            "7d_all_time": 3,
            "30d_all_time": 8,
        },
        wallet_coverage={
            "pnl_union": {
                "unique_identities": 116,
                "real_solana": 115,
                "real_evm": 75,
                "both_chains": 74,
            },
            "social": {
                "unique_rows": 1065,
                "real_solana": 921,
                "real_evm": 391,
                "both_chains": 368,
                "neither_chain": 121,
            },
        },
        concentration={
            "pnl_top10_share": {
                "24h": 58.4,
                "7d": 52.9,
                "30d": 41.3,
                "all_time": 71.6,
            },
            "volume_top10_share": {
                "24h": 84.7,
                "7d": 79.4,
                "30d": 77.4,
                "all_time": 79.4,
            },
        },
        efficiency={
            "pnl_to_volume_median_pct": {
                "24h": 4.4,
                "7d": 9.7,
                "30d": 8.2,
            },
            "pnl_to_volume_p90_pct": {
                "24h": 38.6,
                "7d": 121.4,
                "30d": 726.6,
            },
        },
        social_segments={
            "followed_by_topN_at_least_5": 134,
            "followed_by_topN_at_least_10": 44,
            "social_rows_with_leaderboard_windows": 52,
            "social_rows_without_real_wallet": 121,
        },
        schema_notes=[
            "PnL leaderboards expose rank, handle/name, source PnL, volume, trades, followers, real SOL/EVM wallet coverage, old FOMO wallets, and fomo_id.",
            "Social/common-follow rows expose followed_by_topN, leaderboard_windows, wallet coverage, total volume, and fomo_id.",
            "The twitter field was blank in the inspected CSVs.",
        ],
        provenance_gaps=[
            "No row-level collection timestamp was present.",
            "No scrape code or source API contract was published with the snapshot.",
            "The method for labeling wallets as real owner-controlled wallets is not independently verified.",
            "USD valuation source and timestamp are unknown.",
            "The page claims hourly updates, but fetched headers showed the same May 3, 2026 timestamp.",
        ],
        safe_claim=(
            "985monitor published five FOMO-derived CSV snapshots with aggregate "
            "leaderboard and common-follow structure as of the May 3, 2026 snapshot."
        ),
    )


def build_fomo_playbook(summary: FomoSnapshotSummary) -> dict[str, Any]:
    """Build the complete five-play research packet."""

    plays = _build_plays(summary)
    return {
        "mode": "research_only",
        "research_only": True,
        "schema": "fomo_985monitor_playbook.v1",
        "boundary": RESEARCH_BOUNDARY,
        "source": {
            "url": summary.source_url,
            "snapshot_timestamp_utc": summary.snapshot_timestamp_utc,
            "inspected_at_utc": summary.inspected_at_utc,
            "freshness_status": summary.freshness_status,
            "provenance_status": "incomplete",
            "safe_claim": summary.safe_claim,
        },
        "dataset_summary": asdict(summary),
        "source_snapshot_contract": {
            "schema": "trading_lab_product_playbook.v0",
            "normalized_fields": [
                "topic",
                "payload",
                "metadata",
                "provenance",
                "producer",
                "sequence",
                "hash",
            ],
            "derived_fields": [
                "freshness",
                "source_timestamp",
                "license_note",
                "provenance_status",
                "content_hash",
            ],
            "privacy": "aggregate_or_pseudonymous",
        },
        "completed_plays_count": len(plays),
        "plays": [asdict(play) for play in plays],
        "global_blocked_outputs": list(GLOBAL_BLOCKED_OUTPUTS),
        "promotion_status": {
            "status": "blocked_by_incomplete_provenance",
            "promotion_ready": False,
            "reason": (
                "Point-in-time snapshot lacks row-level timing, independent wallet "
                "verification, live execution evidence, legal rights review, and "
                "forward-tested monetization proof."
            ),
        },
    }


def render_fomo_playbook_markdown(playbook: dict[str, Any]) -> str:
    """Render the playbook as a source-of-truth Markdown packet."""

    source = playbook["source"]
    summary = playbook["dataset_summary"]
    lines = [
        "# 985monitor FOMO Research Playbook",
        "",
        "## Boundary",
        "",
        playbook["boundary"],
        "",
        "This packet completes the five plays as research and commercialization "
        "artifacts. It does not launch a website, signal service, broker workflow, "
        "or public data product.",
        "",
        "## Source Snapshot",
        "",
        f"- Source URL: {source['url']}",
        f"- Snapshot timestamp: {source['snapshot_timestamp_utc']}",
        f"- Inspected at: {source['inspected_at_utc']}",
        f"- Freshness status: {source['freshness_status']}",
        f"- Provenance status: {source['provenance_status']}",
        f"- Safe claim: {source['safe_claim']}",
        f"- PnL unique identities: {summary['pnl_union_unique_identities']}",
        f"- Social rows: {summary['row_counts']['social']}",
        "",
        "## CSV Manifests",
        "",
    ]
    for manifest in summary["csv_manifests"]:
        lines.extend(
            [
                f"### {manifest['filename']}",
                "",
                f"- URL: {manifest['url']}",
                f"- Rows: {manifest['row_count']}",
                f"- Bytes: {manifest['content_length_bytes']}",
                f"- SHA256: {manifest['sha256']}",
                f"- Source timestamp: {manifest['source_timestamp_utc']}",
                f"- Provenance status: {manifest['provenance_status']}",
                f"- Field label: {manifest['field_label']}",
                f"- Schema: {', '.join(manifest['schema'])}",
                "",
            ]
        )
    lines.extend(
        [
        "## Provenance Gaps",
        "",
        ]
    )
    lines.extend(f"- {gap}" for gap in summary["provenance_gaps"])
    lines.extend(
        [
            "",
            "## Completed Plays",
            "",
        ]
    )
    for index, play in enumerate(playbook["plays"], start=1):
        lines.extend(
            [
                f"### {index}. {play['title']}",
                "",
                f"- ID: {play['id']}",
                f"- Completion artifact: {play['completion_artifact']}",
                f"- Buyer: {play['buyer']}",
                f"- Revenue mechanism: {play['revenue_mechanism']}",
                f"- Status: {play['completion_status']}",
                f"- Blocker: {play['blocker']}",
                "- Source fields or aggregates:",
                *_bullet_lines(play["source_fields_or_aggregates"]),
                "- Deliverable:",
                *_bullet_lines(play["deliverable"]),
                "- Proof gates:",
                *_bullet_lines(play["proof_gates"]),
                "- Blocked outputs:",
                *_bullet_lines(play["blocked_outputs"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Promotion Status",
            "",
            f"- Status: {playbook['promotion_status']['status']}",
            f"- Promotion ready: {playbook['promotion_status']['promotion_ready']}",
            f"- Reason: {playbook['promotion_status']['reason']}",
            "",
            "## Global Blocked Outputs",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in playbook["global_blocked_outputs"])
    lines.append("")
    return "\n".join(lines)


def _build_plays(summary: FomoSnapshotSummary) -> tuple[FomoPlay, ...]:
    shared_gates = [
        "Keep all outputs delayed or point-in-time.",
        "Use aggregate or pseudonymous cohorts by default.",
        "State provenance gaps before any monetization claim.",
        "Block promotion if users could reasonably treat the output as current trade guidance.",
    ]
    return (
        FomoPlay(
            id="paid_falsification_report",
            title="Paid KOL Wallet Falsification Report",
            completion_artifact="reports/985monitor-paid-kol-wallet-falsification-report.md",
            buyer="Research desks, founders, funds, and crypto operators who need a skeptical read on KOL wallet claims.",
            revenue_mechanism="Paid monthly report, bespoke diligence memo, or sponsor-free research subscription.",
            source_fields_or_aggregates=[
                "PnL leaderboard rank by window",
                "multi-window identity persistence",
                "top-10 PnL and volume concentration",
                "wallet coverage by chain",
                "source provenance gaps",
            ],
            deliverable=[
                "A recurring report template that asks what survived and what failed.",
                "A baseline section comparing persistent winners against one-window winners.",
                "A limitations section that leads with timestamp and provenance gaps.",
            ],
            proof_gates=[
                *shared_gates,
                "Require forward-only rank persistence tests before saying a cohort has predictive value.",
                "Require baseline and concentration controls before selling any edge narrative.",
            ],
            blocker="Cannot market as alpha until forward tests, baselines, and friction controls exist.",
            blocked_outputs=list(GLOBAL_BLOCKED_OUTPUTS),
        ),
        FomoPlay(
            id="anti_copy_wallet_quality_score",
            title="Anti-Copy Wallet Quality Score",
            completion_artifact="docs/985monitor-fomo-research-playbook.md#2-anti-copy-wallet-quality-score",
            buyer="Wallet-tool builders, Telegram bot teams, trading communities, and diligence teams.",
            revenue_mechanism="B2B score API spec, CSV score export, or diligence pack.",
            source_fields_or_aggregates=[
                "window_count per identity",
                "PnL-to-volume ratio",
                "PnL-per-trade ratio where trades exist",
                "balance-to-volume ratio",
                "SOL-only, EVM-only, both-chain, and no-real-wallet coverage flags",
                "social followed_by_topN buckets",
            ],
            deliverable=[
                "A component scorecard: persistence, concentration risk, wallet coverage, social crowding, and provenance risk.",
                "Risk labels such as evidence thin, concentration heavy, stale snapshot, and provenance blocked.",
                "An appeal/removal and rights-review note for public packaging.",
            ],
            proof_gates=[
                *shared_gates,
                "Do not score a named person; score dataset rows or pseudonymous cohorts.",
                "Require an explanation for every score component.",
            ],
            blocker="Defamation, privacy, and provenance risk if labels are attached to people rather than evidence cohorts.",
            blocked_outputs=list(GLOBAL_BLOCKED_OUTPUTS),
        ),
        FomoPlay(
            id="kol_campaign_forensics_template",
            title="KOL Campaign Forensics Template",
            completion_artifact="docs/985monitor-fomo-research-playbook.md#3-kol-campaign-forensics-template",
            buyer="Token teams, exchanges, communities, compliance-minded sponsors, and investor relations teams.",
            revenue_mechanism="Fixed-scope forensic review, pre-campaign diligence, or post-campaign audit retainer.",
            source_fields_or_aggregates=[
                "public handle/identity count as aggregate",
                "wallet coverage availability",
                "social common-follow clusters",
                "leaderboard window metadata",
                "volume concentration by cohort",
            ],
            deliverable=[
                "A campaign intake checklist that requests token, campaign window, disclosed relationships, and public source links.",
                "A forensics memo layout: evidence observed, what cannot be proven, disclosure questions, and dump-risk indicators.",
                "A no-harassment and no-deanonymization handling policy.",
            ],
            proof_gates=[
                *shared_gates,
                "Require campaign date windows and public source citations before making any campaign finding.",
                "Separate disclosure questions from misconduct conclusions.",
            ],
            blocker="Legal and reputational sensitivity if the output implies misconduct without evidence.",
            blocked_outputs=list(GLOBAL_BLOCKED_OUTPUTS),
        ),
        FomoPlay(
            id="derived_aggregate_dataset_licensing_packet",
            title="Derived Aggregate Dataset Licensing Packet",
            completion_artifact="docs/985monitor-fomo-research-playbook.md#4-derived-aggregate-dataset-licensing-packet",
            buyer="Dashboard builders, data startups, research desks, and market-intelligence vendors.",
            revenue_mechanism="Monthly derived dataset license, aggregate feed, or private research data room.",
            source_fields_or_aggregates=[
                "row counts by source file",
                "identity overlap counts",
                "wallet coverage counts",
                "top-N concentration",
                "followed_by_topN distribution buckets",
                "provenance and rights-review status",
            ],
            deliverable=[
                "A license packet for aggregate metrics only.",
                "A data dictionary that excludes raw wallet-handle mappings unless rights review approves them.",
                "A buyer-safe redaction policy and refresh cadence note.",
            ],
            proof_gates=[
                *shared_gates,
                "Complete source rights review before redistribution.",
                "Ship aggregates first; keep raw wallet maps out of commercial packages by default.",
            ],
            blocker="Redistribution rights and wallet-label provenance remain unresolved.",
            blocked_outputs=list(GLOBAL_BLOCKED_OUTPUTS),
        ),
        FomoPlay(
            id="trading_lab_hypothesis_factory",
            title="Trading Lab Hypothesis Factory",
            completion_artifact="hypotheses/985monitor-fomo-wallet-falsification.json",
            buyer="Internal Trading Lab research, workshops, and founder-facing falsification demos.",
            revenue_mechanism="Paid workshop, implementation kit, or research operating-system demo.",
            source_fields_or_aggregates=[
                "point-in-time event timing",
                "leaderboard persistence",
                "cluster convergence",
                "crowding or fade behavior",
                "category-specific skill",
                "monetization after fees, slippage, delay, and capacity limits",
            ],
            deliverable=[
                "A pre-registered hypothesis registry entry.",
                "A ranked backlog of falsification tests.",
                "A promotion gate that keeps the result not live-signal ready until forward tests pass.",
            ],
            proof_gates=[
                *shared_gates,
                "Require row-level timestamps before event-impact claims.",
                "Require fees, slippage, delay, and capacity checks before monetization claims.",
                "Reject any hypothesis whose value disappears after baseline or leakage controls.",
            ],
            blocker="Historical snapshots and executable friction data are missing.",
            blocked_outputs=list(GLOBAL_BLOCKED_OUTPUTS),
        ),
    )


def _bullet_lines(values: list[str]) -> list[str]:
    return [f"  - {value}" for value in values]


def _pnl_schema() -> list[str]:
    return [
        "rank",
        "handle",
        "name",
        "pnl_period_usd",
        "total_volume_usd",
        "trades",
        "followers",
        "real_solana",
        "real_solana_usd",
        "real_evm",
        "real_evm_usd",
        "sol_count",
        "evm_count",
        "fomo_old_solana",
        "fomo_old_evm",
        "twitter",
        "fomo_id",
    ]


def _social_schema() -> list[str]:
    return [
        "rank",
        "handle",
        "name",
        "real_solana",
        "real_solana_usd",
        "real_evm",
        "real_evm_usd",
        "total_volume_usd",
        "followed_by_topN",
        "leaderboard_windows",
        "sol_wallet_count",
        "evm_wallet_count",
        "fomo_old_solana",
        "fomo_old_evm",
        "twitter",
        "fomo_id",
    ]
