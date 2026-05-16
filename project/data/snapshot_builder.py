from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re

from project.common.models import Asset, DatasetSnapshot, ResearchUniverse
from project.data.ingestion import build_dataset_snapshot_identity
from project.data.models import DatasetProvenance
from project.data.quality import (
    DEFAULT_MAX_STALENESS_DAYS,
    DatasetQualityReport,
    build_data_quality_report,
)
from project.data.repository import DataRepository


@dataclass(frozen=True)
class DatasetSnapshotBuildResult:
    universe_id: str
    dataset_snapshot_id: str
    assets: tuple[str, ...]
    data_start: str
    data_end: str
    quality_status: str
    research_universe: ResearchUniverse
    dataset_snapshot: DatasetSnapshot
    quality_report: DatasetQualityReport
    provenance: DatasetProvenance


def create_dataset_snapshot(
    repository: DataRepository,
    name: str,
    market: str,
    symbols: tuple[str, ...],
    data_start: str,
    data_end: str,
    resolution: str = "1d",
    description: str | None = None,
) -> DatasetSnapshotBuildResult:
    normalized_symbols = _normalize_symbols(symbols)
    start = _normalize_range_bound(data_start, end=False)
    end = _normalize_range_bound(data_end, end=True)
    quality_report = build_data_quality_report(
        repository,
        normalized_symbols,
        resolution,
        DEFAULT_MAX_STALENESS_DAYS,
        start,
        end,
    )
    if quality_report.status == "fail":
        raise ValueError(_quality_failure_message(quality_report))
    assets = _resolve_assets(repository, normalized_symbols)
    universe = _research_universe(name, market, assets, description, resolution)
    snapshot = _dataset_snapshot(universe, assets, quality_report, resolution, start, end)
    with repository.transaction():
        repository.persist_research_artifact(universe)
        repository.persist_research_artifact(snapshot)
    provenance = repository.get_dataset_provenance(snapshot, resolution)
    return DatasetSnapshotBuildResult(
        universe_id=universe.universe_id,
        dataset_snapshot_id=snapshot.dataset_snapshot_id,
        assets=tuple(asset.symbol for asset in assets),
        data_start=start,
        data_end=end,
        quality_status=quality_report.status,
        research_universe=universe,
        dataset_snapshot=snapshot,
        quality_report=quality_report,
        provenance=provenance,
    )


def _research_universe(
    name: str,
    market: str,
    assets: tuple[Asset, ...],
    description: str | None,
    resolution: str,
) -> ResearchUniverse:
    return ResearchUniverse(
        universe_id=_universe_id(name, market),
        name=name,
        market=market.upper(),
        description=description or _default_description(name, market, resolution, assets),
        asset_ids=tuple(asset.asset_id for asset in assets),
    )


def _dataset_snapshot(
    universe: ResearchUniverse,
    assets: tuple[Asset, ...],
    quality_report: DatasetQualityReport,
    resolution: str,
    data_start: str,
    data_end: str,
) -> DatasetSnapshot:
    source_name = _source_name(quality_report.sources)
    return DatasetSnapshot(
        dataset_snapshot_id=build_dataset_snapshot_identity(
            source_name,
            resolution,
            tuple((asset.asset_id, asset.symbol) for asset in assets),
            data_start,
            data_end,
        ),
        universe_id=universe.universe_id,
        captured_at=_latest_timestamp(quality_report),
        data_start=data_start,
        data_end=data_end,
        asset_ids=tuple(asset.asset_id for asset in assets),
    )


def _resolve_assets(
    repository: DataRepository,
    symbols: tuple[str, ...],
) -> tuple[Asset, ...]:
    assets = []
    for symbol in symbols:
        asset = _asset_by_symbol(repository, symbol)
        if asset is None:
            raise ValueError(f"asset not found for symbol: {symbol}")
        assets.append(asset)
    return tuple(sorted(assets, key=lambda item: item.symbol))


def _asset_by_symbol(repository: DataRepository, symbol: str) -> Asset | None:
    for asset in repository.list_assets():
        if asset.symbol == symbol.upper():
            return asset
    return None


def _normalize_symbols(symbols: tuple[str, ...]) -> tuple[str, ...]:
    normalized: dict[str, None] = {}
    for symbol in symbols:
        text = symbol.strip().upper()
        if text:
            normalized.setdefault(text, None)
    if not normalized:
        raise ValueError("at least one symbol is required")
    return tuple(normalized)


def _normalize_range_bound(value: str, end: bool) -> str:
    if "T" in value or " " in value:
        return _normalize_datetime(value).isoformat()
    suffix = "23:59:59" if end else "00:00:00"
    return _normalize_datetime(f"{value}T{suffix}+00:00").isoformat()


def _normalize_datetime(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).replace(microsecond=0)


def _universe_id(name: str, market: str) -> str:
    return f"research_universe:{_slugify(name)}:{market.lower()}"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return slug.strip("_") or "dataset"


def _source_name(sources: tuple[str, ...]) -> str:
    return ",".join(sources) if sources else "unknown"


def _latest_timestamp(report: DatasetQualityReport) -> str:
    timestamps = [
        symbol.latest_timestamp
        for symbol in report.symbols
        if symbol.latest_timestamp is not None
    ]
    if not timestamps:
        raise ValueError("quality report does not contain a latest timestamp")
    return max(timestamps)


def _default_description(
    name: str,
    market: str,
    resolution: str,
    assets: tuple[Asset, ...],
) -> str:
    symbols = ", ".join(asset.symbol for asset in assets)
    return f"{name} {market.upper()} {resolution} dataset snapshot for {symbols}"


def _quality_failure_message(report: DatasetQualityReport) -> str:
    issues = []
    for symbol in report.symbols:
        if symbol.errors:
            issues.append(f"{symbol.symbol}: {'; '.join(symbol.errors)}")
    return "dataset quality checks failed: " + " | ".join(issues)
