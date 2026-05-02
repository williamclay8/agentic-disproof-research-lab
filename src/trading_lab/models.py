"""Typed research artifacts for offline trading hypothesis falsification."""

from dataclasses import dataclass, field
from typing import Any, Literal


def _require_non_empty_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


def _require_non_empty_sequence(value: list[Any], field_name: str) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field_name} must be non-empty")


@dataclass(frozen=True)
class Hypothesis:
    id: str
    thesis: str
    null_hypothesis: str
    asset_universe: list[str]
    time_horizon: str
    signal_definition: str
    expected_failure_modes: list[str] = field(default_factory=list)
    falsification_tests: list[str] = field(default_factory=list)
    pre_registered_metrics: list[str] = field(default_factory=list)
    acceptance_thresholds: dict[str, Any] = field(default_factory=dict)
    data_requirements: list[str] = field(default_factory=list)
    posthoc_edit_policy: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "id",
            "thesis",
            "null_hypothesis",
            "time_horizon",
            "signal_definition",
        ):
            _require_non_empty_text(getattr(self, field_name), field_name)
        _require_non_empty_sequence(self.asset_universe, "asset_universe")


@dataclass(frozen=True)
class DatasetManifest:
    source: str
    symbols: list[str]
    start_date: str
    end_date: str
    columns: list[str]
    content_hash: str
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_non_empty_sequence(self.symbols, "symbols")
        _require_non_empty_text(self.content_hash, "content_hash")


@dataclass(frozen=True)
class BacktestSpec:
    hypothesis_id: str
    dataset_hash: str
    short_window: int
    long_window: int
    transaction_cost_bps: float
    slippage_bps: float
    execution_delay_bars: int

    def __post_init__(self) -> None:
        if self.short_window <= 0:
            raise ValueError("short_window must be positive")
        if self.long_window <= 0:
            raise ValueError("long_window must be positive")
        if self.long_window <= self.short_window:
            raise ValueError("long_window must be greater than short_window")
        if self.transaction_cost_bps < 0:
            raise ValueError("transaction_cost_bps must be non-negative")
        if self.slippage_bps < 0:
            raise ValueError("slippage_bps must be non-negative")
        if self.execution_delay_bars < 1:
            raise ValueError("execution_delay_bars must be at least 1")


@dataclass(frozen=True)
class BacktestResult:
    metrics: dict[str, Any]
    trades: list[dict[str, Any]]
    returns: list[float]
    positions: list[Any]
    warnings: list[str]
    fingerprint: str


GateStatus = Literal["pass", "fail", "warn"]
GateSeverity = Literal["critical", "warning", "info"]
ReportVerdict = Literal["rejected", "inconclusive", "passed preliminary gates"]


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    status: GateStatus
    evidence: dict[str, Any]
    threshold: str
    remediation_hint: str
    severity: GateSeverity

    def __post_init__(self) -> None:
        if self.status not in ("pass", "fail", "warn"):
            raise ValueError("status must be one of: pass, fail, warn")
        if self.severity not in ("critical", "warning", "info"):
            raise ValueError("severity must be one of: critical, warning, info")


@dataclass(frozen=True)
class ResearchReport:
    verdict: ReportVerdict
    summary: str
    gate_results: list[GateResult]
    metrics: dict[str, Any]
    limitations: list[str]
    next_tests: list[str]

    def __post_init__(self) -> None:
        if self.verdict not in (
            "rejected",
            "inconclusive",
            "passed preliminary gates",
        ):
            raise ValueError(
                "verdict must be one of: rejected, inconclusive, "
                "passed preliminary gates"
            )
