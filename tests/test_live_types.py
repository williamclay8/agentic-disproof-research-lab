from datetime import datetime, timedelta, timezone

import pytest

from trading_lab.live_types import (
    LiveDataEnvelope,
    LiveProvenance,
    MarketBar,
    MarketQuote,
    ProviderIdentity,
    ProviderStatus,
    stable_normalized_hash,
    stable_raw_hash,
)


def test_market_quote_requires_observation_fields() -> None:
    observed_at = datetime(2026, 5, 2, 14, 30, tzinfo=timezone.utc)

    quote = MarketQuote(
        symbol="AAPL",
        observed_at=observed_at,
        bid=101.20,
        ask=101.25,
        last=101.23,
        bid_size=200,
        ask_size=300,
        venue="IEX",
    )

    assert quote.symbol == "AAPL"
    assert quote.observed_at == observed_at
    assert quote.midpoint == 101.225


def test_market_quote_rejects_invalid_required_fields() -> None:
    observed_at = datetime(2026, 5, 2, 14, 30, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="symbol"):
        MarketQuote(symbol="", observed_at=observed_at, bid=1, ask=2)

    with pytest.raises(ValueError, match="observed_at"):
        MarketQuote(symbol="AAPL", observed_at=datetime(2026, 5, 2, 14, 30), bid=1, ask=2)

    with pytest.raises(ValueError, match="ask"):
        MarketQuote(symbol="AAPL", observed_at=observed_at, bid=2, ask=1)


def test_market_bar_requires_valid_ohlcv_window() -> None:
    start = datetime(2026, 5, 2, 14, 30, tzinfo=timezone.utc)
    end = start + timedelta(minutes=1)

    bar = MarketBar(
        symbol="MSFT",
        start_at=start,
        end_at=end,
        open=200.0,
        high=202.0,
        low=199.5,
        close=201.25,
        volume=1200,
        interval="1m",
    )

    assert bar.symbol == "MSFT"
    assert bar.observed_at == end

    with pytest.raises(ValueError, match="high"):
        MarketBar(
            symbol="MSFT",
            start_at=start,
            end_at=end,
            open=200.0,
            high=199.0,
            low=199.5,
            close=201.25,
            volume=1200,
            interval="1m",
        )


def test_envelope_reports_fresh_delayed_and_stale_observations() -> None:
    observed_at = datetime(2026, 5, 2, 14, 30, tzinfo=timezone.utc)
    received_at = observed_at + timedelta(seconds=2)
    quote = MarketQuote(symbol="AAPL", observed_at=observed_at, bid=101.20, ask=101.25)
    provider = ProviderIdentity(name="sandbox-feed", dataset="iex-tops")
    provenance = LiveProvenance(provider=provider, raw_hash="raw", normalized_hash="norm")

    envelope = LiveDataEnvelope(
        observation=quote,
        received_at=received_at,
        provenance=provenance,
        freshness_ttl=timedelta(seconds=10),
        delayed_after=timedelta(seconds=5),
    )

    assert envelope.observation_delay == timedelta(seconds=2)
    assert envelope.freshness_at(received_at + timedelta(seconds=4)) == "fresh"
    assert envelope.freshness_at(received_at + timedelta(seconds=6)) == "delayed"
    assert envelope.freshness_at(received_at + timedelta(seconds=11)) == "stale"


def test_provider_status_exposes_research_only_health_not_execution_state() -> None:
    checked_at = datetime(2026, 5, 2, 14, 30, tzinfo=timezone.utc)
    status = ProviderStatus(
        provider=ProviderIdentity(name="sandbox-feed"),
        checked_at=checked_at,
        state="degraded",
        message="snapshot lagging",
        lag=timedelta(seconds=12),
    )

    assert status.state == "degraded"
    assert status.is_available is False

    with pytest.raises(ValueError, match="state"):
        ProviderStatus(provider=ProviderIdentity(name="sandbox-feed"), checked_at=checked_at, state="filled")


def test_hash_helpers_are_stable_and_distinguish_raw_from_normalized_payloads() -> None:
    left = {"symbol": "AAPL", "bid": 101.2, "nested": {"ask": 101.25, "venue": "IEX"}}
    right = {"nested": {"venue": "IEX", "ask": 101.25}, "bid": 101.2, "symbol": "AAPL"}

    assert stable_raw_hash(left) == stable_raw_hash(right)
    assert stable_normalized_hash(left) == stable_normalized_hash(right)
    assert stable_raw_hash(left) != stable_normalized_hash(left)


def test_live_types_use_safety_terminology_only() -> None:
    exported = set(LiveDataEnvelope.__module__.split(".")) | set(
        __import__("trading_lab.live_types", fromlist=["__all__"]).__all__
    )
    forbidden_fragments = {"broker", "account", "order", "trade", "recommendation"}

    assert not any(
        fragment in exported_name.lower()
        for exported_name in exported
        for fragment in forbidden_fragments
    )
