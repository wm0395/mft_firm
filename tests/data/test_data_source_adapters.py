from __future__ import annotations

import pytest

from project.data_sources.adapters import load_source_sample
from project.data_sources.common import load_json_fixture
from project.data_sources.nse.adapter import FIXTURE_PATH as NSE_FIXTURE_PATH
from project.data_sources.nse.parser import parse_sample_payload as parse_nse_sample


@pytest.mark.parametrize(
    ("source_id", "asset_class", "expected_canonical_count", "expected_metadata_count"),
    [
        ("nse_official_reports", "indian_equity_cash", 1, 4),
        ("mcx_official_bhavcopy", "mcx_commodity_future", 1, 4),
        ("fred_api", "macro_series", 2, 2),
    ],
)
def test_prototype_source_adapters_load_fixture_backed_samples(
    source_id: str,
    asset_class: str,
    expected_canonical_count: int,
    expected_metadata_count: int,
) -> None:
    sample = load_source_sample(source_id, asset_class)

    assert sample.source_id == source_id
    assert sample.asset_class == asset_class
    assert len(sample.canonical_records) == expected_canonical_count
    assert len(sample.metadata_records) == expected_metadata_count
    assert sample.quality_report.status == "needs_review"
    assert sample.raw_file.source_id == source_id
    assert sample.raw_file.asset_class == asset_class

    if source_id == "fred_api":
        assert sample.canonical_records[0].symbol == "DGS10"
        assert sample.canonical_records[0].value == 4.31
    else:
        assert sample.canonical_records[0].vwap is not None
        assert sample.metadata_records[0].point_in_time_status == "available"


def test_nse_parser_rejects_missing_required_fields() -> None:
    payload = load_json_fixture(NSE_FIXTURE_PATH)
    payload["records"][0].pop("vwap")

    with pytest.raises(ValueError, match="missing required NSE fields"):
        parse_nse_sample(
            payload,
            NSE_FIXTURE_PATH,
            NSE_FIXTURE_PATH.read_text(encoding="utf-8"),
            "indian_equity_cash",
        )
