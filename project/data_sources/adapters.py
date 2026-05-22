from __future__ import annotations

from project.data_sources.common import SourceSampleResult
from project.data_sources.fred import load_sample as load_fred_sample
from project.data_sources.mcx import load_sample as load_mcx_sample
from project.data_sources.nse import load_sample as load_nse_sample

PROTOTYPE_SOURCE_IDS = (
    "nse_official_reports",
    "mcx_official_bhavcopy",
    "fred_api",
)


def load_source_sample(source_id: str, asset_class: str) -> SourceSampleResult:
    if source_id == "nse_official_reports":
        return load_nse_sample(asset_class)
    if source_id == "mcx_official_bhavcopy":
        return load_mcx_sample(asset_class)
    if source_id == "fred_api":
        return load_fred_sample(asset_class)
    raise ValueError(f"no prototype adapter available for {source_id}")
