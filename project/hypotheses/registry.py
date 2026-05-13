from __future__ import annotations

from project.common.models import (
    HypothesisDefinition,
    StrategySpec,
    strategy_spec_missing_fields,
    strategy_spec_sequence_parameter,
)


VALID_STATUSES = {"draft", "testing", "active", "deprecated", "archived"}


class HypothesisRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, HypothesisDefinition] = {}
        self._signal_map: dict[str, tuple[str, ...]] = {}
        self._strategy_specs: dict[str, StrategySpec] = {}

    def register(self, definition: HypothesisDefinition, signal_types: tuple[str, ...]) -> None:
        if definition.status not in VALID_STATUSES:
            raise ValueError("invalid hypothesis status")
        existing = self._definitions.get(definition.hypothesis_id)
        if existing and existing.version >= definition.version:
            raise ValueError("hypothesis updates must increase version")
        if not signal_types:
            raise ValueError("hypothesis must declare signal dependencies")
        self._definitions[definition.hypothesis_id] = definition
        self._signal_map[definition.hypothesis_id] = tuple(sorted(signal_types))

    def activate(
        self,
        definition: HypothesisDefinition,
        signal_types: tuple[str, ...],
        strategy_spec: StrategySpec,
    ) -> None:
        self._validate_strategy_spec(definition, signal_types, strategy_spec)
        self.register(definition, signal_types)
        self._strategy_specs[definition.hypothesis_id] = strategy_spec

    def active(self) -> tuple[HypothesisDefinition, ...]:
        return tuple(
            definition
            for definition in sorted(self._definitions.values(), key=lambda item: item.hypothesis_id)
            if definition.status == "active"
        )

    def required_signals(self, hypothesis_id: str) -> tuple[str, ...]:
        return self._signal_map[hypothesis_id]

    def get_definition(self, hypothesis_id: str) -> HypothesisDefinition | None:
        return self._definitions.get(hypothesis_id)

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
        required_signals = tuple(
            sorted(strategy_spec_sequence_parameter(strategy_spec, "required_signals"))
        )
        expected_failures = strategy_spec_sequence_parameter(
            strategy_spec,
            "expected_failure_modes",
        )
        if not expected_failures:
            raise ValueError("strategy spec expected_failure_modes must not be empty")
        if required_signals != tuple(sorted(signal_types)):
            raise ValueError(
                "strategy spec required_signals must match registration dependencies"
            )
