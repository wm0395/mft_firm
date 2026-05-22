from __future__ import annotations

from dataclasses import fields

from project.data.contract_models import (
    CanonicalOHLCVRecord,
    IndustryMetadataRecord,
    VWAPObservationRecord,
)
from project.data.schema import REQUIRED_TABLES
from project.data.schema_multi_asset import CONTRACT_SCHEMA_SQL, EXTRA_REQUIRED_TABLES


def test_multi_asset_contract_fields_are_explicit() -> None:
    vwap_field_names = {field.name for field in fields(VWAPObservationRecord)}
    industry_field_names = {field.name for field in fields(IndustryMetadataRecord)}
    canonical_field_names = {field.name for field in fields(CanonicalOHLCVRecord)}

    assert {
        "vwap_observation_id",
        "source_id",
        "asset_id",
        "symbol",
        "asset_class",
        "timestamp",
        "vwap",
        "vwap_kind",
        "vwap_method",
        "is_proxy",
        "currency",
        "raw_reference",
        "ingestion_timestamp",
    }.issubset(vwap_field_names)
    assert "vwap" in canonical_field_names
    assert {
        "industry_metadata_id",
        "source_id",
        "asset_id",
        "symbol",
        "asset_class",
        "exchange",
        "classification_scheme",
        "sector",
        "industry",
        "country",
        "as_of_date",
        "effective_from",
        "point_in_time_status",
        "raw_reference",
        "ingestion_timestamp",
    }.issubset(industry_field_names)
    assert {
        "vwap_observations",
        "industry_metadata_history",
    }.issubset(EXTRA_REQUIRED_TABLES)
    assert "vwap_observations" in " ".join(CONTRACT_SCHEMA_SQL)
    assert "industry_metadata_history" in " ".join(CONTRACT_SCHEMA_SQL)
    assert {"vwap_observations", "industry_metadata_history"}.issubset(REQUIRED_TABLES)
