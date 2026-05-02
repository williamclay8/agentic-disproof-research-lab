"""Append-only snapshot storage for local DataHub-style events."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


JSONValue = Any


class SnapshotStore:
    """Persist event snapshots as JSONL plus a compact latest pointer."""

    def __init__(
        self,
        root: str | Path,
        *,
        jsonl_name: str = "snapshots.jsonl",
        latest_name: str = "latest.json",
    ) -> None:
        self.root = Path(root)
        self.jsonl_path = self.root / jsonl_name
        self.latest_path = self.root / latest_name

    def append(
        self,
        event: Any,
        *,
        topic: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        provenance: Mapping[str, Any] | None = None,
    ) -> dict[str, JSONValue]:
        """Append one snapshot and replace the compact latest record."""

        record = _snapshot_record(
            event,
            topic=topic,
            metadata=metadata,
            provenance=provenance,
        )
        self.root.mkdir(parents=True, exist_ok=True)
        line = _canonical_json(record)
        with self.jsonl_path.open("a", encoding="utf-8") as stream:
            stream.write(line)
            stream.write("\n")

        tmp_path = self.latest_path.with_suffix(f"{self.latest_path.suffix}.tmp")
        tmp_path.write_text(line, encoding="utf-8")
        tmp_path.replace(self.latest_path)
        return record

    def read_latest(self) -> dict[str, JSONValue] | None:
        """Return the latest compact snapshot, if it exists."""

        return read_latest(self.root, latest_name=self.latest_path.name)


def read_latest(
    root: str | Path,
    *,
    latest_name: str = "latest.json",
) -> dict[str, JSONValue] | None:
    """Read the compact latest snapshot from a store directory or file."""

    path = Path(root)
    latest_path = path if path.is_file() else path / latest_name
    if not latest_path.exists():
        return None
    return json.loads(latest_path.read_text(encoding="utf-8"))


def snapshot_hash(value: Any) -> str:
    """Return a deterministic SHA-256 hash for a JSON-safe snapshot value."""

    return sha256(_canonical_json(_safe_json(value)).encode("utf-8")).hexdigest()


def _snapshot_record(
    event: Any,
    *,
    topic: str | None,
    metadata: Mapping[str, Any] | None,
    provenance: Mapping[str, Any] | None,
) -> dict[str, JSONValue]:
    event_metadata = _read_mapping(event, "metadata")
    event_provenance = _read_mapping(event, "provenance")
    record_metadata = {**event_metadata, **dict(metadata or {})}
    record_provenance = {**event_provenance, **dict(provenance or {})}

    record: dict[str, JSONValue] = {
        "topic": _safe_json(topic or _read_topic(event)),
        "payload": _safe_json(_read_payload(event)),
        "metadata": _safe_json(record_metadata),
        "provenance": _safe_json(record_provenance),
    }
    for name in ("created_at", "sequence", "expires_at", "producer"):
        value = _read_optional(event, name)
        if value is not None:
            record[name] = _safe_json(value)
    record["hash"] = snapshot_hash(record)
    return record


def _read_topic(event: Any) -> Any:
    if isinstance(event, Mapping):
        return event.get("topic") or event.get("channel") or event.get("name")
    return (
        getattr(event, "topic", None)
        or getattr(event, "channel", None)
        or getattr(event, "name", None)
    )


def _read_payload(event: Any) -> Any:
    if isinstance(event, Mapping):
        if "payload" in event:
            return event["payload"]
        if "data" in event:
            return event["data"]
        return event
    if hasattr(event, "payload"):
        return getattr(event, "payload")
    if hasattr(event, "data"):
        return getattr(event, "data")
    return event


def _read_mapping(event: Any, name: str) -> dict[str, Any]:
    value = _read_optional(event, name)
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _read_optional(event: Any, name: str) -> Any:
    if isinstance(event, Mapping):
        return event.get(name)
    return getattr(event, name, None)


def _safe_json(value: Any) -> JSONValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _safe_json(item) for key, item in sorted(value.items(), key=_sort_key)}
    if isinstance(value, (list, tuple)):
        return [_safe_json(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_safe_json(item) for item in sorted(value, key=lambda item: _canonical_json(_safe_json(item)))]
    if is_dataclass(value) and not isinstance(value, type):
        return _safe_json(asdict(value))
    return f"<{type(value).__module__}.{type(value).__qualname__}>"


def _sort_key(item: tuple[Any, Any]) -> str:
    return str(item[0])


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


__all__ = ["SnapshotStore", "read_latest", "snapshot_hash"]
