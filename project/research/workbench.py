from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from project.common.models import DatasetSnapshot
from project.data.repository import DataRepository
from project.research.models import WorkbenchBar, WorkbenchSeries


def load_workbench_series(
    repository: DataRepository,
    asset_symbol: str,
    start_date: str,
    end_date: str,
) -> WorkbenchSeries:
    start_timestamp = _day_bound(start_date, end=False)
    end_timestamp = _day_bound(end_date, end=True)
    rows = repository.get_market_data(asset_symbol.upper(), start_timestamp, end_timestamp)
    bars = tuple(_bar_from_row(row) for row in rows)
    if not bars:
        raise ValueError("workbench series is empty")
    return WorkbenchSeries(asset_symbol=asset_symbol.upper(), bars=bars)


def load_workbench_series_for_snapshot(
    repository: DataRepository,
    dataset_snapshot_id: str,
    asset_symbol: str,
) -> WorkbenchSeries:
    snapshot = _dataset_snapshot(repository, dataset_snapshot_id)
    asset_id = f"asset:{asset_symbol.upper()}"
    if asset_id not in snapshot.asset_ids:
        raise ValueError(f"asset {asset_symbol.upper()} is not included in dataset snapshot {dataset_snapshot_id}")
    return load_workbench_series(repository, asset_symbol, snapshot.data_start[:10], snapshot.data_end[:10])


def close_prices(series: WorkbenchSeries) -> tuple[float, ...]:
    return tuple(bar.close for bar in series.bars)


def _dataset_snapshot(repository: DataRepository, dataset_snapshot_id: str) -> DatasetSnapshot:
    for snapshot in repository.get_dataset_snapshots():
        if snapshot.dataset_snapshot_id == dataset_snapshot_id:
            return snapshot
    raise ValueError(f"dataset snapshot not found: {dataset_snapshot_id}")


def _bar_from_row(row: tuple[object, ...]) -> WorkbenchBar:
    return WorkbenchBar(
        timestamp=_timestamp_text(row[0]),
        open=_float_value(row[1]),
        high=_float_value(row[2]),
        low=_float_value(row[3]),
        close=_float_value(row[4]),
        volume=_float_value(row[5]),
    )


def _day_bound(value: str, end: bool) -> datetime:
    suffix = "23:59:59" if end else "00:00:00"
    return _timestamp_value(f"{value}T{suffix}+00:00")


def _timestamp_text(value: object) -> str:
    parsed = _timestamp_value(value)
    return parsed.astimezone(UTC).replace(microsecond=0).isoformat()


def _timestamp_value(value: object) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime):
        raise ValueError("timestamp must be datetime-like")
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _float_value(value: object) -> float:
    return float(cast(Any, value))
