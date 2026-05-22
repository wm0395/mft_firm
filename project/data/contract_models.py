from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataSourceRecord:
    source_id: str
    name: str
    base_url: str
    asset_classes: tuple[str, ...]
    expected_fields: tuple[str, ...]
    frequency: str
    history_depth: str
    access_method: str
    free_or_paid: str
    license_status: str
    adapter_status: str
    data_quality_status: str
    notes: str
    owner_role: str


@dataclass(frozen=True)
class AssetClassRecord:
    asset_class_id: str
    description: str
    canonical_symbol_format: str
    source_priority_order: tuple[str, ...]
    trading_calendar: str
    price_type: str
    adjustment_policy: str
    liquidity_fields: tuple[str, ...]
    benchmark: str
    known_risks: tuple[str, ...]


@dataclass(frozen=True)
class InstrumentRecord:
    asset_id: str
    symbol: str
    source_symbol: str
    asset_class: str
    exchange: str
    sector: str
    industry: str
    country: str
    currency: str
    lot_size: float | None
    tick_size: float | None
    point_value: float | None
    is_active: bool
    valid_from: str
    valid_to: str | None
    source_id: str


@dataclass(frozen=True)
class SymbolMappingRecord:
    mapping_id: str
    source_id: str
    asset_id: str
    asset_class: str
    source_symbol: str
    canonical_symbol: str
    valid_from: str
    valid_to: str | None
    mapping_status: str


@dataclass(frozen=True)
class ContractMetadataRecord:
    contract_id: str
    asset_id: str
    source_id: str
    asset_class: str
    root: str
    expiry: str | None
    instrument_type: str
    roll_rule: str
    continuous_contract_method: str
    volume_oi_filter: str
    near_contract_policy: str
    source_symbol: str
    canonical_symbol: str
    valid_from: str
    valid_to: str | None


@dataclass(frozen=True)
class SourceRawFileRecord:
    raw_file_id: str
    source_id: str
    asset_id: str | None
    asset_class: str
    source_url: str
    file_path: str
    file_format: str
    source_date: str
    fetched_at: str
    checksum: str
    byte_size: int
    freshness: str
    notes: str


@dataclass(frozen=True)
class VWAPObservationRecord:
    vwap_observation_id: str
    source_id: str
    asset_id: str
    symbol: str
    asset_class: str
    timestamp: str
    vwap: float
    vwap_kind: str
    vwap_method: str
    is_proxy: bool
    currency: str
    raw_reference: str
    ingestion_timestamp: str


@dataclass(frozen=True)
class IndustryMetadataRecord:
    industry_metadata_id: str
    source_id: str
    asset_id: str
    symbol: str
    asset_class: str
    exchange: str
    classification_scheme: str
    sector: str
    industry: str
    sub_industry: str | None
    country: str
    as_of_date: str
    effective_from: str
    effective_to: str | None
    point_in_time_status: str
    source_snapshot_id: str | None
    raw_reference: str
    ingestion_timestamp: str


@dataclass(frozen=True)
class DataQualityReportRecord:
    report_id: str
    source_id: str
    asset_class: str
    dataset_snapshot_id: str | None
    status: str
    source_gap_count: int
    asset_gap_count: int
    field_gap_count: int
    duplicate_timestamp_count: int
    generated_at: str
    summary_json: str
    notes: str


@dataclass(frozen=True)
class MacroSeriesRecord:
    series_record_id: str
    source_id: str
    asset_id: str
    symbol: str
    asset_class: str
    timestamp: str
    value: float
    frequency: str
    unit: str
    release_date: str
    revision_flag: str
    realtime_start: str | None
    realtime_end: str | None
    raw_reference: str
    ingestion_timestamp: str


@dataclass(frozen=True)
class PointInTimeIndustryMetadataRecord:
    industry_metadata_id: str
    asset_id: str
    source_id: str
    source_symbol: str
    asset_class: str
    exchange: str
    sector: str
    industry: str
    country: str
    valid_from: str
    valid_to: str | None
    as_of_timestamp: str
    point_in_time_status: str
    notes: str


@dataclass(frozen=True)
class UniverseMembershipRecord:
    membership_id: str
    universe_id: str
    asset_id: str
    asset_class: str
    source_id: str
    valid_from: str
    valid_to: str | None
    is_member: bool
    notes: str


@dataclass(frozen=True)
class PointInTimeMetadataStatusRecord:
    status_id: str
    asset_id: str
    source_id: str
    metadata_type: str
    point_in_time_status: str
    valid_from: str
    valid_to: str | None
    notes: str


@dataclass(frozen=True)
class CanonicalOHLCVRecord:
    source_id: str
    asset_id: str
    symbol: str
    asset_class: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float | None
    adjusted_close: float | None
    turnover: float | None
    delivery_volume: float | None
    open_interest: float | None
    contract_expiry: str | None
    instrument_type: str | None
    currency: str
    raw_reference: str
    ingestion_timestamp: str
