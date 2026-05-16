from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
import re

from project.common.models import Asset
from project.data.repository import DataRepository


QualityStatus = Literal["ok", "warn", "fail"]
DEFAULT_MAX_STALENESS_DAYS = 7
SHORT_HISTORY_WARNING_ROWS = 20
_RESOLUTION_PATTERN = re.compile(r"^(?P<count>\d+)(?P<unit>[smhdw])$")


@dataclass(frozen=True)
class SymbolQualityReport:
    symbol: str
    asset_id: str | None
    row_count: int
    min_timestamp: str | None
    max_timestamp: str | None
    latest_timestamp: str | None
    duplicate_timestamp_count: int
    missing_ohlcv_count: int
    invalid_ohlc_count: int
    non_positive_close_count: int
    non_positive_volume_count: int
    large_gap_count: int
    source_count: int
    sources: tuple[str, ...]
    status: QualityStatus
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class DatasetQualityReport:
    status: QualityStatus
    resolution: str
    requested_symbols: tuple[str, ...]
    generated_at: str
    data_start: str | None
    data_end: str | None
    max_staleness_days: int
    source_count: int
    sources: tuple[str, ...]
    symbols: tuple[SymbolQualityReport, ...]


@dataclass(frozen=True)
class _MarketRow:
    timestamp: datetime
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None


@dataclass(frozen=True)
class _RowAnalysis:
    min_timestamp: datetime
    max_timestamp: datetime
    duplicate_timestamp_count: int
    missing_ohlcv_count: int
    missing_price_count: int
    missing_volume_count: int
    invalid_ohlc_count: int
    non_positive_close_count: int
    non_positive_volume_count: int
    large_gap_count: int
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def build_data_quality_report(
    repository: DataRepository,
    symbols: tuple[str, ...],
    resolution: str = "1d",
    max_staleness_days: int | None = None,
    data_start: str | None = None,
    data_end: str | None = None,
    as_of: datetime | None = None,
) -> DatasetQualityReport:
    requested_symbols = _normalize_symbols(symbols)
    start = _normalize_timestamp(data_start) if data_start is not None else None
    end = _normalize_timestamp(data_end) if data_end is not None else None
    if start is not None and end is not None and start > end:
        raise ValueError("data_start must be before data_end")
    staleness_days = (
        DEFAULT_MAX_STALENESS_DAYS
        if max_staleness_days is None
        else max_staleness_days
    )
    if staleness_days < 0:
        raise ValueError("max_staleness_days must be non-negative")
    current_time = as_of or datetime.now(UTC)
    symbol_reports = tuple(
        _symbol_quality_report(
            repository,
            symbol,
            resolution,
            staleness_days,
            start,
            end,
            current_time,
        )
        for symbol in requested_symbols
    )
    sources = tuple(sorted({source for report in symbol_reports for source in report.sources}))
    return DatasetQualityReport(
        status=(
            "fail"
            if any(report.status == "fail" for report in symbol_reports)
            else "warn"
            if any(report.status == "warn" for report in symbol_reports)
            else "ok"
        ),
        resolution=resolution,
        requested_symbols=requested_symbols,
        generated_at=_timestamp_text(current_time),
        data_start=_timestamp_text(start) if start is not None else None,
        data_end=_timestamp_text(end) if end is not None else None,
        max_staleness_days=staleness_days,
        source_count=len(sources),
        sources=sources,
        symbols=symbol_reports,
    )


def _symbol_quality_report(
    repository: DataRepository,
    symbol: str,
    resolution: str,
    max_staleness_days: int,
    start: datetime | None,
    end: datetime | None,
    as_of: datetime,
) -> SymbolQualityReport:
    asset = _asset_by_symbol(repository, symbol)
    if asset is None:
        return _missing_asset_report(symbol)
    rows = _market_rows(repository, asset.symbol, start, end)
    raw_sources = _raw_sources(repository, asset.asset_id, start, end)
    if not rows:
        return _empty_report(symbol, asset.asset_id, raw_sources)
    analysis = _analyze_rows(
        rows,
        raw_sources,
        resolution,
        max_staleness_days,
        as_of,
    )
    return SymbolQualityReport(
        symbol=symbol,
        asset_id=asset.asset_id,
        row_count=len(rows),
        min_timestamp=_timestamp_text(analysis.min_timestamp),
        max_timestamp=_timestamp_text(analysis.max_timestamp),
        latest_timestamp=_timestamp_text(analysis.max_timestamp),
        duplicate_timestamp_count=analysis.duplicate_timestamp_count,
        missing_ohlcv_count=analysis.missing_ohlcv_count,
        invalid_ohlc_count=analysis.invalid_ohlc_count,
        non_positive_close_count=analysis.non_positive_close_count,
        non_positive_volume_count=analysis.non_positive_volume_count,
        large_gap_count=analysis.large_gap_count,
        source_count=len(raw_sources),
        sources=raw_sources,
        status="fail" if analysis.errors else "warn" if analysis.warnings else "ok",
        errors=analysis.errors,
        warnings=analysis.warnings,
    )


def _empty_report(symbol: str, asset_id: str, sources: tuple[str, ...]) -> SymbolQualityReport:
    return _fail_report(symbol, asset_id, ("no rows in requested data",), sources)


def _missing_asset_report(symbol: str) -> SymbolQualityReport:
    return _fail_report(symbol, None, (f"asset not found: {symbol}",))


