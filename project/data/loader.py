from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from project.data.models import DataSourceMetadata
from project.data.repository import DataRepository
from project.data.validation import validate_historical_data


@dataclass(frozen=True)
class CsvSourceMetadataAdapter:
    source_name: str
    symbol_mapping: tuple[tuple[str, str], ...]
    bar_timeframe: str

    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            source_name=self.source_name,
            symbol_mapping=tuple(sorted(self.symbol_mapping)),
            bar_timeframe=self.bar_timeframe,
        )


def load_ohlcv_csv(
    file_path: Path,
    asset_symbol: str,
    repository: DataRepository,
) -> int:
    """
    Deterministically loads OHLCV data from a CSV file.
    Expected CSV format: timestamp, open, high, low, close, volume
    Returns the number of rows ingested.
    """
    data: list[tuple[datetime, float, float, float, float, float]] = []

    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            first_row = next(reader)
        except StopIteration:
            return 0

        if first_row and not _looks_like_header(first_row):
            data.append(_parse_ohlcv_row(first_row))

        for row in reader:
            if not row:
                continue
            data.append(_parse_ohlcv_row(row))

    validation_result = validate_historical_data(data)
    if not validation_result.is_valid:
        raise ValueError(
            f"Historical data validation failed: {validation_result.errors}"
        )

    _ingest_ohlcv_records(repository, asset_symbol, tuple(data))
    return len(data)


def _ingest_ohlcv_records(
    repository: DataRepository,
    asset_symbol: str,
    records: tuple[tuple[datetime, float, float, float, float, float], ...],
) -> None:
    for record in records:
        repository.ingest_market_data(
            asset_symbol=asset_symbol,
            timestamp=record[0],
            open=record[1],
            high=record[2],
            low=record[3],
            close=record[4],
            volume=record[5],
        )


def _looks_like_header(row: list[str]) -> bool:
    try:
        _parse_ohlcv_row(row)
    except ValueError:
        return True
    return False


def _parse_ohlcv_row(row: list[str]) -> tuple[datetime, float, float, float, float, float]:
    try:
        ts = datetime.fromisoformat(row[0])
        open_p = float(row[1])
        high = float(row[2])
        low = float(row[3])
        close = float(row[4])
        volume = float(row[5])
    except (ValueError, IndexError) as error:
        raise ValueError(f"Invalid CSV row: {row}. Error: {error}") from error
    return (ts, open_p, high, low, close, volume)
