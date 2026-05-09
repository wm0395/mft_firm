from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class VolatilityRegime:
    state: Literal["low", "normal", "high", "extreme"]
    realized_volatility: float
    percentile_rank: float

@dataclass(frozen=True)
class TrendRegime:
    state: Literal["strong_bull", "weak_bull", "sideways", "weak_bear", "strong_bear"]
    slope: float
    strength: float

@dataclass(frozen=True)
class LiquidityRegime:
    state: Literal["low", "normal", "high"]
    volume_ma_ratio: float
    spread_bps: float

@dataclass(frozen=True)
class MomentumRegime:
    state: Literal["overbought", "neutral", "oversold"]
    rsi_value: float
    momentum_score: float

@dataclass(frozen=True)
class MarketRegimeSnapshot:
    timestamp: str
    asset_id: str
    volatility: VolatilityRegime
    trend: TrendRegime
    liquidity: LiquidityRegime
    momentum: MomentumRegime
