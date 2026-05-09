from __future__ import annotations
import math
import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from project.regimes.models import (
    VolatilityRegime, TrendRegime, LiquidityRegime, MomentumRegime, MarketRegimeSnapshot
)

class RegimeEngine:
    def __init__(self, window: int = 20):
        self.window = window

    def compute_regime(
        self, 
        asset_id: str, 
        timestamp: str, 
        market_data: tuple[tuple[datetime, float, float, float, float, float], ...]
    ) -> MarketRegimeSnapshot:
        """
        Computes the market regime based on a window of historical OHLCV data.
        market_data: tuple of (timestamp, open, high, low, close, volume)
        """
        if len(market_data) < self.window:
            raise ValueError(f"Insufficient data for regime computation. Need {self.window} bars.")

        # Extract closing prices and volumes
        closes = [row[4] for row in market_data[-self.window:]]
        volumes = [row[5] for row in market_data[-self.window:]]
        
        # 1. Volatility Regime
        vol_regime = self._compute_volatility(closes)
        
        # 2. Trend Regime
        trend_regime = self._compute_trend(closes)
        
        # 3. Liquidity Regime
        liq_regime = self._compute_liquidity(volumes)
        
        # 4. Momentum Regime
        mom_regime = self._compute_momentum(closes)
        
        return MarketRegimeSnapshot(
            timestamp=timestamp,
            asset_id=asset_id,
            volatility=vol_regime,
            trend=trend_regime,
            liquidity=liq_regime,
            momentum=mom_regime
        )

    def _compute_volatility(self, prices: list[float]) -> VolatilityRegime:
        returns = []
        for i in range(1, len(prices)):
            returns.append(math.log(prices[i] / prices[i-1]))
        
        realized_vol = statistics.stdev(returns) if len(returns) > 1 else 0.0
        
        # Simplified state mapping based on fixed thresholds for this implementation
        # In a production system, these would be based on historical percentiles
        if realized_vol < 0.001: state = "low"
        elif realized_vol < 0.003: state = "normal"
        elif realized_vol < 0.006: state = "high"
        else: state = "extreme"
        
        return VolatilityRegime(
            state=state,
            realized_volatility=realized_vol,
            percentile_rank=0.0 # Placeholder as we don't have global distribution
        )

    def _compute_trend(self, prices: list[float]) -> TrendRegime:
        # Simple linear regression slope
        n = len(prices)
        x = list(range(n))
        y = prices
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)
        
        denominator = (n * sum_xx - sum_x**2)
        slope = (n * sum_xy - sum_x * sum_y) / denominator if denominator != 0 else 0.0
        
        # Strength based on R-squared (simplified)
        strength = abs(slope) / (statistics.stdev(prices) / n) if statistics.stdev(prices) != 0 else 0.0
        
        if slope > 0.01 * prices[-1]: state = "strong_bull" if strength > 2 else "weak_bull"
        elif slope < -0.01 * prices[-1]: state = "strong_bear" if strength > 2 else "weak_bear"
        else: state = "sideways"
        
        return TrendRegime(state=state, slope=slope, strength=strength)

    def _compute_liquidity(self, volumes: list[float]) -> LiquidityRegime:
        current_vol = volumes[-1]
        avg_vol = statistics.mean(volumes[:-1]) if len(volumes) > 1 else current_vol
        
        ratio = current_vol / avg_vol if avg_vol != 0 else 1.0
        
        if ratio < 0.5: state = "low"
        elif ratio < 1.5: state = "normal"
        else: state = "high"
        
        return LiquidityRegime(
            state=state,
            volume_ma_ratio=ratio,
            spread_bps=0.0 # Not available in raw OHLCV
        )

    def _compute_momentum(self, prices: list[float]) -> MomentumRegime:
        # Simple RSI implementation
        deltas = []
        for i in range(1, len(prices)):
            deltas.append(prices[i] - prices[i-1])
            
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = statistics.mean(gains) if gains else 0.0
        avg_loss = statistics.mean(losses) if losses else 0.0
        
        if avg_loss == 0:
            rsi = 100.0 if avg_gain > 0 else 50.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
            
        if rsi > 70: state = "overbought"
        elif rsi < 30: state = "oversold"
        else: state = "neutral"
        
        return MomentumRegime(
            state=state,
            rsi_value=rsi,
            momentum_score=rsi - 50.0
        )
