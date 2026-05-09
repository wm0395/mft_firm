from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from project.data.repository import DataRepository
from project.data.validation import validate_historical_data

def load_ohlcv_csv(
    file_path: Path, 
    asset_symbol: str, 
    repository: DataRepository
) -> int:
    """
    Deterministically loads OHLCV data from a CSV file.
    Expected CSV format: timestamp, open, high, low, close, volume
    Returns the number of rows ingested.
    """
    data: List[Tuple[datetime, float, float, float, float, float]] = []
    
    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        # Skip header if it exists. Assuming first row is header.
        try:
            next(reader)
            # Basic check to see if it's a header or data
            # If the first element is not a digit/date, it's likely a header.
            # This is a simple heuristic.
        except StopIteration:
            return 0

        for row in reader:
            if not row:
                continue
            try:
                # Expected: timestamp, open, high, low, close, volume
                ts = datetime.fromisoformat(row[0])
                open_p = float(row[1])
                high = float(row[2])
                low = float(row[3])
                close = float(row[4])
                volume = float(row[5])
                data.append((ts, open_p, high, low, close, volume))
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid CSV row: {row}. Error: {e}")

    # Validate
    validation_result = validate_historical_data(data)
    if not validation_result.is_valid:
        raise ValueError(f"Historical data validation failed: {validation_result.errors}")

    # Ingest
    for row in data:
        repository.ingest_market_data(
            asset_symbol=asset_symbol,
            timestamp=row[0],
            open=row[1],
            high=row[2],
            low=row[3],
            close=row[4],
            volume=row[5]
        )

    return len(data)
