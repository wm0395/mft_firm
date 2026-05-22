from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import json
from typing import Any, Iterable

from project.data.contract_models import DataQualityReportRecord, SourceRawFileRecord


@dataclass(frozen=True)
class SourceSampleResult:
    source_id: str
    asset_class: str
    canonical_records: tuple[object, ...]
    metadata_records: tuple[object, ...]
    raw_file: SourceRawFileRecord
    quality_report: DataQualityReportRecord
    warnings: tuple[str, ...] = ()


def load_json_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fixture payload must be a mapping")
    return payload


def build_raw_file_record(
    source_id: str,
    asset_class: str,
    fixture_path: Path,
    payload_text: str,
    source_url: str,
    source_date: str,
    notes: str,
) -> SourceRawFileRecord:
    checksum = sha256(payload_text.encode("utf-8")).hexdigest()
    return SourceRawFileRecord(
        raw_file_id=_stable_id("raw", source_id, asset_class, checksum),
        source_id=source_id,
        asset_id=None,
        asset_class=asset_class,
        source_url=source_url,
        file_path=fixture_path.as_posix(),
        file_format=fixture_path.suffix.lstrip(".") or "json",
        source_date=source_date,
        fetched_at=_now(),
        checksum=checksum,
        byte_size=len(payload_text.encode("utf-8")),
        freshness="prototype sample",
        notes=notes,
    )


def build_quality_report(
    source_id: str,
    asset_class: str,
    raw_file: SourceRawFileRecord,
    canonical_records: Iterable[object],
    metadata_records: Iterable[object],
    *,
    source_gap_count: int = 0,
    asset_gap_count: int = 0,
    field_gap_count: int = 0,
    duplicate_timestamp_count: int = 0,
    notes: str,
) -> DataQualityReportRecord:
    canonical_count = len(tuple(canonical_records))
    metadata_count = len(tuple(metadata_records))
    summary = {
        "asset_class": asset_class,
        "canonical_record_count": canonical_count,
        "metadata_record_count": metadata_count,
        "raw_file_id": raw_file.raw_file_id,
        "source_url": raw_file.source_url,
    }
    return DataQualityReportRecord(
        report_id=_stable_id("quality", source_id, asset_class, raw_file.checksum),
        source_id=source_id,
        asset_class=asset_class,
        dataset_snapshot_id=None,
        status="needs_review",
        source_gap_count=source_gap_count,
        asset_gap_count=asset_gap_count,
        field_gap_count=field_gap_count,
        duplicate_timestamp_count=duplicate_timestamp_count,
        generated_at=_now(),
        summary_json=json.dumps(summary, sort_keys=True),
        notes=notes,
    )


def sample_payload(result: SourceSampleResult) -> dict[str, Any]:
    return asdict(result)


def _stable_id(*parts: str) -> str:
    digest = sha256("::".join(parts).encode("utf-8")).hexdigest()[:16]
    return ":".join((parts[0], digest))


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
