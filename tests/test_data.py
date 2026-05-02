from pathlib import Path

import pytest

from trading_lab.data import build_manifest, load_price_csv
from trading_lab.models import DatasetManifest


def write_csv(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_load_price_csv_returns_typed_sorted_rows(tmp_path):
    csv_path = write_csv(
        tmp_path / "prices.csv",
        "\n".join(
            [
                "date,symbol,open,high,low,close,volume",
                "2024-01-02,AAA,10,11,9.5,10.5,1000",
                "2024-01-02,BBB,20,21,19,20.5,2000",
                "2024-01-03,AAA,10.5,12,10,11.5,1100",
            ]
        ),
    )

    rows = load_price_csv(csv_path)

    assert rows == [
        {
            "date": "2024-01-02",
            "symbol": "AAA",
            "open": 10.0,
            "high": 11.0,
            "low": 9.5,
            "close": 10.5,
            "volume": 1000.0,
        },
        {
            "date": "2024-01-02",
            "symbol": "BBB",
            "open": 20.0,
            "high": 21.0,
            "low": 19.0,
            "close": 20.5,
            "volume": 2000.0,
        },
        {
            "date": "2024-01-03",
            "symbol": "AAA",
            "open": 10.5,
            "high": 12.0,
            "low": 10.0,
            "close": 11.5,
            "volume": 1100.0,
        },
    ]


def test_load_price_csv_rejects_missing_required_columns(tmp_path):
    csv_path = write_csv(
        tmp_path / "missing.csv",
        "\n".join(
            [
                "date,symbol,open,high,low,close",
                "2024-01-02,AAA,10,11,9.5,10.5",
            ]
        ),
    )

    with pytest.raises(ValueError, match="volume"):
        load_price_csv(csv_path)


def test_load_price_csv_rejects_duplicate_date_symbol_rows(tmp_path):
    csv_path = write_csv(
        tmp_path / "duplicate.csv",
        "\n".join(
            [
                "date,symbol,open,high,low,close,volume",
                "2024-01-02,AAA,10,11,9.5,10.5,1000",
                "2024-01-02,AAA,10.5,11.5,10,11,1200",
            ]
        ),
    )

    with pytest.raises(ValueError, match="duplicate.*2024-01-02.*AAA"):
        load_price_csv(csv_path)


def test_load_price_csv_rejects_rows_not_sorted_by_date_then_symbol(tmp_path):
    csv_path = write_csv(
        tmp_path / "unsorted.csv",
        "\n".join(
            [
                "date,symbol,open,high,low,close,volume",
                "2024-01-03,AAA,10,11,9.5,10.5,1000",
                "2024-01-02,BBB,20,21,19,20.5,2000",
            ]
        ),
    )

    with pytest.raises(ValueError, match="sorted by date then symbol"):
        load_price_csv(csv_path)


def test_build_manifest_summarizes_rows_and_hashes_file_bytes(tmp_path):
    csv_path = write_csv(
        tmp_path / "prices.csv",
        "\n".join(
            [
                "date,symbol,open,high,low,close,volume",
                "2024-01-02,BBB,20,21,19,20.5,2000",
                "2024-01-03,AAA,10.5,12,10,11.5,1100",
            ]
        ),
    )
    rows = load_price_csv(csv_path)

    manifest = build_manifest(csv_path, rows)
    same_manifest = build_manifest(csv_path, rows)
    changed_path = write_csv(
        tmp_path / "changed.csv",
        csv_path.read_text(encoding="utf-8") + "\n",
    )

    assert isinstance(manifest, DatasetManifest)
    assert manifest.source == str(csv_path)
    assert manifest.symbols == ["AAA", "BBB"]
    assert manifest.start_date == "2024-01-02"
    assert manifest.end_date == "2024-01-03"
    assert manifest.columns == ["date", "symbol", "open", "high", "low", "close", "volume"]
    assert manifest.content_hash == same_manifest.content_hash
    assert manifest.content_hash != build_manifest(changed_path, rows).content_hash
    assert manifest.warnings == []


def test_build_manifest_preserves_extra_csv_columns_for_leakage_gates(tmp_path):
    csv_path = write_csv(
        tmp_path / "prices.csv",
        "\n".join(
            [
                "date,symbol,open,high,low,close,volume,future_return",
                "2024-01-02,AAA,10,11,9.5,10.5,1000,0.03",
                "2024-01-03,AAA,10.5,12,10,11.5,1100,0.01",
            ]
        ),
    )
    rows = load_price_csv(csv_path)

    manifest = build_manifest(csv_path, rows)

    assert "future_return" in manifest.columns
