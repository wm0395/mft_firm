from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from project.alpha_math.ohlcv import SeriesOrFrame, ema


@dataclass(frozen=True)
class FisherTransformResult:
    fisher: SeriesOrFrame
    value: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame


@dataclass(frozen=True)
class InverseFisherResult:
    transform: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame
    strong_bullish: SeriesOrFrame
    strong_bearish: SeriesOrFrame


@dataclass(frozen=True)
class DetrendedPriceOscillatorResult:
    dpo: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame


@dataclass(frozen=True)
class MassIndexResult:
    mass_index: SeriesOrFrame
    ratio: SeriesOrFrame
    single_ema: SeriesOrFrame
    double_ema: SeriesOrFrame
    bulge: SeriesOrFrame
    reversal_bulge: SeriesOrFrame


def fisher_transform(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    price: SeriesOrFrame | None = None,
    period: int = 10,
    value_smoothing: float = 0.33,
    fisher_smoothing: float = 0.5,
) -> FisherTransformResult:
    source = price if price is not None else (high + low) / 2.0
    if isinstance(source, pd.DataFrame):
        return _fisher_frame(high, low, source, period, value_smoothing, fisher_smoothing)
    return _fisher_series(high, low, source, period, value_smoothing, fisher_smoothing)


def inverse_fisher_transform(
    values: SeriesOrFrame,
    scale: float = 1.0,
    offset: float = 0.0,
    strong_threshold: float = 0.5,
) -> InverseFisherResult:
    transformed = np.tanh((values + offset) * scale)
    return InverseFisherResult(
        transform=transformed,
        bullish=transformed.gt(0.0),
        bearish=transformed.lt(0.0),
        strong_bullish=transformed.ge(strong_threshold),
        strong_bearish=transformed.le(-strong_threshold),
    )


def detrended_price_oscillator(
    close: SeriesOrFrame,
    period: int = 20,
    displacement: int | None = None,
) -> DetrendedPriceOscillatorResult:
    shift = displacement if displacement is not None else (period // 2) + 1
    sma = close.rolling(period, min_periods=period).mean()
    dpo = close.shift(shift) - sma
    return DetrendedPriceOscillatorResult(
        dpo=dpo,
        bullish=dpo.gt(0.0),
        bearish=dpo.lt(0.0),
    )


def mass_index(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    ema_period: int = 9,
    summation_period: int = 25,
    bulge_threshold: float = 27.0,
    trigger_threshold: float = 26.5,
) -> MassIndexResult:
    range_ = high - low
    single_ema = ema(range_, ema_period).replace(0.0, np.nan)
    double_ema = ema(single_ema, ema_period).replace(0.0, np.nan)
    ratio = single_ema.div(double_ema)
    mass = ratio.rolling(summation_period, min_periods=summation_period).sum()
    bulge = mass.ge(bulge_threshold)
    reversal_bulge = mass.shift(1).ge(bulge_threshold) & mass.lt(trigger_threshold)
    return MassIndexResult(
        mass_index=mass,
        ratio=ratio,
        single_ema=single_ema,
        double_ema=double_ema,
        bulge=bulge,
        reversal_bulge=reversal_bulge,
    )


def _fisher_series(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    price: pd.Series,
    period: int,
    value_smoothing: float,
    fisher_smoothing: float,
) -> FisherTransformResult:
    rolling_high = high.rolling(period, min_periods=period).max()
    rolling_low = low.rolling(period, min_periods=period).min()
    value = pd.Series(np.nan, index=price.index, dtype=float)
    fisher = pd.Series(np.nan, index=price.index, dtype=float)
    for idx in range(len(price)):
        if idx == 0:
            continue
        current_high = rolling_high.iloc[idx]
        current_low = rolling_low.iloc[idx]
        current_price = price.iloc[idx]
        if pd.isna(current_high) or pd.isna(current_low) or current_high == current_low:
            continue
        prior_value = 0.0 if pd.isna(value.iloc[idx - 1]) else float(value.iloc[idx - 1])
        raw = ((current_price - current_low) / (current_high - current_low)) - 0.5
        current_value = (value_smoothing * 2.0 * raw) + ((1.0 - value_smoothing) * prior_value)
        current_value = float(np.clip(current_value, -0.9999, 0.9999))
        prior_fisher = 0.0 if pd.isna(fisher.iloc[idx - 1]) else float(fisher.iloc[idx - 1])
        current_fisher = (
            fisher_smoothing
            * np.log((1.0 + current_value) / (1.0 - current_value))
            + (1.0 - fisher_smoothing) * prior_fisher
        )
        value.iloc[idx] = current_value
        fisher.iloc[idx] = current_fisher
    return FisherTransformResult(
        fisher=fisher,
        value=value,
        bullish=fisher.gt(0.0),
        bearish=fisher.lt(0.0),
    )


def _fisher_frame(
    high: pd.DataFrame,
    low: pd.DataFrame,
    price: pd.DataFrame,
    period: int,
    value_smoothing: float,
    fisher_smoothing: float,
) -> FisherTransformResult:
    fisher = pd.DataFrame(index=price.index, columns=price.columns, dtype=float)
    value = pd.DataFrame(index=price.index, columns=price.columns, dtype=float)
    for column in price.columns:
        result = _fisher_series(
            high[column],
            low[column],
            price[column],
            period,
            value_smoothing,
            fisher_smoothing,
        )
        fisher[column] = result.fisher
        value[column] = result.value
    return FisherTransformResult(
        fisher=fisher,
        value=value,
        bullish=fisher.gt(0.0),
        bearish=fisher.lt(0.0),
    )
