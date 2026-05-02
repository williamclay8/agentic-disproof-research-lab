"""Local CSV loading utilities for offline price research datasets."""

from __future__ import annotations

import csv
import hashlib
from datetime import date
from pathlib import Path
from typing import Any

from trading_lab.models import DatasetManifest


REQUIRED_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume"]
NUMERIC_COLUMNS = ["open", "high", "low", "close", "volume"]


def load_price_csv(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)

    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in columns]
        if missing:
            raise ValueError(f"missing required columns: {', '.join(missing)}")

        rows: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str]] = set()
        previous_key: tuple[str, str] | None = None

        for line_number, raw_row in enumerate(reader, start=2):
            row = _parse_price_row(raw_row, line_number)
            key = (row["date"], row["symbol"])

            if key in seen_keys:
                raise ValueError(f"duplicate date/symbol row: {key[0]} {key[1]}")
            if previous_key is not None and key < previous_key:
                raise ValueError("rows must be sorted by date then symbol")

            seen_keys.add(key)
            previous_key = key
            rows.append(row)

    return rows


def build_manifest(path: str | Path, rows: list[dict[str, Any]]) -> DatasetManifest:
    source = Path(path)
    dates = [row["date"] for row in rows]
    columns = _read_header(source)

    return DatasetManifest(
        source=str(source),
        symbols=sorted({row["symbol"] for row in rows}),
        start_date=min(dates),
        end_date=max(dates),
        columns=columns,
        content_hash=hashlib.sha256(source.read_bytes()).hexdigest(),
        warnings=[],
    )


def _parse_price_row(raw_row: dict[str, str], line_number: int) -> dict[str, Any]:
    parsed_date = _parse_iso_date(raw_row["date"], line_number)
    symbol = raw_row["symbol"].strip()
    if not symbol:
        raise ValueError(f"line {line_number}: symbol must be non-empty")

    row: dict[str, Any] = {
        "date": parsed_date,
        "symbol": symbol,
    }
    for column in NUMERIC_COLUMNS:
        row[column] = _parse_float(raw_row[column], column, line_number)

    return row


def _parse_iso_date(value: str, line_number: int) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"line {line_number}: date must be ISO formatted") from exc


def _parse_float(value: str, column: str, line_number: int) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"line {line_number}: {column} must be numeric") from exc


def _read_header(source: Path) -> list[str]:
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return next(reader, [])
