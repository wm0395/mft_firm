from __future__ import annotations

from typing import cast

from project.common.models import (
    Direction,
    HypothesisDefinition,
    HypothesisOutput,
    Signal,
    StrategySpec,
    utc_now_iso,
)
from project.common.explainability import create_ma_crossover_explanation


class MACrossoverHypothesis:
    """Simple moving average crossover hypothesis."""
    definition = HypothesisDefinition(
        hypothesis_id="hypothesis:ma_crossover",
        name="MA Crossover",
        version=1,
        definition={
            "fast_ma": "ma_5",
            "slow_ma": "ma_20",
            "horizon": "5d",
            "bar_timeframe": "1d",
            "intended_universe": "indian_daily_index_basket",
            "required_signals": ("ma_5", "ma_20"),
        },
        explainability_level="full",
        status="active",
    )

    @classmethod
    def strategy_spec(cls, universe_id: str) -> StrategySpec:
        return StrategySpec(
            strategy_spec_id="strategy_spec:ma_crossover:indian_indexes:v1",
            universe_id=universe_id,
            hypothesis_id=cls.definition.hypothesis_id,
            hypothesis_version=cls.definition.version,
            name="Daily Indian Index MA Crossover",
            parameters=(
                ("thesis", "Follow short-term daily trend continuation on liquid indexes."),
                ("bar_timeframe", "1d"),
                ("holding_horizon", "5d"),
                ("required_signals", ("ma_5", "ma_20")),
                ("expected_failure_modes", ("range_bound_whipsaw", "gap_reversal")),
                ("evidence_standard", "dataset_snapshot_plus_replay_backtest"),
                ("intended_universe", ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY")),
            ),
        )

    def evaluate(self, asset_id: str, signals: tuple[Signal, ...]) -> HypothesisOutput:
        snapshot = {signal.signal_type: signal.value for signal in signals}
        ma_5 = _required_signal(snapshot, "ma_5")
        ma_20 = _required_signal(snapshot, "ma_20")
        direction = _crossover_direction(ma_5, ma_20)
        confidence = _crossover_confidence(ma_5, ma_20, direction)
        explanation_tree = create_ma_crossover_explanation(
            ma_fast=ma_5,
            ma_slow=ma_20,
            direction=direction,
            confidence=confidence,
            hypothesis_id=self.definition.hypothesis_id,
            version=self.definition.version,
            asset_id=asset_id,
            horizon="5d",
            timestamp=utc_now_iso(),
        )
        return HypothesisOutput(
            hypothesis_id=self.definition.hypothesis_id,
            version=self.definition.version,
            asset_id=asset_id,
            direction=cast(Direction, direction),
            horizon="5d",
            confidence=round(min(confidence, 1.0), 4),
            signals_snapshot=snapshot,
            explanation=explanation_tree.to_dict(),
        )


def _required_signal(snapshot: dict[str, float], signal_type: str) -> float:
    if signal_type not in snapshot:
        raise ValueError(f"{signal_type} signal is required")
    return snapshot[signal_type]


def _crossover_direction(ma_fast: float, ma_slow: float) -> Direction:
    if ma_fast > ma_slow:
        return "long"
    if ma_fast < ma_slow:
        return "short"
    return "flat"


def _crossover_confidence(ma_fast: float, ma_slow: float, direction: Direction) -> float:
    if direction == "long" and ma_slow != 0:
        return min((ma_fast - ma_slow) / ma_slow, 1.0)
    if direction == "short" and ma_fast != 0:
        return min((ma_slow - ma_fast) / ma_fast, 1.0)
    return 0.0
