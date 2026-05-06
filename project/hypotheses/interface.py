from __future__ import annotations

from typing import Protocol

from project.common.models import HypothesisDefinition, HypothesisOutput, Signal


class Hypothesis(Protocol):
    definition: HypothesisDefinition

    def evaluate(self, asset_id: str, signals: tuple[Signal, ...]) -> HypothesisOutput:
        """Map signals to a deterministic hypothesis output."""
