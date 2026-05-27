from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from project.alpha_math.ohlcv import SeriesOrFrame, ema


@dataclass(frozen=True)
class AccumulationDistributionResult:
    adl: SeriesOrFrame
    money_flow_multiplier: SeriesOrFrame
    money_flow_volume: SeriesOrFrame


@dataclass(frozen=True)
class ChaikinMoneyFlowResult:
    cmf: SeriesOrFrame
    money_flow_volume: SeriesOrFrame


@dataclass(frozen=True)
class ForceIndexResult:
    force_index: SeriesOrFrame
    smoothed_force_index: SeriesOrFrame


@dataclass(frozen=True)
class EaseOfMovementResult:
    eom: SeriesOrFrame
    smoothed_eom: SeriesOrFrame


@dataclass(frozen=True)
class PriceVolumeTrendResult:
    pvt: SeriesOrFrame


@dataclass(frozen=True)
class ChaikinOscillatorResult:
    oscillator: SeriesOrFrame
    fast_ema: SeriesOrFrame
    slow_ema: SeriesOrFrame


def accumulation_distribution_line(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
) -> AccumulationDistributionResult:
    spread = (high - low).replace(0.0, np.nan)
    multiplier = (((close - low) - (high - close)) / spread).where(~spread.eq(0.0), 0.0)
    money_flow_volume = multiplier * volume
    return AccumulationDistributionResult(
        adl=money_flow_volume.cumsum(),
        money_flow_multiplier=multiplier,
        money_flow_volume=money_flow_volume,
    )


def chaikin_money_flow(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    period: int = 20,
) -> ChaikinMoneyFlowResult:
    adl = accumulation_distribution_line(high, low, close, volume)
    numerator = adl.money_flow_volume.rolling(period, min_periods=period).sum()
    denominator = volume.rolling(period, min_periods=period).sum().replace(0.0, np.nan)
    return ChaikinMoneyFlowResult(
        cmf=numerator.div(denominator),
        money_flow_volume=adl.money_flow_volume,
    )


def force_index(
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    period: int = 13,
) -> ForceIndexResult:
    raw = close.diff().mul(volume)
    return ForceIndexResult(force_index=raw, smoothed_force_index=ema(raw, period))


def ease_of_movement(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    volume: SeriesOrFrame,
    period: int = 14,
) -> EaseOfMovementResult:
    midpoint = (high + low) / 2.0
    distance = midpoint.diff()
    box_ratio = volume.div((high - low).replace(0.0, np.nan))
    eom = distance.div(box_ratio.replace(0.0, np.nan))
    return EaseOfMovementResult(eom=eom, smoothed_eom=ema(eom, period))


def price_volume_trend(
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
) -> PriceVolumeTrendResult:
    pvt = (close.pct_change(fill_method=None).mul(volume)).fillna(0.0).cumsum()
    return PriceVolumeTrendResult(pvt=pvt)


def chaikin_oscillator(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    fast: int = 3,
    slow: int = 10,
) -> ChaikinOscillatorResult:
    adl = accumulation_distribution_line(high, low, close, volume).adl
    fast_ema = ema(adl, fast)
    slow_ema = ema(adl, slow)
    return ChaikinOscillatorResult(
        oscillator=fast_ema - slow_ema,
        fast_ema=fast_ema,
        slow_ema=slow_ema,
    )