def _fail_report(
    symbol: str,
    asset_id: str | None,
    errors: tuple[str, ...],
    sources: tuple[str, ...] = (),
) -> SymbolQualityReport:
    return SymbolQualityReport(
        symbol=symbol,
        asset_id=asset_id,
        row_count=0,
        min_timestamp=None,
        max_timestamp=None,
        latest_timestamp=None,
        duplicate_timestamp_count=0,
        missing_ohlcv_count=0,
        invalid_ohlc_count=0,
        non_positive_close_count=0,
        non_positive_volume_count=0,
        large_gap_count=0,
        source_count=len(sources),
        sources=sources,
        status="fail",
        errors=errors,
        warnings=(),
    )


def _analyze_rows(
    rows: tuple[_MarketRow, ...],
    sources: tuple[str, ...],
    resolution: str,
    max_staleness_days: int,
    as_of: datetime,
) -> _RowAnalysis:
    timestamps = tuple(row.timestamp for row in rows)
    counts = Counter(timestamps)
    duplicate_timestamp_count = sum(count - 1 for count in counts.values() if count > 1)
    unique_timestamps = tuple(sorted(counts))
    missing_ohlcv_count = 0
    missing_price_count = 0
    missing_volume_count = 0
    invalid_ohlc_count = 0
    non_positive_close_count = 0
    non_positive_volume_count = 0
    for row in rows:
        missing_price = row.open is None or row.high is None or row.low is None or row.close is None
        missing_volume = row.volume is None
        if missing_price:
            missing_price_count += 1
        if missing_volume:
            missing_volume_count += 1
        if missing_price or missing_volume:
            missing_ohlcv_count += 1
        if not missing_price and (
            row.high < max(row.open, row.close, row.low)
            or row.low > min(row.open, row.close, row.high)
        ):
            invalid_ohlc_count += 1
        if row.close is not None and row.close <= 0:
            non_positive_close_count += 1
        if row.volume is not None and row.volume <= 0:
            non_positive_volume_count += 1
    large_gap_count = 0
    if len(unique_timestamps) > 1:
        threshold = _gap_threshold(resolution)
        large_gap_count = sum(
            1
            for left, right in zip(unique_timestamps, unique_timestamps[1:], strict=False)
            if right - left > threshold
        )
    latest_timestamp = max(unique_timestamps)
    errors = []
    if duplicate_timestamp_count:
        errors.append(f"duplicate timestamps: {duplicate_timestamp_count}")
    if missing_price_count:
        errors.append(f"missing OHLC values: {missing_price_count}")
    if invalid_ohlc_count:
        errors.append(f"invalid OHLC relations: {invalid_ohlc_count}")
    if non_positive_close_count:
        errors.append(f"non-positive close values: {non_positive_close_count}")
    if not sources:
        errors.append("no source metadata available")
    warnings = []
    if len(rows) < SHORT_HISTORY_WARNING_ROWS:
        warnings.append(f"short history: {len(rows)} rows")
    if len(sources) > 1:
        warnings.append(f"multiple sources: {len(sources)}")
    if large_gap_count:
        warnings.append(f"large timestamp gaps: {large_gap_count}")
    if non_positive_volume_count:
        warnings.append(f"non-positive volume values: {non_positive_volume_count}")
    if missing_volume_count:
        warnings.append(f"missing volume values: {missing_volume_count}")
    if as_of.astimezone(UTC) - latest_timestamp.astimezone(UTC) > timedelta(
        days=max_staleness_days
    ):
        warnings.append(
            f"latest timestamp is stale by more than {max_staleness_days} days"
        )
    return _RowAnalysis(
        min_timestamp=min(unique_timestamps),
        max_timestamp=latest_timestamp,
        duplicate_timestamp_count=duplicate_timestamp_count,
        missing_ohlcv_count=missing_ohlcv_count,
        missing_price_count=missing_price_count,
        missing_volume_count=missing_volume_count,
        invalid_ohlc_count=invalid_ohlc_count,
        non_positive_close_count=non_positive_close_count,
        non_positive_volume_count=non_positive_volume_count,
        large_gap_count=large_gap_count,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _gap_threshold(resolution: str) -> timedelta:
    match = _RESOLUTION_PATTERN.fullmatch(resolution.strip().lower())
    if match is None:
        raise ValueError(f"unsupported resolution: {resolution}")
    count = int(match.group("count"))
    unit = match.group("unit")
    base = {
        "s": timedelta(seconds=1),
        "m": timedelta(minutes=1),
        "h": timedelta(hours=1),
        "d": timedelta(days=1),
        "w": timedelta(weeks=1),
    }[unit]
    return base * (count * 3)


def _market_rows(
    repository: DataRepository,
    symbol: str,
    start: datetime | None,
    end: datetime | None,
) -> tuple[_MarketRow, ...]:
    return tuple(
        _MarketRow(
            timestamp=_normalize_timestamp(row[0]),
            open=_optional_float(row[1]),
            high=_optional_float(row[2]),
            low=_optional_float(row[3]),
            close=_optional_float(row[4]),
            volume=_optional_float(row[5]),
        )
        for row in repository.get_market_data(symbol, start, end)
    )


def _raw_sources(
    repository: DataRepository,
    asset_id: str,
    start: datetime | None,
    end: datetime | None,
) -> tuple[str, ...]:
    sources = {
        point.source
        for point in repository.read_raw_values(asset_id, "price")
        if (
            (start is None or _normalize_timestamp(point.timestamp) >= start)
            and (end is None or _normalize_timestamp(point.timestamp) <= end)
        )
    }
    return tuple(sorted(sources))


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


def _normalize_timestamp(value: object) -> datetime:
    timestamp = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if not isinstance(timestamp, datetime):
        raise ValueError(f"expected datetime timestamp, got {type(value)!r}")
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC).replace(microsecond=0)


def _timestamp_text(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _normalize_timestamp(value).isoformat()


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
