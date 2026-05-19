from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

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
    debug_payload: dict[str, Any]


def get_data_page_view(repository: DataRepository) -> DataPageView:
    assets = tuple(repository.list_assets())
    quality = _quality_rows(repository, assets)
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
        default_snapshot=_default_snapshot_view(assets),
        quality_status=_quality_status(quality),
        debug_payload={
            "assets": [asset.__dict__ for asset in assets],
            "snapshots": [snapshot.__dict__ for snapshot in snapshots],
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


def _quality_rows(
    repository: DataRepository,
    assets: tuple[Any, ...],
) -> tuple[QualityRowView, ...]:
    if not assets:
        return ()
    report = build_data_quality_report(repository, tuple(asset.symbol for asset in assets))
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


def _default_snapshot_view(assets: tuple[Any, ...]) -> SnapshotDefaultsView:
    symbols = tuple(asset.symbol for asset in assets)
    market = assets[0].market if assets else "NSE"
    today = datetime.now(UTC).date().isoformat()
    return SnapshotDefaultsView(
        name="Operator Snapshot",
        market=market,
        symbols=symbols,
        data_start=today,
        data_end=today,
        resolution="1d",
        description="Created from the MFT Operator Cockpit",
    )


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

