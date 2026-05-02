import json
from dataclasses import dataclass

from trading_lab.datahub import DataEvent
from trading_lab.snapshots import SnapshotStore, read_latest, snapshot_hash


def test_snapshot_hash_is_deterministic_and_order_insensitive() -> None:
    left = {
        "topic": "market:AAPL",
        "payload": {"price": 101.25, "sizes": [3, 1]},
        "metadata": {"source": "fixture", "tags": {"b": 2, "a": 1}},
    }
    right = {
        "metadata": {"tags": {"a": 1, "b": 2}, "source": "fixture"},
        "payload": {"sizes": [3, 1], "price": 101.25},
        "topic": "market:AAPL",
    }

    assert snapshot_hash(left) == snapshot_hash(right)


def test_snapshot_hash_uses_stable_fallback_for_unknown_objects() -> None:
    assert snapshot_hash({"marker": object()}) == snapshot_hash({"marker": object()})


def test_store_appends_jsonl_and_writes_compact_latest_for_datahub_event(tmp_path) -> None:
    store = SnapshotStore(tmp_path)
    event = DataEvent(
        topic="market:AAPL",
        payload={"price": 101.25},
        created_at=123.45,
        sequence=7,
        expires_at=130.0,
        producer="fixture",
        metadata={"run_id": "run-1", "nested": {"k": "v"}},
    )

    first = store.append(event, provenance={"dataset": "toy"}, metadata={"view": "dashboard"})
    second = store.append(
        DataEvent(
            topic="market:AAPL",
            payload={"price": 102.0},
            created_at=124.0,
            sequence=8,
            producer="fixture",
            metadata={"run_id": "run-2"},
        )
    )

    jsonl_records = [
        json.loads(line)
        for line in (tmp_path / "snapshots.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    latest_text = (tmp_path / "latest.json").read_text(encoding="utf-8")

    assert [record["hash"] for record in jsonl_records] == [first["hash"], second["hash"]]
    assert json.loads(latest_text) == second
    assert "\n" not in latest_text
    assert first["topic"] == "market:AAPL"
    assert first["payload"] == {"price": 101.25}
    assert first["producer"] == "fixture"
    assert first["metadata"] == {
        "run_id": "run-1",
        "nested": {"k": "v"},
        "view": "dashboard",
    }
    assert first["provenance"] == {"dataset": "toy"}
    assert first["hash"] == snapshot_hash({k: v for k, v in first.items() if k != "hash"})


@dataclass(frozen=True)
class LiveEnvelope:
    channel: str
    data: object
    metadata: dict[str, object]
    provenance: dict[str, object]


def test_store_preserves_live_envelope_metadata_and_read_latest(tmp_path) -> None:
    store = SnapshotStore(tmp_path)
    envelope = LiveEnvelope(
        channel="signals:alpha",
        data={"score": 0.82},
        metadata={"model": "baseline"},
        provenance={"generated_by": "unit-test"},
    )

    record = store.append(envelope, metadata={"view": "lab"})

    assert record["topic"] == "signals:alpha"
    assert record["payload"] == {"score": 0.82}
    assert record["metadata"] == {"model": "baseline", "view": "lab"}
    assert record["provenance"] == {"generated_by": "unit-test"}
    assert store.read_latest() == record
    assert read_latest(tmp_path) == record


def test_safe_serialization_handles_sets_tuples_and_objects(tmp_path) -> None:
    store = SnapshotStore(tmp_path)

    record = store.append(
        {"payload": {"symbols": {"MSFT", "AAPL"}, "window": (5, 20), "marker": object()}},
        topic="research:example",
    )

    assert record["payload"]["symbols"] == ["AAPL", "MSFT"]
    assert record["payload"]["window"] == [5, 20]
    assert isinstance(record["payload"]["marker"], str)
