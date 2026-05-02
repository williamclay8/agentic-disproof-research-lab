"""Research-only live market observation types."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from hashlib import sha256
import json
from typing import Any, ClassVar, Mapping, Optional, Union


__all__ = [
    "LiveDataEnvelope",
    "LiveDataKind",
    "LiveProvenance",
    "MarketBar",
    "MarketQuote",
    "ProviderIdentity",
    "ProviderStatus",
    "stable_normalized_hash",
    "stable_raw_hash",
]


Observation = Union["MarketQuote", "MarketBar"]


class LiveDataKind(str, Enum):
    QUOTE = "quote"
    BAR = "bar"
    STATUS = "status"


def stable_raw_hash(payload: Any) -> str:
    """Return a deterministic digest for source payload capture."""
    return _stable_hash("raw", payload)


def stable_normalized_hash(payload: Any) -> str:
    """Return a deterministic digest for normalized observation payloads."""
    return _stable_hash("normalized", payload)


def _stable_hash(namespace: str, payload: Any) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(namespace.encode("utf-8") + b":" + encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    return value


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")


def _require_aware_datetime(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")


def _require_non_negative(value: Optional[float], field: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field} must be non-negative")


@dataclass(frozen=True)
class ProviderIdentity:
    name: str
    dataset: Optional[str] = None
    region: Optional[str] = None

    def __post_init__(self) -> None:
        _require_text(self.name, "name")


@dataclass(frozen=True)
class ProviderStatus:
    provider: ProviderIdentity
    checked_at: datetime
    state: str
    message: Optional[str] = None
    lag: timedelta = timedelta(0)

    VALID_STATES: ClassVar[frozenset[str]] = frozenset({"available", "degraded", "unavailable"})

    def __post_init__(self) -> None:
        _require_aware_datetime(self.checked_at, "checked_at")
        if self.state not in self.VALID_STATES:
            raise ValueError(f"state must be one of {sorted(self.VALID_STATES)}")
        if self.lag < timedelta(0):
            raise ValueError("lag must be non-negative")

    @property
    def is_available(self) -> bool:
        return self.state == "available"


@dataclass(frozen=True)
class MarketQuote:
    symbol: str
    observed_at: datetime
    bid: float
    ask: float
    last: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    venue: Optional[str] = None

    def __post_init__(self) -> None:
        _require_text(self.symbol, "symbol")
        _require_aware_datetime(self.observed_at, "observed_at")
        _require_non_negative(self.bid, "bid")
        _require_non_negative(self.ask, "ask")
        _require_non_negative(self.last, "last")
        _require_non_negative(self.bid_size, "bid_size")
        _require_non_negative(self.ask_size, "ask_size")
        if self.ask < self.bid:
            raise ValueError("ask must be greater than or equal to bid")

    @property
    def midpoint(self) -> float:
        return (self.bid + self.ask) / 2


@dataclass(frozen=True)
class MarketBar:
    symbol: str
    start_at: datetime
    end_at: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    interval: str
    venue: Optional[str] = None

    def __post_init__(self) -> None:
        _require_text(self.symbol, "symbol")
        _require_text(self.interval, "interval")
        _require_aware_datetime(self.start_at, "start_at")
        _require_aware_datetime(self.end_at, "end_at")
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        for field in ("open", "high", "low", "close", "volume"):
            _require_non_negative(getattr(self, field), field)
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be greater than or equal to open, close, and low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be less than or equal to open, close, and high")

    @property
    def observed_at(self) -> datetime:
        return self.end_at


@dataclass(frozen=True)
class LiveProvenance:
    provider: ProviderIdentity
    raw_hash: str
    normalized_hash: str
    source_ref: Optional[str] = None

    def __post_init__(self) -> None:
        _require_text(self.raw_hash, "raw_hash")
        _require_text(self.normalized_hash, "normalized_hash")


@dataclass(frozen=True)
class LiveDataEnvelope:
    observation: Optional[Observation] = None
    received_at: Optional[datetime] = None
    provenance: Optional[LiveProvenance] = None
    freshness_ttl: timedelta = timedelta(seconds=1)
    delayed_after: timedelta = timedelta(0)
    kind: Optional[LiveDataKind] = None
    symbol: Optional[str] = None
    timestamp: Optional[str] = None
    source: Optional[str] = None
    payload: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if self.freshness_ttl <= timedelta(0):
            raise ValueError("freshness_ttl must be positive")
        if self.delayed_after < timedelta(0):
            raise ValueError("delayed_after must be non-negative")
        if self.delayed_after > self.freshness_ttl:
            raise ValueError("delayed_after must not exceed freshness_ttl")
        if self.observation is not None:
            if self.received_at is None:
                raise ValueError("received_at is required")
            if self.provenance is None:
                raise ValueError("provenance is required")
            _require_aware_datetime(self.received_at, "received_at")
            _require_aware_datetime(self.observation.observed_at, "observation.observed_at")
            object.__setattr__(self, "kind", self.kind or _kind_for_observation(self.observation))
            object.__setattr__(self, "symbol", self.symbol or self.observation.symbol)
            object.__setattr__(
                self,
                "timestamp",
                self.timestamp or self.observation.observed_at.isoformat().replace("+00:00", "Z"),
            )
            object.__setattr__(self, "source", self.source or self.provenance.provider.name)
            object.__setattr__(self, "payload", self.payload or _payload_for_observation(self.observation))
            return

        if self.kind is None:
            raise ValueError("kind is required")
        if not isinstance(self.kind, LiveDataKind):
            object.__setattr__(self, "kind", LiveDataKind(self.kind))
        _require_text(self.symbol or "", "symbol")
        _require_text(self.timestamp or "", "timestamp")
        _require_text(self.source or "", "source")
        if self.payload is None:
            raise ValueError("payload is required")

    @property
    def observation_delay(self) -> timedelta:
        if self.observation is None or self.received_at is None:
            raise ValueError("observation_delay requires observation and received_at")
        return self.received_at - self.observation.observed_at

    def freshness_at(self, now: datetime) -> str:
        if self.received_at is None:
            raise ValueError("freshness_at requires received_at")
        _require_aware_datetime(now, "now")
        age = now - self.received_at
        if age > self.freshness_ttl:
            return "stale"
        if age > self.delayed_after:
            return "delayed"
        return "fresh"

    @property
    def channel(self) -> str:
        return f"market:{self.kind.value}:{self.symbol}"

    @property
    def data(self) -> Mapping[str, Any]:
        if self.payload is None:
            raise ValueError("payload is required")
        return self.payload


def _kind_for_observation(observation: Observation) -> LiveDataKind:
    if isinstance(observation, MarketQuote):
        return LiveDataKind.QUOTE
    return LiveDataKind.BAR


def _payload_for_observation(observation: Observation) -> Mapping[str, Any]:
    return _json_ready(observation)
