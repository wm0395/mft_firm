from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from project.cli_operator import _workflow_status_payload
from project.data.quality import build_data_quality_report
from project.data.repository import DataRepository
from project.data.snapshot_builder import DatasetSnapshotBuildResult, create_dataset_snapshot


@dataclass(frozen=True)
class AssetRowView:
    symbol: str
    name: str
    market: str
    sector: str
    created_at: str


@dataclass(frozen=True)
class QualityRowView:
    symbol: str
    status: str
    row_count: int
    latest_timestamp: str
    issues: str


@dataclass(frozen=True)
class SnapshotRowView:
    dataset_snapshot_id: str
    universe_id: str
    captured_at: str
    data_start: str
    data_end: str
    asset_count: int


@dataclass(frozen=True)
class SnapshotDefaultsView:
    name: str
    market: str
    symbols: tuple[str, ...]
    data_start: str
    data_end: str
    resolution: str
    description: str


@dataclass(frozen=True)
class DataPageView:
    assets: tuple[AssetRowView, ...]
    quality_rows: tuple[QualityRowView, ...]
    snapshots: tuple[SnapshotRowView, ...]
    default_snapshot: SnapshotDefaultsView
    quality_status: str
    workflow_next_command: str
    debug_payload: dict[str, Any]


def get_data_page_view(repository: DataRepository) -> DataPageView:
    assets = tuple(repository.list_assets())
    quality_report = _quality_report(repository, assets)
    quality = _quality_rows(quality_report)
    snapshots = tuple(
        SnapshotRowView(
            snapshot.dataset_snapshot_id,
            snapshot.universe_id,
            snapshot.captured_at,
            snapshot.data_start,
            snapshot.data_end,
            len(snapshot.asset_ids),
        )
        for snapshot in repository.get_dataset_snapshots()
    )
    return DataPageView(
        assets=tuple(
            AssetRowView(asset.symbol, asset.name, asset.market, asset.sector, asset.created_at)
            for asset in assets
        ),
        quality_rows=quality,
        snapshots=snapshots,
        default_snapshot=_default_snapshot_view(assets, quality_report),
        quality_status=_quality_status(quality),
        workflow_next_command=_workflow_next_command(repository),
        debug_payload={
            "assets": [asset.__dict__ for asset in assets],
            "snapshots": [snapshot.__dict__ for snapshot in snapshots],
            "workflow": _workflow_status_payload(repository),
        },
    )


def create_snapshot(
    repository: DataRepository,
    name: str,
    market: str,
    symbols: tuple[str, ...],
    data_start: str,
    data_end: str,
    resolution: str,
    description: str | None,
) -> DatasetSnapshotBuildResult:
    return create_dataset_snapshot(
        repository,
        name,
        market,
        symbols,
        data_start,
        data_end,
        resolution,
        description,
    )


def _quality_report(
    repository: DataRepository,
    assets: tuple[Any, ...],
):
    if not assets:
        return None
    symbols = tuple(asset.symbol for asset in assets)
    return build_data_quality_report(
        repository,
        symbols,
        as_of=_quality_as_of(repository, symbols),
    )


def _quality_as_of(repository: DataRepository, symbols: tuple[str, ...]) -> datetime:
    latest_timestamp: datetime | None = None
    for symbol in symbols:
        rows = repository.get_market_data(symbol, None, None)
        if not rows:
            continue
        row_timestamp = rows[-1][0]
        if latest_timestamp is None or row_timestamp > latest_timestamp:
            latest_timestamp = row_timestamp
    return latest_timestamp or datetime.now(UTC)


def _quality_rows(report) -> tuple[QualityRowView, ...]:
    if report is None:
        return ()
    return tuple(
        QualityRowView(
            symbol=item.symbol,
            status=item.status,
            row_count=item.row_count,
            latest_timestamp=item.latest_timestamp or "",
            issues=_issues(item.errors, item.warnings),
        )
        for item in report.symbols
    )


def _default_snapshot_view(
    assets: tuple[Any, ...],
    report,
) -> SnapshotDefaultsView:
    symbols = tuple(asset.symbol for asset in assets)
    market = assets[0].market if assets else "NSE"
    start, end = _quality_date_bounds(report)
    return SnapshotDefaultsView(
        name="Operator Snapshot",
        market=market,
        symbols=symbols,
        data_start=start,
        data_end=end,
        resolution="1d",
        description="Created from the MFT Operator Cockpit",
    )


def _quality_date_bounds(report) -> tuple[str, str]:
    if report is None:
        today = datetime.now(UTC).date().isoformat()
        return today, today
    timestamps = [
        timestamp
        for item in report.symbols
        for timestamp in (item.min_timestamp, item.max_timestamp)
        if timestamp is not None
    ]
    if not timestamps:
        today = datetime.now(UTC).date().isoformat()
        return today, today
    dates = tuple(_date_only(timestamp) for timestamp in timestamps)
    return min(dates), max(dates)


def _date_only(value: str) -> str:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(normalized).date().isoformat()


def _workflow_next_command(repository: DataRepository) -> str:
    workflow = _workflow_status_payload(repository)
    return str(workflow["next_recommended_command"])


def _issues(errors: tuple[str, ...], warnings: tuple[str, ...]) -> str:
    return "; ".join((*errors, *warnings))


def _quality_status(rows: tuple[QualityRowView, ...]) -> str:
    if not rows:
        return "unknown"
    if any(row.status == "fail" for row in rows):
        return "fail"
    if any(row.status == "warn" for row in rows):
        return "warn"
    return "ok"
