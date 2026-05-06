from __future__ import annotations

from typing import Any

from project.common.models import RawDataPoint


def build_raw_price_point(asset_id: str, timestamp: str, close: float, source: str) -> RawDataPoint:
    if close <= 0:
        raise ValueError("close must be positive")
    if not timestamp or "T" not in timestamp:
        raise ValueError("timestamp must be an ISO datetime string")
    return RawDataPoint(
        data_id=f"raw:{asset_id}:{timestamp}:price:{source}",
        asset_id=asset_id,
        timestamp=timestamp,
        data_type="price",
        value={"close": float(close)},
        source=source,
    )


def close_prices(points: tuple[RawDataPoint, ...]) -> tuple[float, ...]:
    values: list[float] = []
    for point in points:
        close: Any = point.value.get("close")
        if not isinstance(close, int | float):
            raise ValueError(f"raw point {point.data_id} does not contain numeric close")
        values.append(float(close))
    return tuple(values)
