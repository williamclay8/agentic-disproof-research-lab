from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from trading_lab.live_types import LiveDataEnvelope, MarketQuote
from trading_lab.providers import FixtureProvider, KrakenTickerProvider, NullProvider


FIXTURE_PATH = Path("examples/live_fixture_quotes.jsonl")


def test_null_provider_streams_no_events() -> None:
    provider = NullProvider()

    assert list(provider.stream()) == []


def test_fixture_provider_streams_normalized_live_quote_envelopes() -> None:
    provider = FixtureProvider(FIXTURE_PATH)

    events = list(provider.stream())

    assert len(events) == 3
    assert all(isinstance(event, LiveDataEnvelope) for event in events)
    assert all(isinstance(event.observation, MarketQuote) for event in events)
    assert [event.observation.symbol for event in events] == ["AAPL", "MSFT", "AAPL"]
    assert events[0].observation.observed_at == datetime(
        2026, 1, 2, 14, 30, tzinfo=timezone.utc
    )
    assert events[0].observation.bid == 101.25
    assert events[0].observation.ask == 101.35
    assert events[0].observation.last == 101.3
    assert events[0].observation.bid_size == 500
    assert events[0].observation.ask_size == 700
    assert events[0].observation.venue == "fixture"
    assert events[0].received_at == events[0].observation.observed_at
    assert events[0].freshness_ttl == timedelta(seconds=60)
    assert events[0].provenance.provider.name == "fixture"
    assert events[0].provenance.source_ref == "examples/live_fixture_quotes.jsonl:1"
    assert events[0].provenance.raw_hash != events[0].provenance.normalized_hash


def test_fixture_provider_rejects_missing_required_quote_fields(tmp_path) -> None:
    fixture = tmp_path / "bad_quotes.jsonl"
    fixture.write_text(
        (
            '{"kind":"quote","symbol":"AAPL",'
            '"timestamp":"2026-01-02T14:30:00Z","bid":101.25}\n'
        ),
        encoding="utf-8",
    )

    provider = FixtureProvider(fixture)

    with pytest.raises(ValueError, match="line 1.*missing.*ask"):
        list(provider.stream())


def test_providers_do_not_expose_broker_or_order_methods() -> None:
    forbidden_terms = ("order", "buy", "sell", "broker", "credential", "account")

    for provider in (NullProvider(), FixtureProvider(FIXTURE_PATH)):
        public_names = [name for name in dir(provider) if not name.startswith("_")]

        assert not any(
            term in name.lower()
            for name in public_names
            for term in forbidden_terms
        )


def test_kraken_ticker_provider_normalizes_public_rest_response(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return (
                b'{"error":[],"result":{"XXBTZUSD":{"a":["65001.0","1","1"],'
                b'"b":["64999.0","1","1"],"c":["65000.0","0.1"],"v":["10","20"]}}}'
            )

    captured_urls: list[str] = []

    def fake_urlopen(request, timeout=0):
        captured_urls.append(request.full_url)
        return FakeResponse()

    monkeypatch.setattr("trading_lab.providers.urlopen", fake_urlopen)

    provider = KrakenTickerProvider(
        symbols=["BTC/USD"],
        received_at="2026-05-02T15:30:01Z",
    )
    envelopes = list(provider.stream())

    assert captured_urls == ["https://api.kraken.com/0/public/Ticker?pair=BTCUSD"]
    assert len(envelopes) == 1
    envelope = envelopes[0]
    assert envelope.symbol == "BTC/USD"
    assert envelope.data["bid"] == 64999.0
    assert envelope.data["ask"] == 65001.0
    assert envelope.data["last"] == 65000.0
    assert envelope.source == "kraken-public-rest"
    assert "Kraken public market data" in envelope.provenance.source_ref
