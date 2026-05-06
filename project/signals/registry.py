from __future__ import annotations

from project.common.models import SignalDefinition


class SignalRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, SignalDefinition] = {}

    def register(self, definition: SignalDefinition) -> None:
        existing = self._definitions.get(definition.signal_type)
        if existing and existing.version >= definition.version:
            raise ValueError("signal updates must increase version")
        self._definitions[definition.signal_type] = definition

    def require(self, signal_type: str) -> SignalDefinition:
        try:
            return self._definitions[signal_type]
        except KeyError as error:
            raise ValueError(f"unregistered signal: {signal_type}") from error

    def list_definitions(self) -> tuple[SignalDefinition, ...]:
        return tuple(self._definitions[key] for key in sorted(self._definitions))


def default_signal_registry() -> SignalRegistry:
    registry = SignalRegistry()
    registry.register(
        SignalDefinition(
            signal_type="rsi_14",
            category="technical",
            definition="14-period relative strength index",
            dependencies=("price",),
            is_persistent=True,
            version=1,
        )
    )
    registry.register(
        SignalDefinition(
            signal_type="ma_20",
            category="technical",
            definition="20-period moving average of close",
            dependencies=("price",),
            is_persistent=True,
            version=1,
        )
    )
    registry.register(
        SignalDefinition(
            signal_type="volatility_20",
            category="technical",
            definition="20-period mean absolute close return",
            dependencies=("price",),
            is_persistent=True,
            version=1,
        )
    )
    return registry
