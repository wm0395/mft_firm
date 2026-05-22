from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from project.data.contract_models import (
    CanonicalOHLCVRecord,
    ContractMetadataRecord,
    InstrumentRecord,
    PointInTimeIndustryMetadataRecord,
    PointInTimeMetadataStatusRecord,
    SymbolMappingRecord,
)
from project.data_sources.common import (
    SourceSampleResult,
    build_quality_report,
    build_raw_file_record,
)

SOURCE_ID = "nse_official_reports"
SUPPORTED_ASSET_CLASSES = (
    "indian_equity_cash",
    "indian_etf",
    "indian_index",
    "nse_equity_derivative",
)


def parse_sample_payload(
    payload: dict[str, Any],
    fixture_path: Path,
    fixture_text: str,
    asset_class: str,
) -> SourceSampleResult:
    if asset_class not in SUPPORTED_ASSET_CLASSES:
        raise ValueError(f"unsupported NSE asset class: {asset_class}")
    rows = _selected_rows(payload, asset_class)
    canonical_records: list[CanonicalOHLCVRecord] = []
    metadata_records: list[object] = []
    for row in rows:
        canonical_records.append(_canonical_record(row, fixture_path))
        metadata_records.extend(_metadata_records(row, fixture_path))
    raw_file = build_raw_file_record(
        SOURCE_ID,
        asset_class,
        fixture_path,
        fixture_text,
        _text(payload.get("source_url", "https://www.nseindia.com")),
        _text(payload.get("sample_date", _timestamp_date(rows[0]))),
        "prototype fixture for NSE official reports",
    )
    quality_report = build_quality_report(
        SOURCE_ID,
        asset_class,
        raw_file,
        tuple(canonical_records),
        tuple(metadata_records),
        duplicate_timestamp_count=_duplicate_timestamps(canonical_records),
        notes="prototype sample only; exchange downloads remain non-production",
    )
    return SourceSampleResult(
        source_id=SOURCE_ID,
        asset_class=asset_class,
        canonical_records=tuple(canonical_records),
        metadata_records=tuple(metadata_records),
        raw_file=raw_file,
        quality_report=quality_report,
    )


def _selected_rows(payload: dict[str, Any], asset_class: str) -> list[dict[str, Any]]:
    rows = payload.get("records")
    if not isinstance(rows, list):
        raise ValueError("NSE fixture must contain a records list")
    selected = [
        row
        for row in rows
        if isinstance(row, dict) and _text(row.get("asset_class")) == asset_class
    ]
    if not selected:
        raise ValueError(f"fixture does not include asset_class={asset_class}")
    return selected


def _canonical_record(row: dict[str, Any], fixture_path: Path) -> CanonicalOHLCVRecord:
    required = (
        "asset_id",
        "symbol",
        "source_symbol",
        "exchange",
        "sector",
        "industry",
        "country",
        "currency",
        "lot_size",
        "tick_size",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "vwap",
        "volume",
        "instrument_type",
        "valid_from",
    )
    _require_fields(row, required)
    raw_reference = _raw_reference("nse", row, fixture_path)
    return CanonicalOHLCVRecord(
        source_id=SOURCE_ID,
        asset_id=_text(row["asset_id"]),
        symbol=_text(row["symbol"]),
        asset_class=_text(row["asset_class"]),
        timestamp=_text(row["timestamp"]),
        open=_number(row["open"]),
        high=_number(row["high"]),
        low=_number(row["low"]),
        close=_number(row["close"]),
        volume=_number(row["volume"]),
        vwap=_number(row["vwap"]),
        adjusted_close=_optional_number(row.get("adjusted_close")),
        turnover=_optional_number(row.get("turnover")),
        delivery_volume=_optional_number(row.get("delivery_volume")),
        open_interest=_optional_number(row.get("open_interest")),
        contract_expiry=_optional_text(row.get("contract_expiry")),
        instrument_type=_text(row["instrument_type"]),
        currency=_text(row["currency"]),
        raw_reference=raw_reference,
        ingestion_timestamp=_now(),
    )


