from __future__ import annotations

from pathlib import Path
from typing import Any

from project.cli.context import CLIContext
from project.cli.errors import CliError, CommandOutcome
from project.data_sources.adapters import load_source_sample
from project.data_sources.registry import load_source_registry_file
from project.data_sources.validation import validate_source_registry, validate_source_registry_entry
from project.data_sources.common import sample_payload


def list_data_sources(context: CLIContext) -> CommandOutcome:
    registry = _load_registry()
    payload = {
        "registry_name": registry.registry_name,
        "registry_version": registry.registry_version,
        "source_count": len(registry.sources),
        "sources": [_source_payload(source) for source in registry.sources],
    }
    return CommandOutcome(payload, status="ok")


def show_data_source(context: CLIContext, source_id: str) -> CommandOutcome:
    registry = _load_registry()
    source = _source_by_id(registry, source_id)
    validation = validate_source_registry_entry(source)
    payload = {
        "source": _source_payload(source),
        "validation": _validation_payload(validation),
    }
    return CommandOutcome(payload, status="ok" if validation.is_valid else "warn")


def validate_data_source(context: CLIContext, source_id: str) -> CommandOutcome:
    registry = _load_registry()
    source = _source_by_id(registry, source_id)
    validation = validate_source_registry_entry(source)
    return CommandOutcome(_validation_payload(validation), status="ok" if validation.is_valid else "warn")


def ingest_source_sample(
    context: CLIContext,
    source_id: str,
    asset_class: str,
) -> CommandOutcome:
    registry = _load_registry()
    source = _source_by_id(registry, source_id)
    if asset_class not in source.asset_classes:
        raise CliError(
            f"asset class {asset_class} is not supported by {source_id}",
            why="Source sample ingestion must remain constrained to the declared asset classes.",
            next_action="Choose one of the declared asset classes.",
            command=f"mft show-data-source {source_id}",
        )
    if source.adapter_status == "not_started":
        return CommandOutcome(
            {
                "source": _source_payload(source),
                "asset_class": asset_class,
                "status": "blocked",
                "reason": "adapter prototype not started",
            },
            status="blocked",
            exit_code=1,
        )
    try:
        sample = load_source_sample(source_id, asset_class)
    except ValueError as error:
        raise CliError(
            str(error),
            why="The prototype adapter could not normalize the requested sample.",
            next_action="Use one of the source's declared asset classes.",
            command=f"mft show-data-source {source_id}",
        ) from error
    return CommandOutcome(
        {
            "source": _source_payload(source),
            "asset_class": asset_class,
            "status": "ok",
            "sample": sample_payload(sample),
            "record_count": len(sample.canonical_records),
            "metadata_record_count": len(sample.metadata_records),
        },
        status="ok",
    )


def data_source_quality_report(context: CLIContext, source_id: str) -> CommandOutcome:
    registry = _load_registry()
    source = _source_by_id(registry, source_id)
    registry_validation = validate_source_registry(registry)
    validation = validate_source_registry_entry(source)
    sample_report = None
    sample_asset_class = None
    if source.adapter_status in {"prototype", "validated", "production"}:
        sample_asset_class = source.asset_classes[0]
        try:
            sample = load_source_sample(source_id, sample_asset_class)
        except ValueError as error:
            raise CliError(
                str(error),
                why="The quality report depends on the prototype sample fixture.",
                next_action="Review the committed source fixture for the requested asset class.",
                command=f"mft ingest-source-sample {source_id} --asset-class {sample_asset_class}",
            ) from error
        sample_report = sample_payload(sample)
    payload = {
        "source": _source_payload(source),
        "validation": _validation_payload(validation),
        "registry_validation": {
            "registry_name": registry_validation.registry_name,
            "registry_version": registry_validation.registry_version,
            "is_valid": registry_validation.is_valid,
            "errors": registry_validation.errors,
            "warnings": registry_validation.warnings,
        },
        "quality_status": source.data_quality_status,
        "sample_asset_class": sample_asset_class,
        "sample_report": sample_report,
    }
    return CommandOutcome(payload, status="ok" if validation.is_valid else "warn")


def _load_registry():
    return load_source_registry_file(_repo_root() / "research" / "data_sources" / "source_registry.yaml")


def _source_by_id(registry, source_id: str):
    for source in registry.sources:
        if source.source_id == source_id:
            return source
    raise CliError(
        f"source_id not found: {source_id}",
        why="The requested source must exist in the committed registry.",
        next_action="List available data sources.",
        command="mft list-data-sources",
    )


def _source_payload(source) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "name": source.name,
        "base_url": source.base_url,
        "asset_classes": source.asset_classes,
        "expected_fields": source.expected_fields,
        "frequency": source.frequency,
        "history_depth": source.history_depth,
        "access_method": source.access_method,
        "free_or_paid": source.free_or_paid,
        "license_status": source.license_status,
        "adapter_status": source.adapter_status,
        "data_quality_status": source.data_quality_status,
        "allowed_use": source.allowed_use,
        "rate_limit_notes": source.rate_limit_notes,
        "freshness": source.freshness,
        "reliability_rating": source.reliability_rating,
        "notes": source.notes,
        "owner_role": source.owner_role,
    }


def _validation_payload(validation) -> dict[str, Any]:
    return {
        "source_id": validation.source_id,
        "name": validation.name,
        "is_valid": validation.is_valid,
        "errors": validation.errors,
        "warnings": validation.warnings,
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
