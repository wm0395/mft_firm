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
from project.common.explainability import create_rsi_explanation


class RSIMeanReversionHypothesis:
    definition = HypothesisDefinition(
        hypothesis_id="hypothesis:rsi_mean_reversion",
        name="RSI mean reversion",
        version=1,
        definition={
            "signal": "rsi_14",
            "long_below": 30.0,
            "short_above": 70.0,
            "direction_policy": "long_short_or_flat",
            "horizon": "10d",
            "bar_timeframe": "1d",
            "intended_universe": "indian_daily_index_basket",
            "required_signals": ("rsi_14",),
            "thesis": "Fade daily index extremes when RSI stretches away from neutral.",
            "failure_modes": ("trend_breakout", "earnings_gap", "macro_shock"),
            "evidence_standard": {
                "min_dataset_snapshots": 1,
                "min_total_trades": 20,
                "required_metrics": ("win_rate", "max_drawdown", "total_return_pct"),
            },
        },
        explainability_level="full",
        status="active",
    )

    @classmethod
    def strategy_spec(cls, universe_id: str) -> StrategySpec:
        return StrategySpec(
            strategy_spec_id="strategy_spec:rsi_mean_reversion:indian_indexes:v1",
            universe_id=universe_id,
            hypothesis_id=cls.definition.hypothesis_id,
            hypothesis_version=cls.definition.version,
            name="Daily Indian Index RSI Mean Reversion",
            parameters=(
                ("thesis", "Fade oversold and overbought daily index extremes."),
                ("bar_timeframe", "1d"),
                ("holding_horizon", "10d"),
                ("required_signals", ("rsi_14",)),
                ("expected_failure_modes", ("trend_breakout", "regime_shift")),
                ("evidence_standard", "dataset_snapshot_plus_replay_backtest"),
                ("intended_universe", ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY")),
            ),
        )

    def evaluate(self, asset_id: str, signals: tuple[Signal, ...]) -> HypothesisOutput:
        snapshot = {signal.signal_type: signal.value for signal in signals}
        if "rsi_14" not in snapshot:
            raise ValueError("rsi_14 signal is required")
        rsi_value = snapshot["rsi_14"]
        direction: Direction
        if rsi_value <= 30.0:
            direction = "long"
            confidence = (30.0 - rsi_value) / 30.0
        elif rsi_value >= 70.0:
            direction = "short"
            confidence = (rsi_value - 70.0) / 30.0
        else:
            direction = "flat"
            confidence = 0.0
        
        # Generate enhanced explanation
        explanation_tree = create_rsi_explanation(
            rsi_value=rsi_value,
            direction=direction,
            confidence=confidence,
            hypothesis_id=self.definition.hypothesis_id,
            version=self.definition.version,
            asset_id=asset_id,
            horizon="10d",
            timestamp=utc_now_iso()
        )
        
        return HypothesisOutput(
            hypothesis_id=self.definition.hypothesis_id,
            version=self.definition.version,
            asset_id=asset_id,
            direction=cast(Direction, direction),
            horizon="10d",
            confidence=round(min(confidence, 1.0), 4),
            signals_snapshot=snapshot,
            explanation=explanation_tree.to_dict(),
        )
