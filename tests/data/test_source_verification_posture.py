from __future__ import annotations

from pathlib import Path

from project.data_sources.registry import load_source_registry_file


def test_source_registry_records_conservative_verified_posture() -> None:
    registry_path = (
        Path(__file__).resolve().parents[2]
        / "research"
        / "data_sources"
        / "source_registry.yaml"
    )
    registry = load_source_registry_file(registry_path)
    license_statuses = {
        source.source_id: source.license_status for source in registry.sources
    }
    adapter_statuses = {
        source.source_id: source.adapter_status for source in registry.sources
    }

    assert license_statuses["nse_official_reports"] == "restricted"
    assert license_statuses["mcx_official_bhavcopy"] == "restricted"
    assert license_statuses["fred_api"] == "restricted"
    assert license_statuses["alpha_vantage_free_tier"] == "restricted"
    assert license_statuses["stooq_free_daily"] == "unknown"
    assert license_statuses["rbi_dbie_data_pages"] == "unknown"
    assert license_statuses["yfinance_convenience"] == "unknown"
    assert adapter_statuses["nse_official_reports"] == "prototype"
    assert adapter_statuses["mcx_official_bhavcopy"] == "prototype"
    assert adapter_statuses["fred_api"] == "prototype"
    assert all(
        source.adapter_status in {"not_started", "prototype"}
        for source in registry.sources
    )
    assert all(source.adapter_status != "production" for source in registry.sources)
    assert any(source.adapter_status == "prototype" for source in registry.sources)
    assert any(source.license_status == "restricted" for source in registry.sources)
    assert any(source.license_status == "unknown" for source in registry.sources)