def _metadata_records(row: dict[str, Any], fixture_path: Path) -> tuple[object, ...]:
    asset_class = _text(row["asset_class"])
    industry_status = PointInTimeMetadataStatusRecord(
        status_id=_stable_id("status", row, fixture_path),
        asset_id=_text(row["asset_id"]),
        source_id=SOURCE_ID,
        metadata_type="industry",
        point_in_time_status=_text(row.get("point_in_time_status", "available")),
        valid_from=_text(row["valid_from"]),
        valid_to=_optional_text(row.get("valid_to")),
        notes="prototype sample fixture",
    )
    industry_metadata = PointInTimeIndustryMetadataRecord(
        industry_metadata_id=_stable_id("industry", row, fixture_path),
        asset_id=_text(row["asset_id"]),
        source_id=SOURCE_ID,
        source_symbol=_text(row["source_symbol"]),
        asset_class=asset_class,
        exchange=_text(row["exchange"]),
        sector=_text(row["sector"]),
        industry=_text(row["industry"]),
        country=_text(row["country"]),
        valid_from=_text(row["valid_from"]),
        valid_to=_optional_text(row.get("valid_to")),
        as_of_timestamp=_text(row["timestamp"]),
        point_in_time_status=_text(row.get("point_in_time_status", "available")),
        notes="prototype sample fixture",
    )
    instrument = InstrumentRecord(
        asset_id=_text(row["asset_id"]),
        symbol=_text(row["symbol"]),
        source_symbol=_text(row["source_symbol"]),
        asset_class=asset_class,
        exchange=_text(row["exchange"]),
        sector=_text(row["sector"]),
        industry=_text(row["industry"]),
        country=_text(row["country"]),
        currency=_text(row["currency"]),
        lot_size=_optional_number(row.get("lot_size")),
        tick_size=_optional_number(row.get("tick_size")),
        point_value=_optional_number(row.get("point_value")),
        is_active=bool(row.get("is_active", True)),
        valid_from=_text(row["valid_from"]),
        valid_to=_optional_text(row.get("valid_to")),
        source_id=SOURCE_ID,
    )
    mapping = SymbolMappingRecord(
        mapping_id=_stable_id("mapping", row, fixture_path),
        source_id=SOURCE_ID,
        asset_id=_text(row["asset_id"]),
        asset_class=asset_class,
        source_symbol=_text(row["source_symbol"]),
        canonical_symbol=_text(row["symbol"]),
        valid_from=_text(row["valid_from"]),
        valid_to=_optional_text(row.get("valid_to")),
        mapping_status="active",
    )
    records: list[object] = [industry_status, industry_metadata, instrument, mapping]
    if asset_class == "nse_equity_derivative":
        records.append(
            ContractMetadataRecord(
                contract_id=_stable_id("contract", row, fixture_path),
                asset_id=_text(row["asset_id"]),
                source_id=SOURCE_ID,
                asset_class=asset_class,
                root=_text(row["root"]),
                expiry=_text(row["expiry"]),
                instrument_type=_text(row["instrument_type"]),
                roll_rule=_text(row["roll_rule"]),
                continuous_contract_method=_text(row["continuous_contract_method"]),
                volume_oi_filter=_text(row["volume_oi_filter"]),
                near_contract_policy=_text(row["near_contract_policy"]),
                source_symbol=_text(row["source_symbol"]),
                canonical_symbol=_text(row["symbol"]),
                valid_from=_text(row["valid_from"]),
                valid_to=_optional_text(row.get("valid_to")),
            )
        )
    return tuple(records)


def _duplicate_timestamps(records: list[CanonicalOHLCVRecord]) -> int:
    timestamps = [record.timestamp for record in records]
    return len(timestamps) - len(set(timestamps))


def _require_fields(row: dict[str, Any], required: tuple[str, ...]) -> None:
    missing = [field for field in required if field not in row or row[field] in (None, "")]
    if missing:
        raise ValueError(f"missing required NSE fields: {', '.join(sorted(missing))}")


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


def _optional_number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _timestamp_date(row: dict[str, Any]) -> str:
    timestamp = _text(row["timestamp"])
    return timestamp[:10]


def _now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat()
