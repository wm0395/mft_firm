from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
import json
from typing import Any, cast

from project.data_sources.models import (
    AccessMethod,
    AdapterStatus,
    CostModel,
    DataQualityStatus,
    LicenseStatus,
    ReliabilityRating,
    SourceRegistry,
    SourceRegistryEntry,
)

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - dependency is declared with the project
    yaml = None  # type: ignore[assignment]

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


def load_source_registry(
    source: SourceRegistry | Mapping[str, Any] | Sequence[Any] | str | Path,
) -> SourceRegistry:
    if isinstance(source, SourceRegistry):
        return source
    payload = _load_payload(source)
    return _registry_from_payload(payload)


def load_source_registry_text(text: str) -> SourceRegistry:
    return _registry_from_payload(_load_text_payload(text))


def load_source_registry_file(path: str | Path) -> SourceRegistry:
    return _registry_from_payload(_load_text_payload(Path(path).read_text(encoding="utf-8")))


def _load_payload(source: Mapping[str, Any] | Sequence[Any] | str | Path) -> Any:
    if isinstance(source, Mapping) or _is_sequence_payload(source):
        return source
    if isinstance(source, Path):
        return _load_text_payload(source.read_text(encoding="utf-8"))
    text = str(source)
    if not _looks_like_payload_text(text) and Path(text).exists():
        text = Path(text).read_text(encoding="utf-8")
    return _load_text_payload(text)


def _load_text_payload(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if yaml is None:
            raise ValueError("YAML support is unavailable") from None
        return yaml.safe_load(text)


def _registry_from_payload(payload: Any) -> SourceRegistry:
    if isinstance(payload, SourceRegistry):
        return payload
    if isinstance(payload, Mapping):
        return _registry_from_mapping(payload)
    if _is_sequence_payload(payload):
        return SourceRegistry(sources=tuple(_entry_from_mapping(item) for item in payload))
    raise ValueError("registry payload must be a mapping or sequence")


def _registry_from_mapping(mapping: Mapping[str, Any]) -> SourceRegistry:
    entries = mapping.get("sources") or mapping.get("entries")
    if entries is None:
        raise ValueError("registry mapping must include sources or entries")
    return SourceRegistry(
        registry_name=_text(mapping.get("registry_name", "source_registry")),
        registry_version=_int(mapping.get("registry_version", 1)),
        description=str(mapping.get("description", "")).strip(),
        sources=tuple(_entry_from_mapping(item) for item in entries),
    )


def _entry_from_mapping(mapping: Any) -> SourceRegistryEntry:
    if not isinstance(mapping, Mapping):
        raise ValueError("registry entry must be a mapping")
    return SourceRegistryEntry(
        source_id=_text(mapping.get("source_id")),
        name=_text(mapping.get("name")),
        base_url=_text(mapping.get("base_url")),
        asset_classes=_text_tuple(mapping.get("asset_classes"), "asset_classes"),
        expected_fields=_text_tuple(mapping.get("expected_fields"), "expected_fields"),
        frequency=_text(mapping.get("frequency")),
        history_depth=_text(mapping.get("history_depth")),
        access_method=cast(
            AccessMethod,
            _choice(
                mapping.get("access_method"),
                "access_method",
                ALLOWED_ACCESS_METHODS,
            ),
        ),
        free_or_paid=cast(
            CostModel,
            _choice(
                mapping.get("free_or_paid"),
                "free_or_paid",
                ALLOWED_COST_MODELS,
            ),
        ),
        license_status=cast(
            LicenseStatus,
            _choice(
                mapping.get("license_status"),
                "license_status",
                ALLOWED_LICENSE_STATUSES,
            ),
        ),
        adapter_status=cast(
            AdapterStatus,
            _choice(
                mapping.get("adapter_status"),
                "adapter_status",
                ALLOWED_ADAPTER_STATUSES,
            ),
        ),
        data_quality_status=cast(
            DataQualityStatus,
            _choice(
                mapping.get("data_quality_status"),
                "data_quality_status",
                ALLOWED_DATA_QUALITY_STATUSES,
            ),
        ),
        allowed_use=_text(mapping.get("allowed_use")),
        rate_limit_notes=_text(mapping.get("rate_limit_notes")),
        freshness=_text(mapping.get("freshness")),
        reliability_rating=cast(
            ReliabilityRating,
            _choice(
                mapping.get("reliability_rating"),
                "reliability_rating",
                ALLOWED_RELIABILITY_RATINGS,
            ),
        ),
        notes=_text(mapping.get("notes")),
        owner_role=_text(mapping.get("owner_role")),
    )


def _text(value: Any) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError("registry text field must be non-empty")
    return text


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("registry_version must be an integer") from exc


def _text_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{field_name} must be a sequence")
    items = tuple(str(item).strip() for item in value)
    if not items or any(not item for item in items):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return items


def _choice(value: Any, field_name: str, allowed: set[str]) -> str:
    text = _text(value)
    if text not in allowed:
        raise ValueError(f"{field_name} has unsupported value: {text}")
    return text


def _is_sequence_payload(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _looks_like_payload_text(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("{") or stripped.startswith("[") or "\n" in text
