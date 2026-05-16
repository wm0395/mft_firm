from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from project.common.models import (
    HypothesisDefinition,
    StrategySpec,
    strategy_spec_missing_fields,
    strategy_spec_sequence_parameter,
)
from project.hypotheses.interface import Hypothesis
from project.hypotheses.ma_crossover import MACrossoverHypothesis
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis


VALID_STATUSES = {"draft", "testing", "active", "deprecated", "archived"}
VALID_EXPLAINABILITY_LEVELS = {"full", "partial", "opaque"}
REQUIRED_DEFINITION_FIELDS = {
    "required_signals",
    "direction_policy",
    "horizon",
    "thesis",
    "failure_modes",
    "evidence_standard",
}


@dataclass(frozen=True)
class HypothesisCatalogEntry:
    hypothesis: Hypothesis
    definition: HypothesisDefinition
    required_signals: tuple[str, ...]


def default_hypothesis_catalog() -> tuple[HypothesisCatalogEntry, ...]:
    return (
        HypothesisCatalogEntry(
            hypothesis=RSIMeanReversionHypothesis(),
            definition=RSIMeanReversionHypothesis.definition,
            required_signals=("rsi_14",),
        ),
        HypothesisCatalogEntry(
            hypothesis=MACrossoverHypothesis(),
            definition=MACrossoverHypothesis.definition,
            required_signals=("ma_5", "ma_20"),
        ),
    )


def get_hypothesis_implementation(hypothesis_id: str) -> Hypothesis | None:
    for entry in default_hypothesis_catalog():
        if entry.definition.hypothesis_id == hypothesis_id:
            return entry.hypothesis
    return None


def list_hypotheses() -> tuple[HypothesisDefinition, ...]:
    return tuple(
        sorted(
            (entry.definition for entry in default_hypothesis_catalog()),
            key=lambda item: (item.hypothesis_id, item.version),
        )
    )


def get_hypothesis(hypothesis_id: str) -> HypothesisDefinition | None:
    for definition in list_hypotheses():
        if definition.hypothesis_id == hypothesis_id:
            return definition
    return None


def active_hypotheses() -> tuple[Hypothesis, ...]:
    return research_hypotheses()


def research_hypotheses(
    include_testing: bool = False,
    include_draft: bool = False,
) -> tuple[Hypothesis, ...]:
    allowed = {"active"}
    if include_testing:
        allowed.add("testing")
    if include_draft:
        allowed.add("draft")
    return tuple(
        entry.hypothesis
        for entry in default_hypothesis_catalog()
        if entry.definition.status in allowed
    )


def validate_hypothesis_definition(
    definition: HypothesisDefinition,
    registered_signal_types: tuple[str, ...] | None = None,
    strategy_spec: StrategySpec | None = None,
) -> tuple[str, ...]:
    errors: list[str] = []
    if not definition.hypothesis_id.startswith("hypothesis:"):
        errors.append("invalid_hypothesis_id")
    if definition.version < 1:
        errors.append("invalid_hypothesis_version")
    if definition.status not in VALID_STATUSES:
        errors.append("invalid_hypothesis_status")
    if definition.explainability_level not in VALID_EXPLAINABILITY_LEVELS:
        errors.append("invalid_explainability_level")
    if not isinstance(definition.definition, dict):
        errors.append("invalid_definition_structure")
        return tuple(errors)
    errors.extend(_definition_field_errors(definition.definition))
    required_signals = _definition_required_signals(definition.definition, errors)
    if required_signals is not None:
        duplicate_signals = sorted(
            {signal for signal in required_signals if required_signals.count(signal) > 1}
        )
        if duplicate_signals:
            errors.append("duplicate_required_signals")
        if registered_signal_types is not None:
            missing = [signal for signal in required_signals if signal not in registered_signal_types]
            if missing:
                errors.append("unregistered_required_signals: " + ", ".join(missing))
    if strategy_spec is not None:
        errors.extend(strategy_spec_missing_fields(strategy_spec))
        if strategy_spec.hypothesis_id != definition.hypothesis_id:
            errors.append("strategy_spec_hypothesis_id_mismatch")
        if strategy_spec.hypothesis_version != definition.version:
            errors.append("strategy_spec_version_mismatch")
        try:
            strategy_required_signals = strategy_spec_sequence_parameter(
                strategy_spec,
                "required_signals",
            )
        except ValueError as error:
            errors.append(str(error))
        else:
            if required_signals is not None and tuple(sorted(strategy_required_signals)) != tuple(sorted(required_signals)):
                errors.append("strategy_spec_required_signals_mismatch")
        try:
            strategy_spec_sequence_parameter(strategy_spec, "expected_failure_modes")
        except ValueError as error:
            errors.append(str(error))
    try:
        import json

        json.dumps(definition.definition, sort_keys=True)
    except (TypeError, ValueError):
        errors.append("non_deterministic_definition_structure")
    return tuple(dict.fromkeys(errors))


def hypothesis_summary(definition: HypothesisDefinition) -> dict[str, Any]:
    payload = dict(definition.definition)
    payload.update(
        {
            "hypothesis_id": definition.hypothesis_id,
            "name": definition.name,
            "version": definition.version,
            "status": definition.status,
            "explainability_level": definition.explainability_level,
            "required_signals": _definition_required_signals(definition.definition, []),
        }
    )
    return payload


def _definition_field_errors(definition: dict[str, Any]) -> list[str]:
    missing = sorted(REQUIRED_DEFINITION_FIELDS - set(definition))
    if missing:
        return ["missing_definition_fields: " + ", ".join(missing)]
    return []


def _definition_required_signals(
    definition: dict[str, Any],
    errors: list[str],
) -> tuple[str, ...] | None:
    value = definition.get("required_signals")
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    errors.append("invalid_required_signals")
    return None
