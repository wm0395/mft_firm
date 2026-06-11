from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from research.projects.price_action_strategy_lab.backtest_modes import BacktestResult


@dataclass(frozen=True)
class SelectorDecision:
    selector: str
    chosen_name: str
    confidence: float
    abstain: bool
    reason_code: str


@dataclass(frozen=True)
class SelectorSpec:
    name: str
    description: str
    builder: Callable[[tuple[BacktestResult, ...]], SelectorDecision]


def selector_spec(
    name: str,
    description: str,
) -> Callable[
    [Callable[[tuple[BacktestResult, ...]], SelectorDecision]],
    SelectorSpec,
]:
    def decorate(
        builder: Callable[[tuple[BacktestResult, ...]], SelectorDecision],
    ) -> SelectorSpec:
        return SelectorSpec(name=name, description=description, builder=builder)

    return decorate


def selector_registry() -> tuple[SelectorSpec, ...]:
    from research.projects.price_action_strategy_lab.selectors import SELECTORS

    names = tuple(spec.name for spec in SELECTORS)
    if len(names) != len(set(names)):
        raise ValueError("selector names must be unique")
    return SELECTORS
