from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol

from project.common.models import RawDataPoint
from project.data.models import DataSourceMetadata, DatasetProvenance


class DataSourceMetadataAdapter(Protocol):
    def metadata(self) -> DataSourceMetadata:
        ...


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


def build_dataset_snapshot_identity(
    source_name: str,
    bar_timeframe: str,
    symbol_mapping: tuple[tuple[str, str], ...],
    data_start: str,
    data_end: str,
) -> str:
    payload = json.dumps(
        {
            "source_name": source_name,
            "bar_timeframe": bar_timeframe,
            "symbol_mapping": [list(item) for item in sorted(symbol_mapping)],
            "data_start": data_start,
            "data_end": data_end,
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"dataset_snapshot:{source_name}:{bar_timeframe}:{digest}"


def build_dataset_provenance(
    adapter: DataSourceMetadataAdapter,
    coverage_start: str,
    coverage_end: str,
) -> DatasetProvenance:
    metadata = adapter.metadata()
    if not metadata.source_name:
        raise ValueError("source name is required")
    if not metadata.bar_timeframe:
        raise ValueError("bar timeframe is required")
    if not metadata.symbol_mapping:
        raise ValueError("symbol mapping is required")
    snapshot_identity = build_dataset_snapshot_identity(
        metadata.source_name,
        metadata.bar_timeframe,
        metadata.symbol_mapping,
        coverage_start,
        coverage_end,
    )
    return DatasetProvenance(
        snapshot_identity=snapshot_identity,
        source_name=metadata.source_name,
        bar_timeframe=metadata.bar_timeframe,
        symbol_mapping=tuple(sorted(metadata.symbol_mapping)),
        coverage_start=coverage_start,
        coverage_end=coverage_end,
    )
