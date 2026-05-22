from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AccessMethod = Literal["api", "download", "file", "manual", "web", "mixed"]
AdapterStatus = Literal["not_started", "prototype", "validated", "production"]
CostModel = Literal["free", "paid", "mixed", "unknown"]
DataQualityStatus = Literal[
    "unknown",
    "not_assessed",
    "unverified",
    "needs_review",
    "validated",
    "degraded",
    "blocked",
]
LicenseStatus = Literal["unknown", "approved", "rejected", "restricted"]
ReliabilityRating = Literal["unknown", "low", "medium", "high"]


@dataclass(frozen=True)
class SourceRegistryEntry:
    source_id: str
    name: str
    base_url: str
    asset_classes: tuple[str, ...]
    expected_fields: tuple[str, ...]
    frequency: str
    history_depth: str
    access_method: AccessMethod
    free_or_paid: CostModel
    license_status: LicenseStatus
    adapter_status: AdapterStatus
    data_quality_status: DataQualityStatus
    allowed_use: str
    rate_limit_notes: str
    freshness: str
    reliability_rating: ReliabilityRating
    notes: str
    owner_role: str


@dataclass(frozen=True)
class SourceRegistry:
    sources: tuple[SourceRegistryEntry, ...]
    registry_name: str = "source_registry"
    registry_version: int = 1
    description: str = ""
