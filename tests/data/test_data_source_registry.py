from __future__ import annotations

from pathlib import Path

from project.data_sources.registry import load_source_registry_file
from project.data_sources.validation import validate_source_registry


def test_committed_source_registry_is_valid_and_explicit() -> None:
    registry_path = Path(__file__).resolve().parents[2] / "research" / "data_sources" / "source_registry.yaml"

    registry = load_source_registry_file(registry_path)
    validation = validate_source_registry(registry)

    assert registry.registry_name == "source_registry"
    assert validation.is_valid
    assert validation.source_count == 7
    assert validation.duplicate_source_ids == ()
    assert any("license status is unknown" in warning for warning in validation.warnings)
    assert any("adapter is prototype" in warning for warning in validation.warnings)
    assert registry.sources[0].access_method == "download"
    assert registry.sources[3].access_method == "api"
    assert registry.sources[5].free_or_paid == "mixed"
    assert registry.sources[0].adapter_status == "prototype"
    assert registry.sources[1].adapter_status == "prototype"
    assert registry.sources[3].adapter_status == "prototype"
