"""Local-only live data provider interfaces and fixture implementations."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from trading_lab.live_types import (
    LiveDataEnvelope,
    LiveProvenance,
    MarketQuote,
    ProviderIdentity,
    stable_normalized_hash,
    stable_raw_hash,
)


QUOTE_FIELDS = ("bid", "ask")


class LiveDataProvider(Protocol):
    """Provider protocol for streaming normalized local live-data envelopes."""

    name: str

    def stream(self) -> Iterator[LiveDataEnvelope]:
        """Yield normalized live-data envelopes."""


class NullProvider:
    """Provider that intentionally yields no events."""

    name = "null"

    def stream(self) -> Iterator[LiveDataEnvelope]:
        return iter(())


class FixtureProvider:
    """Stream normalized quote events from a local JSONL fixture."""

    def __init__(
        self,
        path: str | Path,
        *,
        source: str = "fixture",
        freshness_ttl: timedelta = timedelta(seconds=60),
        delayed_after: timedelta = timedelta(0),
    ) -> None:
        self.path = Path(path)
        self.source = source
        self.name = source
        self.freshness_ttl = freshness_ttl
        self.delayed_after = delayed_after

    def stream(self) -> Iterator[LiveDataEnvelope]:
        with self.path.open(encoding="utf-8") as fixture:
            for line_number, line in enumerate(fixture, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                yield self._envelope_from_line(stripped, line_number)

    def _envelope_from_line(self, line: str, line_number: int) -> LiveDataEnvelope:
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_number}: invalid JSON") from exc

        if not isinstance(raw, dict):
            raise ValueError(f"line {line_number}: quote event must be a JSON object")

        kind = str(raw.get("kind", raw.get("type", ""))).strip().lower()
        if kind != "quote":
            raise ValueError(f"line {line_number}: unsupported event kind {kind!r}")

        symbol = str(raw.get("symbol", "")).strip().upper()
        if not symbol:
            raise ValueError(f"line {line_number}: symbol must be non-empty")

        observed_at = _parse_timestamp(raw.get("timestamp"), "timestamp", line_number)
        received_at = _parse_timestamp(
            raw.get("received_at", raw.get("timestamp")),
            "received_at",
            line_number,
        )

        missing = [field for field in QUOTE_FIELDS if field not in raw]
        if missing:
            raise ValueError(f"line {line_number}: missing quote field {missing[0]!r}")

        payload = {
            "bid": _as_float(raw["bid"], "bid", line_number),
            "ask": _as_float(raw["ask"], "ask", line_number),
            "last": _as_optional_float(raw.get("last"), "last", line_number),
            "bid_size": _as_optional_float(
                raw.get("bid_size"), "bid_size", line_number
            ),
            "ask_size": _as_optional_float(
                raw.get("ask_size"), "ask_size", line_number
            ),
            "venue": _as_optional_text(raw.get("venue")),
        }
        quote = MarketQuote(
            symbol=symbol,
            observed_at=observed_at,
            **payload,
        )
        return LiveDataEnvelope(
            observation=quote,
            received_at=received_at,
            provenance=LiveProvenance(
                provider=ProviderIdentity(name=self.source, dataset=str(self.path)),
                raw_hash=stable_raw_hash(raw),
                normalized_hash=stable_normalized_hash(quote),
                source_ref=f"{self.path}:{line_number}",
            ),
            freshness_ttl=self.freshness_ttl,
            delayed_after=self.delayed_after,
        )


class KrakenTickerProvider:
    """Read-only public Kraken ticker observation provider.

    This adapter fetches public market data only. It does not authenticate,
    collect credentials, expose accounts, or support execution.
    """

    name = "kraken-public-rest"
    endpoint = "https://api.kraken.com/0/public/Ticker"

    def __init__(
        self,
        symbols: list[str],
        *,
        received_at: str | None = None,
        freshness_ttl: timedelta = timedelta(seconds=30),
    ) -> None:
        self.symbols = [symbol.upper() for symbol in symbols]
        self.received_at = _parse_timestamp(
            received_at,
            "received_at",
            0,
        ) if received_at else None
        self.freshness_ttl = freshness_ttl

    def stream(self) -> Iterator[LiveDataEnvelope]:
        for symbol in self.symbols:
            raw = self._fetch(symbol)
            yield self._envelope_from_response(symbol, raw)

    def _fetch(self, symbol: str) -> dict:
        pair = _kraken_pair(symbol)
        url = f"{self.endpoint}?{urlencode({'pair': pair})}"
        request = Request(url, headers={"User-Agent": "trading-lab research data"})
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        errors = payload.get("error") or []
        if errors:
            raise ValueError(f"Kraken ticker error: {errors}")
        return payload

    def _envelope_from_response(self, symbol: str, raw: dict) -> LiveDataEnvelope:
        result = raw.get("result") or {}
        if not result:
            raise ValueError("Kraken ticker response missing result")
        quote_payload = next(iter(result.values()))
        received_at = self.received_at or datetime.now().astimezone()
        quote = MarketQuote(
            symbol=symbol,
            observed_at=received_at,
            bid=float(quote_payload["b"][0]),
            ask=float(quote_payload["a"][0]),
            last=float(quote_payload["c"][0]),
            venue="Kraken",
        )
        return LiveDataEnvelope(
            observation=quote,
            received_at=received_at,
            provenance=LiveProvenance(
                provider=ProviderIdentity(name=self.name, dataset="public-ticker"),
                raw_hash=stable_raw_hash(raw),
                normalized_hash=stable_normalized_hash(quote),
                source_ref="Kraken public market data REST ticker",
            ),
            freshness_ttl=self.freshness_ttl,
        )


def _as_float(value: object, field: str, line_number: int) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"line {line_number}: {field} must be numeric") from exc


def _as_optional_float(value: object, field: str, line_number: int) -> float | None:
    if value is None:
        return None
    return _as_float(value, field, line_number)


def _as_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_timestamp(value: object, field: str, line_number: int) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"line {line_number}: {field} must be non-empty")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"line {line_number}: {field} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"line {line_number}: {field} must be timezone-aware")
    return parsed


def _kraken_pair(symbol: str) -> str:
    normalized = symbol.upper().replace("/", "")
    aliases = {
        "BTCUSD": "BTCUSD",
        "XBTUSD": "XBTUSD",
        "ETHUSD": "ETHUSD",
    }
    return aliases.get(normalized, normalized)
