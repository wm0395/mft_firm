from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from project.data.contract_models import (
    MacroSeriesRecord,
    PointInTimeMetadataStatusRecord,
)
from project.data_sources.common import (
    SourceSampleResult,
    build_quality_report,
    build_raw_file_record,
)

SOURCE_ID = "fred_api"
SUPPORTED_ASSET_CLASSES = ("macro_series",)


def parse_sample_payload(
    payload: dict[str, Any],
    fixture_path: Path,
    fixture_text: str,
    asset_class: str,
) -> SourceSampleResult:
    if asset_class not in SUPPORTED_ASSET_CLASSES:
        raise ValueError(f"unsupported FRED asset class: {asset_class}")
    rows = _selected_rows(payload, asset_class)
    canonical_records = tuple(_macro_record(row, fixture_path) for row in rows)
    metadata_records = tuple(_metadata_record(row, fixture_path) for row in rows)
    raw_file = build_raw_file_record(
        SOURCE_ID,
        asset_class,
        fixture_path,
        fixture_text,
        _text(payload.get("source_url", "https://fred.stlouisfed.org")),
        _text(payload.get("sample_date", _timestamp_date(rows[0]))),
        "prototype fixture for FRED API",
    )
    quality_report = build_quality_report(
        SOURCE_ID,
        asset_class,
        raw_file,
        canonical_records,
        metadata_records,
        duplicate_timestamp_count=_duplicate_timestamps(canonical_records),
        notes="prototype sample only; series vintage handling remains research-only",
    )
    return SourceSampleResult(
        source_id=SOURCE_ID,
        asset_class=asset_class,
        canonical_records=canonical_records,
        metadata_records=metadata_records,
        raw_file=raw_file,
        quality_report=quality_report,
    )


def _selected_rows(payload: dict[str, Any], asset_class: str) -> list[dict[str, Any]]:
    rows = payload.get("records")
    if not isinstance(rows, list):
        raise ValueError("FRED fixture must contain a records list")
    selected = [
        row
        for row in rows
        if isinstance(row, dict) and _text(row.get("asset_class")) == asset_class
    ]
    if not selected:
        raise ValueError(f"fixture does not include asset_class={asset_class}")
    return selected


def _macro_record(row: dict[str, Any], fixture_path: Path) -> MacroSeriesRecord:
    _require_fields(
        row,
        (
            "asset_id",
            "symbol",
            "timestamp",
            "value",
            "frequency",
            "unit",
            "release_date",
            "revision_flag",
        ),
    )
    return MacroSeriesRecord(
        series_record_id=_stable_id("series", row, fixture_path),
        source_id=SOURCE_ID,
        asset_id=_text(row["asset_id"]),
        symbol=_text(row["symbol"]),
        asset_class=_text(row["asset_class"]),
        timestamp=_text(row["timestamp"]),
        value=_number(row["value"]),
        frequency=_text(row["frequency"]),
        unit=_text(row["unit"]),
        release_date=_text(row["release_date"]),
        revision_flag=_text(row["revision_flag"]),
        realtime_start=_optional_text(row.get("realtime_start")),
        realtime_end=_optional_text(row.get("realtime_end")),
        raw_reference=_raw_reference("fred", row, fixture_path),
        ingestion_timestamp=_now(),
    )


def _metadata_record(row: dict[str, Any], fixture_path: Path) -> PointInTimeMetadataStatusRecord:
    return PointInTimeMetadataStatusRecord(
        status_id=_stable_id("status", row, fixture_path),
        asset_id=_text(row["asset_id"]),
        source_id=SOURCE_ID,
        metadata_type="release_vintage",
        point_in_time_status=_text(row.get("point_in_time_status", "available")),
        valid_from=_text(row["release_date"]),
        valid_to=None,
        notes="prototype sample fixture",
    )


def _duplicate_timestamps(records: tuple[MacroSeriesRecord, ...]) -> int:
    timestamps = [record.timestamp for record in records]
    return len(timestamps) - len(set(timestamps))


def _require_fields(row: dict[str, Any], required: tuple[str, ...]) -> None:
    missing = [field for field in required if field not in row or row[field] in (None, "")]
    if missing:
        raise ValueError(f"missing required FRED fields: {', '.join(sorted(missing))}")


def _raw_reference(prefix: str, row: dict[str, Any], fixture_path: Path) -> str:
    payload = f"{prefix}:{fixture_path.name}:{row.get('asset_id')}:{row.get('timestamp')}"
    digest = sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{digest}"


def _stable_id(prefix: str, row: dict[str, Any], fixture_path: Path) -> str:
    return _raw_reference(prefix, row, fixture_path)


def _text(value: Any) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError("fixture field must be non-empty")
    return text


def _optional_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return _text(value)


def _number(value: Any) -> float:
    return float(value)


def _timestamp_date(row: dict[str, Any]) -> str:
    return _text(row["timestamp"])[:10]


def _now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat()
