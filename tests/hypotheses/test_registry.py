from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from project.common.models import HypothesisDefinition
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.hypotheses.catalog import (
    default_hypothesis_catalog,
    list_hypotheses,
)
from project.hypotheses.lifecycle import promote_definition, validate_transition
from project.hypotheses.ma_crossover import MACrossoverHypothesis
from project.hypotheses.registry import validate_hypothesis_definition
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.signals.registry import DEFAULT_SIGNAL_DEFINITIONS
from project.cli_utils import ensure_default_hypothesis_catalog


def test_default_catalog_definitions_are_valid() -> None:
    signal_types = tuple(definition.signal_type for definition in DEFAULT_SIGNAL_DEFINITIONS)
    for entry in default_hypothesis_catalog():
        errors = validate_hypothesis_definition(entry.definition, signal_types)
        assert errors == ()


def test_validate_hypothesis_definition_rejects_missing_required_signals() -> None:
    definition = HypothesisDefinition(
        hypothesis_id="hypothesis:test",
        name="Test",
        version=1,
        definition={
            "direction_policy": "long_short_or_flat",
            "horizon": "5d",
            "thesis": "Test thesis",
            "failure_modes": ("trend",),
            "evidence_standard": {"min_total_trades": 1},
        },
        explainability_level="full",
        status="draft",
    )

    errors = validate_hypothesis_definition(definition, ("rsi_14",))

    assert "missing_definition_fields: required_signals" in errors


def test_validate_hypothesis_definition_rejects_unregistered_signals() -> None:
    definition = replace(RSIMeanReversionHypothesis.definition, status="testing")

    errors = validate_hypothesis_definition(definition, ("ma_5",))

    assert any(error.startswith("unregistered_required_signals") for error in errors)


def test_lifecycle_transitions_are_enforced() -> None:
    draft = replace(MACrossoverHypothesis.definition, status="draft")

    promoted = promote_definition(draft, "testing")
    assert promoted.status == "testing"

    with pytest.raises(ValueError):
        validate_transition("active", "testing")

    forced = promote_definition(draft, "active", force=True)
    assert forced.status == "active"


def test_default_catalog_persistence_is_idempotent(tmp_path: Path) -> None:
    repository = DataRepository(DuckDBAccess(tmp_path / "mft.duckdb"))
    repository.initialize()

    ensure_default_hypothesis_catalog(repository)
    ensure_default_hypothesis_catalog(repository)

    hypotheses = repository.get_hypotheses()
    signal_defs = repository.get_signal_definitions()
    signal_map_rows = sum(
        len(repository.get_hypothesis_signal_map(definition.hypothesis_id))
        for definition in hypotheses
    )

    assert len(hypotheses) == len(list_hypotheses())
    assert len(signal_defs) == len(DEFAULT_SIGNAL_DEFINITIONS)
    assert signal_map_rows == sum(len(entry.required_signals) for entry in default_hypothesis_catalog())
