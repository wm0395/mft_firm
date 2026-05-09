from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from datetime import datetime

@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: List[str]

def validate_ohlcv_consistency(open_p: float, high: float, low: float, close: float) -> Tuple[bool, str | None]:
    if high < open_p or high < close:
        return False, f"High {high} is less than open {open_p} or close {close}"
    if low > open_p or low > close:
        return False, f"Low {low} is greater than open {open_p} or close {close}"
    if low > high:
        return False, f"Low {low} is greater than high {high}"
    return True, None

def validate_historical_data(data: List[Tuple[datetime, float, float, float, float, float]]) -> ValidationResult:
    errors = []
    last_timestamp = None
    seen_timestamps = set()

    for i, row in enumerate(data):
        ts, open_p, high, low, close, volume = row
        
        if ts in seen_timestamps:
            errors.append(f"Duplicate timestamp at row {i}: {ts}")
        seen_timestamps.add(ts)

        if last_timestamp and ts <= last_timestamp:
            errors.append(f"Timestamp not strictly increasing at row {i}: {ts} <= {last_timestamp}")
        last_timestamp = ts

        valid, error = validate_ohlcv_consistency(open_p, high, low, close)
        if not valid:
            errors.append(f"OHLC inconsistency at row {i} ({ts}): {error}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
