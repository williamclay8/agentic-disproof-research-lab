"""Async live data collection runtime for local research workflows."""

from __future__ import annotations

from dataclasses import dataclass
from inspect import isawaitable
from time import monotonic
from typing import Any, AsyncIterator, Callable, Iterator, Protocol

from trading_lab.datahub import DataEvent, DataHub


Clock = Callable[[], float]


class SnapshotStore(Protocol):
    def append(self, event: Any, **kwargs: Any) -> Any:
        ...


@dataclass(frozen=True)
class LiveCollectionResult:
    provider: str
    events_collected: int
    status: str


async def collect_live_data(
    provider: Any,
    datahub: DataHub,
    *,
    max_events: int | None = None,
    duration: float | None = None,
    clock: Clock | None = None,
    snapshot_store: SnapshotStore | None = None,
) -> LiveCollectionResult:
    """Collect provider envelopes into DataHub until a bound is reached."""

    if max_events is not None and max_events < 0:
        raise ValueError("max_events must be non-negative")
    if duration is not None and duration < 0:
        raise ValueError("duration must be non-negative")

    provider_name = _provider_name(provider)
    now = clock or monotonic
    started_at = now()
    collected = 0
    status = "completed"

    datahub.publish(
        _status_topic(provider_name),
        _status_payload(provider_name, "running", collected),
        producer=provider_name,
    )

    stream = _stream(provider)
    iterator = stream.__aiter__()

    try:
        while True:
            if max_events is not None and collected >= max_events:
                status = "max_events_reached"
                break
            if duration is not None and now() - started_at >= duration:
                status = "duration_reached"
                break

            try:
                envelope = await iterator.__anext__()
            except StopAsyncIteration:
                status = "completed"
                break

            event = datahub.publish(
                _envelope_topic(envelope),
                _envelope_payload(envelope),
                producer=provider_name,
                metadata=_envelope_metadata(envelope, provider_name),
            )
            collected += 1

            if snapshot_store is not None:
                await _append_snapshot(snapshot_store, event)

            if duration is not None and now() - started_at >= duration:
                status = "duration_reached"
                break
    except Exception as error:
        payload = _status_payload(provider_name, "error", collected)
        payload.update({"error": str(error), "error_type": type(error).__name__})
        datahub.publish(_error_topic(provider_name), payload, producer=provider_name)
        datahub.publish(_status_topic(provider_name), payload, producer=provider_name)
        raise

    datahub.publish(
        _status_topic(provider_name),
        _status_payload(provider_name, status, collected),
        producer=provider_name,
    )
    return LiveCollectionResult(
        provider=provider_name,
        events_collected=collected,
        status=status,
    )


def _stream(provider: Any) -> AsyncIterator[Any]:
    stream = provider.stream() if hasattr(provider, "stream") else provider
    if hasattr(stream, "__aiter__"):
        return stream
    if hasattr(stream, "__iter__"):
        return _async_from_sync(stream)
    raise TypeError("provider must expose a stream")


async def _async_from_sync(stream: Iterator[Any]) -> AsyncIterator[Any]:
    for item in stream:
        yield item


def _provider_name(provider: Any) -> str:
    name = getattr(provider, "name", None) or getattr(provider, "source", None)
    return str(name or provider.__class__.__name__)


def _envelope_topic(envelope: Any) -> str:
    topic = getattr(envelope, "channel", None) or getattr(envelope, "topic", None)
    if topic is None:
        raise ValueError("live envelope must include channel or topic")
    return str(topic)


def _envelope_payload(envelope: Any) -> Any:
    if hasattr(envelope, "data"):
        return envelope.data
    if hasattr(envelope, "payload"):
        return envelope.payload
    raise ValueError("live envelope must include data or payload")


def _envelope_metadata(envelope: Any, provider_name: str) -> dict[str, Any]:
    metadata = dict(getattr(envelope, "metadata", {}) or {})
    source = getattr(envelope, "source", None) or provider_name
    metadata.setdefault("source", source)
    if "delay_class" not in metadata and "lag" not in metadata:
        metadata.setdefault("delay_class", "simulated" if source == "fixture" else "unlabeled")
    timestamp = getattr(envelope, "timestamp", None)
    if timestamp is not None:
        metadata.setdefault("source_timestamp", timestamp)
    provenance = getattr(envelope, "provenance", None)
    if provenance:
        metadata.setdefault("provenance", provenance)
        metadata.setdefault("license_note", "research data only")
    return metadata


async def _append_snapshot(snapshot_store: SnapshotStore, event: DataEvent) -> None:
    result = snapshot_store.append(event)
    if isawaitable(result):
        await result


def _status_topic(provider_name: str) -> str:
    return f"provider:status:{provider_name}"


def _error_topic(provider_name: str) -> str:
    return f"provider:error:{provider_name}"


def _status_payload(provider_name: str, state: str, events_collected: int) -> dict[str, Any]:
    return {
        "provider": provider_name,
        "state": state,
        "events_collected": events_collected,
    }


__all__ = ["LiveCollectionResult", "SnapshotStore", "collect_live_data"]
