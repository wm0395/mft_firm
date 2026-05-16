from __future__ import annotations

import json
from typing import Any

from project.common.models import (
    HypothesisDefinition,
    HypothesisStatus,
    StrategySpec,
    strategy_spec_missing_fields,
    strategy_spec_sequence_parameter,
)
from project.hypotheses.lifecycle import promote_definition


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


class HypothesisRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, HypothesisDefinition] = {}
        self._signal_map: dict[str, tuple[str, ...]] = {}
        self._strategy_specs: dict[str, StrategySpec] = {}

    def register(
        self,
        definition: HypothesisDefinition,
        signal_types: tuple[str, ...],
    ) -> None:
        if definition.status not in VALID_STATUSES:
            raise ValueError("invalid hypothesis status")
        if not signal_types:
            raise ValueError("hypothesis must declare signal dependencies")
        existing = self._definitions.get(definition.hypothesis_id)
        if existing and existing.version >= definition.version:
            raise ValueError("hypothesis updates must increase version")
        self._definitions[definition.hypothesis_id] = definition
        self._signal_map[definition.hypothesis_id] = tuple(signal_types)

    def activate(
        self,
        definition: HypothesisDefinition,
        signal_types: tuple[str, ...],
        strategy_spec: StrategySpec,
    ) -> None:
        self._validate_strategy_spec(definition, signal_types, strategy_spec)
        self.register(definition, signal_types)
        self._strategy_specs[definition.hypothesis_id] = strategy_spec

    def promote(self, hypothesis_id: str, to_status: HypothesisStatus, force: bool = False) -> HypothesisDefinition:
        definition = self.get_hypothesis(hypothesis_id)
        if definition is None:
            raise ValueError(f"unknown hypothesis: {hypothesis_id}")
        promoted = promote_definition(definition, to_status, force=force)
        self._definitions[hypothesis_id] = promoted
        return promoted

    def list_hypotheses(self) -> tuple[HypothesisDefinition, ...]:
        return tuple(sorted(self._definitions.values(), key=lambda item: (item.hypothesis_id, item.version)))

    def get_hypothesis(self, hypothesis_id: str) -> HypothesisDefinition | None:
        return self._definitions.get(hypothesis_id)

    def get_definition(self, hypothesis_id: str) -> HypothesisDefinition | None:
        return self.get_hypothesis(hypothesis_id)

    def active_hypotheses(self) -> tuple[HypothesisDefinition, ...]:
        return self.research_hypotheses()

    def research_hypotheses(
        self,
        include_testing: bool = False,
        include_draft: bool = False,
    ) -> tuple[HypothesisDefinition, ...]:
        allowed = {"active"}
        if include_testing:
            allowed.add("testing")
        if include_draft:
            allowed.add("draft")
        return tuple(
            definition
            for definition in self.list_hypotheses()
            if definition.status in allowed
        )

    def required_signals(self, hypothesis_id: str) -> tuple[str, ...]:
        return self._signal_map[hypothesis_id]

    def get_strategy_spec(self, hypothesis_id: str) -> StrategySpec | None:
        return self._strategy_specs.get(hypothesis_id)

    def _validate_strategy_spec(
        self,
        definition: HypothesisDefinition,
        signal_types: tuple[str, ...],
        strategy_spec: StrategySpec,
    ) -> None:
        if definition.status != "active":
            msg = "strategy spec activation is only required for active hypotheses"
            raise ValueError(msg)
        if strategy_spec.hypothesis_id != definition.hypothesis_id:
            raise ValueError("strategy spec must match hypothesis id")
        if strategy_spec.hypothesis_version != definition.version:
            raise ValueError("strategy spec must match hypothesis version")
        missing = strategy_spec_missing_fields(strategy_spec)
        if missing:
            raise ValueError("strategy spec missing fields: " + ", ".join(missing))
        required_signals = strategy_spec_sequence_parameter(strategy_spec, "required_signals")
        expected_failures = strategy_spec_sequence_parameter(
            strategy_spec,
            "expected_failure_modes",
        )
        if not expected_failures:
            raise ValueError("strategy spec expected_failure_modes must not be empty")
        if tuple(sorted(required_signals)) != tuple(sorted(signal_types)):
            raise ValueError(
                "strategy spec required_signals must match registration dependencies"
            )


def list_hypotheses(registry: HypothesisRegistry) -> tuple[HypothesisDefinition, ...]:
    return registry.list_hypotheses()


def get_hypothesis(
    registry: HypothesisRegistry,
    hypothesis_id: str,
) -> HypothesisDefinition | None:
    return registry.get_hypothesis(hypothesis_id)


def active_hypotheses(registry: HypothesisRegistry) -> tuple[HypothesisDefinition, ...]:
    return registry.active_hypotheses()


def research_hypotheses(
    registry: HypothesisRegistry,
    include_testing: bool = False,
    include_draft: bool = False,
) -> tuple[HypothesisDefinition, ...]:
    return registry.research_hypotheses(include_testing, include_draft)


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
        duplicate_signals = sorted({signal for signal in required_signals if required_signals.count(signal) > 1})
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
            strategy_required_signals = strategy_spec_sequence_parameter(strategy_spec, "required_signals")
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
        json.dumps(definition.definition, sort_keys=True)
    except (TypeError, ValueError):
        errors.append("non_deterministic_definition_structure")
    return tuple(dict.fromkeys(errors))


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
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    errors.append("invalid_required_signals")
    return None
