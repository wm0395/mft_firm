from __future__ import annotations

from project.common.models import HypothesisDefinition


VALID_STATUSES = {"draft", "testing", "active", "deprecated", "archived"}


class HypothesisRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, HypothesisDefinition] = {}
        self._signal_map: dict[str, tuple[str, ...]] = {}

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
