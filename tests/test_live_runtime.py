from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional

import pytest

from trading_lab.datahub import DataHub
from trading_lab.live_runtime import collect_live_data


@dataclass(frozen=True)
class FakeEnvelope:
    channel: str
    data: object
    source: str = "fixture"
    metadata: dict[str, object] = field(default_factory=dict)
    provenance: dict[str, object] = field(default_factory=dict)


class ManualClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class AsyncProvider:
    name = "fixture"

    def __init__(self, events: list[FakeEnvelope], clock: Optional[ManualClock] = None) -> None:
        self.events = events
        self.clock = clock

    async def stream(self):
        for event in self.events:
            if self.clock is not None:
                self.clock.advance(0.6)
            yield event


class FailingProvider:
    name = "broken"

    async def stream(self):
        yield FakeEnvelope("market:quote:AAPL", {"last": 101.3})
        raise RuntimeError("fixture disconnected")


class RecordingSnapshotStore:
    def __init__(self) -> None:
        self.records: list[object] = []

    def append(self, event, **_kwargs):
        self.records.append(event)
        return {"topic": event.topic}


def test_collect_live_data_publishes_envelopes_and_provider_status() -> None:
    hub = DataHub(clock=ManualClock())
    provider = AsyncProvider(
        [
            FakeEnvelope("market:quote:AAPL", {"last": 101.3}, metadata={"lag": "simulated"}),
            FakeEnvelope("market:quote:MSFT", {"last": 201.5}),
        ]
    )

    result = asyncio.run(collect_live_data(provider, hub, max_events=2))

    assert result.events_collected == 2
    assert result.status == "max_events_reached"
    assert hub.peek("market:quote:AAPL").payload == {"last": 101.3}
    assert hub.peek("market:quote:AAPL").producer == "fixture"
    assert hub.peek("market:quote:AAPL").metadata == {
        "lag": "simulated",
        "source": "fixture",
    }
    assert hub.peek("market:quote:MSFT").payload == {"last": 201.5}
    assert hub.peek("provider:status:fixture").payload == {
        "provider": "fixture",
        "state": "max_events_reached",
        "events_collected": 2,
    }


def test_collect_live_data_honors_duration_bound_with_injected_clock() -> None:
    clock = ManualClock()
    hub = DataHub(clock=clock)
    provider = AsyncProvider(
        [
            FakeEnvelope("market:quote:AAPL", {"last": 101.3}),
            FakeEnvelope("market:quote:MSFT", {"last": 201.5}),
            FakeEnvelope("market:quote:NVDA", {"last": 301.8}),
        ],
        clock=clock,
    )

    result = asyncio.run(collect_live_data(provider, hub, duration=1.0, clock=clock))

    assert result.events_collected == 2
    assert result.status == "duration_reached"
    assert hub.peek("market:quote:AAPL") is not None
    assert hub.peek("market:quote:MSFT") is not None
    assert hub.peek("market:quote:NVDA") is None


def test_collect_live_data_publishes_provider_errors_and_reraises() -> None:
    hub = DataHub(clock=ManualClock())

    with pytest.raises(RuntimeError, match="fixture disconnected"):
        asyncio.run(collect_live_data(FailingProvider(), hub))

    assert hub.peek("market:quote:AAPL").payload == {"last": 101.3}
    assert hub.peek("provider:error:broken").payload == {
        "provider": "broken",
        "state": "error",
        "events_collected": 1,
        "error": "fixture disconnected",
        "error_type": "RuntimeError",
    }


def test_collect_live_data_writes_snapshots_when_store_is_supplied() -> None:
    hub = DataHub(clock=ManualClock())
    store = RecordingSnapshotStore()
    provider = AsyncProvider([FakeEnvelope("market:quote:AAPL", {"last": 101.3})])

    result = asyncio.run(collect_live_data(provider, hub, max_events=1, snapshot_store=store))

    assert result.events_collected == 1
    assert [event.topic for event in store.records] == ["market:quote:AAPL"]
