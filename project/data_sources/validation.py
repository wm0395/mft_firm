from __future__ import annotations

from dataclasses import dataclass
import re

from project.data_sources.models import SourceRegistry, SourceRegistryEntry

SOURCE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
ALLOWED_ACCESS_METHODS = {"api", "download", "file", "manual", "web", "mixed"}
ALLOWED_ADAPTER_STATUSES = {"not_started", "prototype", "validated", "production"}
ALLOWED_COST_MODELS = {"free", "paid", "mixed", "unknown"}
ALLOWED_LICENSE_STATUSES = {"unknown", "approved", "rejected", "restricted"}
ALLOWED_DATA_QUALITY_STATUSES = {
    "unknown",
    "not_assessed",
    "unverified",
    "needs_review",
    "validated",
    "degraded",
    "blocked",
}
ALLOWED_RELIABILITY_RATINGS = {"unknown", "low", "medium", "high"}


@dataclass(frozen=True)
class SourceEntryValidationResult:
    source_id: str
    name: str
    is_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class SourceRegistryValidationResult:
    registry_name: str
    registry_version: int
    is_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    source_count: int
    source_ids: tuple[str, ...]
    duplicate_source_ids: tuple[str, ...]
    entry_results: tuple[SourceEntryValidationResult, ...]


def validate_source_registry(registry: SourceRegistry) -> SourceRegistryValidationResult:
    duplicate_source_ids = _duplicate_source_ids(registry.sources)
    entry_results = tuple(
        validate_source_registry_entry(entry, duplicate_source_ids)
        for entry in registry.sources
    )
    errors, warnings = _registry_messages(registry, entry_results)
    return SourceRegistryValidationResult(
        registry_name=registry.registry_name,
        registry_version=registry.registry_version,
        is_valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        source_count=len(registry.sources),
        source_ids=tuple(entry.source_id for entry in registry.sources),
        duplicate_source_ids=duplicate_source_ids,
        entry_results=entry_results,
    )


def validate_source_registry_entry(
    entry: SourceRegistryEntry,
    duplicate_source_ids: tuple[str, ...] = (),
) -> SourceEntryValidationResult:
    errors = _entry_errors(entry, duplicate_source_ids)
    warnings = _entry_warnings(entry)
    return SourceEntryValidationResult(
        source_id=entry.source_id,
        name=entry.name,
        is_valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _registry_messages(
    registry: SourceRegistry,
    entry_results: tuple[SourceEntryValidationResult, ...],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not registry.registry_name.strip():
        errors.append("registry_name must be non-empty")
    if registry.registry_version <= 0:
        errors.append("registry_version must be positive")
    if not registry.sources:
        errors.append("registry sources must not be empty")
    if entry_results:
        errors.extend(
            f"{result.source_id}: {error}"
            for result in entry_results
            for error in result.errors
        )
        warnings.extend(
            f"{result.source_id}: {warning}"
            for result in entry_results
            for warning in result.warnings
        )
    return errors, warnings


def _entry_errors(
    entry: SourceRegistryEntry,
    duplicate_source_ids: tuple[str, ...],
) -> list[str]:
    errors: list[str] = []
    _append_text_error(errors, entry.source_id, "source_id", pattern=True)
    _append_text_error(errors, entry.name, "name")
    _append_text_error(errors, entry.base_url, "base_url", http_url=True)
    _append_text_tuple_error(errors, entry.asset_classes, "asset_classes")
    _append_text_tuple_error(errors, entry.expected_fields, "expected_fields")
    _append_text_error(errors, entry.frequency, "frequency")
    _append_text_error(errors, entry.history_depth, "history_depth")
    _append_choice_error(errors, entry.access_method, "access_method", ALLOWED_ACCESS_METHODS)
    _append_choice_error(errors, entry.free_or_paid, "free_or_paid", ALLOWED_COST_MODELS)
    _append_choice_error(errors, entry.license_status, "license_status", ALLOWED_LICENSE_STATUSES)
    _append_choice_error(errors, entry.adapter_status, "adapter_status", ALLOWED_ADAPTER_STATUSES)
    _append_choice_error(
        errors,
        entry.data_quality_status,
        "data_quality_status",
        ALLOWED_DATA_QUALITY_STATUSES,
    )
    _append_text_error(errors, entry.allowed_use, "allowed_use")
    _append_text_error(errors, entry.rate_limit_notes, "rate_limit_notes")
    _append_text_error(errors, entry.freshness, "freshness")
    _append_choice_error(
        errors,
        entry.reliability_rating,
        "reliability_rating",
        ALLOWED_RELIABILITY_RATINGS,
    )
    _append_text_error(errors, entry.notes, "notes")
    _append_text_error(errors, entry.owner_role, "owner_role")
    if entry.source_id in duplicate_source_ids:
        errors.append(f"duplicate source_id: {entry.source_id}")
    return errors


def _entry_warnings(entry: SourceRegistryEntry) -> list[str]:
    warnings: list[str] = []
    if entry.license_status == "unknown":
        warnings.append("license status is unknown")
    if entry.adapter_status == "prototype":
        warnings.append("adapter is prototype")
    if entry.adapter_status == "not_started":
        warnings.append("adapter has not started")
    if entry.data_quality_status in {"unknown", "not_assessed", "unverified", "needs_review"}:
        warnings.append(f"data quality status is {entry.data_quality_status}")
    if entry.reliability_rating == "unknown":
        warnings.append("reliability rating is unknown")
    return warnings


def _duplicate_source_ids(entries: tuple[SourceRegistryEntry, ...]) -> tuple[str, ...]:
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.source_id] = counts.get(entry.source_id, 0) + 1
    return tuple(source_id for source_id, count in counts.items() if count > 1)


def _append_text_error(
    errors: list[str],
    value: str,
    field_name: str,
    *,
    pattern: bool = False,
    http_url: bool = False,
) -> None:
    text = value.strip()
    if not text:
        errors.append(f"{field_name} must be non-empty")
        return
    if pattern and SOURCE_ID_PATTERN.fullmatch(text) is None:
        errors.append(f"{field_name} must use lowercase snake_case")
    if http_url and not (text.startswith("http://") or text.startswith("https://")):
        errors.append(f"{field_name} must be an http(s) URL")


def _append_text_tuple_error(
    errors: list[str],
    values: tuple[str, ...],
    field_name: str,
) -> None:
    if not values:
        errors.append(f"{field_name} must not be empty")
        return
    if any(not str(value).strip() for value in values):
        errors.append(f"{field_name} must not contain blank values")


def _append_choice_error(
    errors: list[str],
    value: str,
    field_name: str,
    allowed: set[str],
) -> None:
    if not str(value).strip():
        errors.append(f"{field_name} must be non-empty")
        return
    if value not in allowed:
        errors.append(f"{field_name} has unsupported value: {value}")
