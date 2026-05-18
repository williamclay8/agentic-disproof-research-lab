"""Research-only hypothesis factory for the 985monitor/FOMO packet."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from trading_lab.fomo_plays import (
    GLOBAL_BLOCKED_OUTPUTS,
    RESEARCH_BOUNDARY,
    FomoSnapshotSummary,
)


@dataclass(frozen=True)
class CandidateEdge:
    id: str
    title: str
    verdict: str
    score: int
    evidence_hook: str
    aggregate_support: dict[str, Any]
    hypothesis: str
    null_hypothesis: str
    required_next_data: list[str]
    baseline: list[str]
    falsification_criteria: list[str]
    failure_modes: list[str]
    next_safe_research_action: str
    promotion_blockers: list[str]
    blocked_outputs: list[str]
    research_only: bool = True


def build_fomo_hypothesis_factory(summary: FomoSnapshotSummary) -> dict[str, Any]:
    """Rank candidate edge hypotheses without validating any trading edge."""

    candidates = sorted(
        _candidate_edges(summary),
        key=lambda candidate: candidate.score,
        reverse=True,
    )
    best = candidates[0]
    return {
        "schema": "fomo_hypothesis_factory.v1",
        "schema_version": 1,
        "mode": "research_only",
        "research_only": True,
        "boundary": RESEARCH_BOUNDARY,
        "source": {
            "url": summary.source_url,
            "snapshot_timestamp_utc": summary.snapshot_timestamp_utc,
            "inspected_at_utc": summary.inspected_at_utc,
            "freshness_status": summary.freshness_status,
            "provenance_status": "incomplete",
            "rights_review_status": "not_reviewed",
        },
        "edge_status": "candidate_edge_found_not_validated",
        "validated_edge_found": False,
        "best_candidate_edge_id": best.id,
        "best_candidate_summary": (
            "The strongest candidate is multi-window PnL persistence: identities "
            "that recur across source-reported leaderboard windows may be a less "
            "fragile cohort than one-window leaderboard rows. This is not a "
            "validated trading edge because the snapshot lacks row-level timing, "
            "forward outcomes, baselines, and friction evidence."
        ),
        "candidate_edges": [asdict(candidate) for candidate in candidates],
        "review_status": {
            "baseline_results": "missing",
            "walk_forward_results": "missing",
            "cost_slippage_latency_capacity": "missing",
            "leakage_review": "missing",
            "concentration_stress": "candidate_only",
            "forward_test_status": "missing",
            "rights_review_status": "not_reviewed",
            "human_review_status": "not_reviewed",
        },
        "promotion_status": {
            "status": "not_live_signal_ready",
            "promotion_ready": False,
            "reason": (
                "Candidate edges are hypothesis seeds only. No candidate has "
                "passed point-in-time lineage, baseline, leakage, cost, slippage, "
                "latency, capacity, rights, or human-review gates."
            ),
        },
        "global_blocked_outputs": list(GLOBAL_BLOCKED_OUTPUTS),
    }


def render_fomo_hypothesis_factory_markdown(factory: dict[str, Any]) -> str:
    """Render the hypothesis factory packet as a reviewable report."""

    source = factory["source"]
    lines = [
        "# 985monitor FOMO Hypothesis Factory",
        "",
        "## Boundary",
        "",
        factory["boundary"],
        "",
        "No validated trading edge was found. The factory found ranked candidate "
        "edge hypotheses for offline falsification only.",
        "",
        "## Source",
        "",
        f"- URL: {source['url']}",
        f"- Snapshot timestamp: {source['snapshot_timestamp_utc']}",
        f"- Freshness status: {source['freshness_status']}",
        f"- Provenance status: {source['provenance_status']}",
        "",
        "## Edge Verdict",
        "",
        f"- Edge status: `{factory['edge_status']}`",
        f"- Validated edge found: `{factory['validated_edge_found']}`",
        f"- Best candidate edge: `{factory['best_candidate_edge_id']}`",
        f"- Summary: {factory['best_candidate_summary']}",
        "",
        "## Candidate Edges",
        "",
    ]
    for index, edge in enumerate(factory["candidate_edges"], start=1):
        lines.extend(
            [
                f"### {index}. {edge['title']}",
                "",
                f"- ID: `{edge['id']}`",
                f"- Verdict: `{edge['verdict']}`",
                f"- Score: `{edge['score']}`",
                f"- Evidence hook: {edge['evidence_hook']}",
                f"- Hypothesis: {edge['hypothesis']}",
                f"- Null hypothesis: {edge['null_hypothesis']}",
                "- Aggregate support:",
                *_dict_lines(edge["aggregate_support"]),
                "- Required next data:",
                *_bullet_lines(edge["required_next_data"]),
                "- Baselines:",
                *_bullet_lines(edge["baseline"]),
                "- Falsification criteria:",
                *_bullet_lines(edge["falsification_criteria"]),
                "- Why it might fail:",
                *_bullet_lines(edge["failure_modes"]),
                "- Promotion blockers:",
                *_bullet_lines(edge["promotion_blockers"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Promotion Status",
            "",
            f"- Status: `{factory['promotion_status']['status']}`",
            f"- Promotion ready: `{factory['promotion_status']['promotion_ready']}`",
            f"- Reason: {factory['promotion_status']['reason']}",
            "",
            "## Blocked Outputs",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in factory["global_blocked_outputs"])
    lines.append("")
    return "\n".join(lines)


def _candidate_edges(summary: FomoSnapshotSummary) -> tuple[CandidateEdge, ...]:
    repeated = (
        summary.pnl_membership_distribution["two_windows"]
        + summary.pnl_membership_distribution["three_windows"]
        + summary.pnl_membership_distribution["four_windows"]
    )
    durable = (
        summary.pnl_membership_distribution["three_windows"]
        + summary.pnl_membership_distribution["four_windows"]
    )
    return (
        CandidateEdge(
            id="pnl_window_persistence",
            title="Multi-Window PnL Persistence Candidate",
            verdict="candidate_edge_unvalidated",
            score=88,
            evidence_hook=(
                "44 of 116 PnL identities appear in at least two leaderboard "
                "windows, and 13 appear in at least three windows."
            ),
            aggregate_support={
                "unique_pnl_identities": summary.pnl_union_unique_identities,
                "appears_in_two_or_more_windows": repeated,
                "appears_in_three_or_more_windows": durable,
                "four_window_identities": summary.pnl_membership_distribution[
                    "four_windows"
                ],
                "largest_pairwise_overlap": max(summary.pairwise_overlap.values()),
            },
            hypothesis=(
                "Multi-window leaderboard recurrence may identify a cohort that "
                "is less fragile than one-window source-reported winners."
            ),
            null_hypothesis=(
                "Recurring leaderboard membership has no forward value after "
                "survivorship, concentration, and baseline controls."
            ),
            required_next_data=[
                "historical leaderboard snapshots with inclusion timestamps",
                "forward wallet outcomes after inclusion",
                "active-wallet universe for random and volume-weighted controls",
                "fees, slippage, latency, spread, and capacity assumptions",
            ],
            baseline=[
                "random active-wallet cohort",
                "volume-weighted active-wallet cohort",
                "one-window-only leaderboard cohort",
            ],
            falsification_criteria=[
                "Reject if recurring cohorts do not beat one-window and random baselines in forward-only windows.",
                "Reject if edge disappears after removing top-10 concentrated identities.",
                "Reject if returns are positive only before costs, latency, slippage, or capacity limits.",
            ],
            failure_modes=[
                "source-reported PnL may be backward-looking survivorship bias",
                "a small head cohort may dominate the apparent pattern",
                "wallet labels may not represent controlled current wallets",
            ],
            next_safe_research_action="Research: archive historical snapshots and run forward-only recurrence tests against random and volume-weighted baselines.",
            promotion_blockers=_promotion_blockers(),
            blocked_outputs=list(GLOBAL_BLOCKED_OUTPUTS),
        ),
        CandidateEdge(
            id="concentration_fade",
            title="Leaderboard Concentration Fade Candidate",
            verdict="candidate_edge_unvalidated",
            score=76,
            evidence_hook=(
                "Top-10 concentration is high across PnL and volume windows, "
                "suggesting crowding or head-cohort fragility may be testable."
            ),
            aggregate_support={
                "pnl_top10_share": summary.concentration["pnl_top10_share"],
                "volume_top10_share": summary.concentration["volume_top10_share"],
            },
            hypothesis=(
                "Highly concentrated leaderboard windows may be more fragile than "
                "diversified cohorts in forward tests."
            ),
            null_hypothesis=(
                "Top-heavy concentration has no independent relationship with "
                "future cohort decay after activity and volume controls."
            ),
            required_next_data=[
                "forward outcomes by leaderboard window",
                "cohort concentration over time",
                "liquidity and spread context",
            ],
            baseline=[
                "same-window low-concentration cohorts",
                "volume-matched non-leaderboard cohorts",
                "market beta or token-sector movement",
            ],
            falsification_criteria=[
                "Reject if top-heavy cohorts do not decay faster than matched cohorts.",
                "Reject if concentration adds no explanatory value beyond volume.",
            ],
            failure_modes=[
                "concentration may reflect genuine skill or capital rather than fragility",
                "forward sample may be too small",
                "token-level regime effects may dominate wallet effects",
            ],
            next_safe_research_action="Research: run leave-top-10-out and matched low-concentration cohort tests.",
            promotion_blockers=_promotion_blockers(),
            blocked_outputs=list(GLOBAL_BLOCKED_OUTPUTS),
        ),
        CandidateEdge(
            id="efficiency_adjusted_leaderboard",
            title="Efficiency-Adjusted Leaderboard Candidate",
            verdict="candidate_edge_unvalidated",
            score=72,
            evidence_hook=(
                "Source-reported PnL divided by volume is highly dispersed, "
                "creating a testable normalized cohort distinct from gross PnL rank."
            ),
            aggregate_support={
                "pnl_to_volume_median_pct": summary.efficiency[
                    "pnl_to_volume_median_pct"
                ],
                "pnl_to_volume_p90_pct": summary.efficiency[
                    "pnl_to_volume_p90_pct"
                ],
            },
            hypothesis=(
                "Efficiency-adjusted leaderboard rows may identify different "
                "research cohorts than gross PnL or raw volume rank."
            ),
            null_hypothesis=(
                "PnL-to-volume efficiency has no forward value after trade count, "
                "liquidity, costs, and outlier controls."
            ),
            required_next_data=[
                "trade-level timing and token exposure",
                "forward outcomes after inclusion",
                "liquidity, spread, and minimum-volume filters",
                "trade count controls",
            ],
            baseline=[
                "raw PnL rank",
                "raw volume rank",
                "volume-matched leaderboard cohorts",
                "minimum-volume-filtered random active wallets",
            ],
            falsification_criteria=[
                "Reject if efficiency is driven by tiny-volume outliers.",
                "Reject if efficiency-adjusted cohorts do not beat raw-rank baselines forward-only.",
                "Reject if edge disappears after liquidity, trade count, cost, and slippage filters.",
            ],
            failure_modes=[
                "small denominators can inflate PnL-to-volume ratios",
                "source-reported PnL may include stale or backward-looking outcomes",
                "liquidity constraints may make apparent efficiency non-monetizable",
            ],
            next_safe_research_action="Research: apply minimum-volume and trade-count filters, then compare forward outcomes against raw PnL and volume ranks.",
            promotion_blockers=_promotion_blockers(),
            blocked_outputs=list(GLOBAL_BLOCKED_OUTPUTS),
        ),
        CandidateEdge(
            id="social_consensus_filter",
            title="Common-Follow Social Consensus Candidate",
            verdict="candidate_edge_unvalidated",
            score=69,
            evidence_hook=(
                "The social sheet has 44 rows followed by at least 10 top accounts, "
                "creating an aggregate social-context bucket to test."
            ),
            aggregate_support={
                "social_rows": summary.row_counts["social"],
                "followed_by_topN_at_least_5": summary.social_segments[
                    "followed_by_topN_at_least_5"
                ],
                "followed_by_topN_at_least_10": summary.social_segments[
                    "followed_by_topN_at_least_10"
                ],
                "social_rows_without_real_wallet": summary.social_segments[
                    "social_rows_without_real_wallet"
                ],
            },
            hypothesis=(
                "High common-follow buckets may help prioritize which KOL-wallet "
                "claims deserve diligence before lower-consensus rows."
            ),
            null_hypothesis=(
                "Common-follow count adds no value beyond simple activity, volume, "
                "or leaderboard-window metadata."
            ),
            required_next_data=[
                "historical common-follow snapshots",
                "activity and volume controls",
                "forward outcomes and source refresh history",
            ],
            baseline=[
                "random social rows",
                "volume-matched social rows",
                "leaderboard-window-only rows",
            ],
            falsification_criteria=[
                "Reject if common-follow buckets do not improve forward diligence hit-rate over controls.",
                "Reject if signal vanishes when rows without verified wallet coverage are excluded.",
            ],
            failure_modes=[
                "common-follow may measure popularity rather than trading value",
                "social context may be stale or incomplete",
                "using social fields can drift into targeting or identity claims",
            ],
            next_safe_research_action="Research: test common-follow buckets against activity and volume controls using only aggregate cohorts.",
            promotion_blockers=_promotion_blockers(),
            blocked_outputs=list(GLOBAL_BLOCKED_OUTPUTS),
        ),
        CandidateEdge(
            id="cross_chain_coverage_filter",
            title="Cross-Chain Wallet Coverage Candidate",
            verdict="candidate_edge_unvalidated",
            score=61,
            evidence_hook=(
                "74 of 116 PnL identities have both SOL and EVM coverage, making "
                "wallet coverage a possible quality-control filter."
            ),
            aggregate_support={
                "pnl_union_wallet_coverage": summary.wallet_coverage["pnl_union"],
                "social_wallet_coverage": summary.wallet_coverage["social"],
            },
            hypothesis=(
                "Rows with broader source-reported wallet coverage may produce "
                "more auditable research cohorts than rows with sparse coverage."
            ),
            null_hypothesis=(
                "Chain coverage does not improve auditability or forward evidence "
                "quality after activity controls."
            ),
            required_next_data=[
                "wallet-linkage provenance",
                "chain-specific activity history",
                "coverage completeness by refresh",
            ],
            baseline=[
                "SOL-only rows",
                "EVM-only rows",
                "rows with no real-wallet field",
            ],
            falsification_criteria=[
                "Reject if both-chain rows do not produce cleaner lineage or better forward evidence coverage.",
                "Reject if wallet coverage is an artifact of source labeling rather than verifiable activity.",
            ],
            failure_modes=[
                "more coverage may simply mean more source enrichment, not more edge",
                "wallet ownership may be incorrectly inferred",
            ],
            next_safe_research_action="Research: verify wallet-linkage provenance and compare auditability across coverage buckets.",
            promotion_blockers=_promotion_blockers(),
            blocked_outputs=list(GLOBAL_BLOCKED_OUTPUTS),
        ),
        CandidateEdge(
            id="freshness_arbitrage_rejected",
            title="Freshness Arbitrage Candidate",
            verdict="candidate_edge_unvalidated",
            score=34,
            evidence_hook=(
                "The inspected snapshot was stale despite an hourly-update claim, "
                "so freshness itself is a research risk and possible data-product gap."
            ),
            aggregate_support={
                "freshness_status": summary.freshness_status,
                "snapshot_timestamp_utc": summary.snapshot_timestamp_utc,
                "inspected_at_utc": summary.inspected_at_utc,
            },
            hypothesis=(
                "A reliable point-in-time archive could have monetizable research "
                "value because stale public snapshots are not enough."
            ),
            null_hypothesis=(
                "Freshness capture adds no actionable research value after rights, "
                "provenance, and refresh costs."
            ),
            required_next_data=[
                "scheduled refresh archive",
                "source availability logs",
                "change detection and content hashes",
            ],
            baseline=[
                "manual snapshot checks",
                "static public page",
                "random refresh cadence",
            ],
            falsification_criteria=[
                "Reject if archived refreshes rarely change or cannot be licensed.",
                "Reject if refresh latency is too high for even delayed research workflows.",
            ],
            failure_modes=[
                "source may not update reliably",
                "rights review may block redistribution",
                "freshness is operational value, not a trading edge",
            ],
            next_safe_research_action="Research: build a timestamped archive and measure whether refreshes change enough to justify a data product.",
            promotion_blockers=_promotion_blockers(),
            blocked_outputs=list(GLOBAL_BLOCKED_OUTPUTS),
        ),
    )


def _promotion_blockers() -> list[str]:
    return [
        "incomplete provenance",
        "stale point-in-time snapshot",
        "no row-level source timestamp",
        "no forward-only outcome test",
        "no baseline challenge",
        "no fee/slippage/latency/capacity model",
        "no rights review",
        "no human review",
    ]


def _bullet_lines(values: list[str]) -> list[str]:
    return [f"  - {value}" for value in values]


def _dict_lines(values: dict[str, Any]) -> list[str]:
    return [f"  - {key}: `{value}`" for key, value in values.items()]
