from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from project.alpha_math.market_structure import gap_pressure
from project.alpha_math.ohlcv import (
    SeriesOrFrame,
    average_true_range,
    close_location_value,
)


@dataclass(frozen=True)
class OpeningGapMetrics:
    gap: SeriesOrFrame
    gap_pct: SeriesOrFrame
    gap_atr: SeriesOrFrame
    fill_ratio: SeriesOrFrame
    close_location: SeriesOrFrame
    continuation_score: SeriesOrFrame


@dataclass(frozen=True)
class OpeningGapRegime:
    metrics: OpeningGapMetrics
    bullish_gap: SeriesOrFrame
    bearish_gap: SeriesOrFrame
    gap_filled: SeriesOrFrame
    gap_faded: SeriesOrFrame
    gap_continuation: SeriesOrFrame
    gap_exhaustion: SeriesOrFrame


def opening_gap_metrics(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    atr_period: int = 14,
) -> OpeningGapMetrics:
    pressure = gap_pressure(open_, high, low, close)
    gap = pressure.gap
    gap_abs = gap.abs().replace(0.0, np.nan)
    previous_close = close.shift(1)
    gap_pct = gap.div(previous_close.replace(0.0, np.nan))
    gap_atr = gap_abs.div(average_true_range(high, low, close, atr_period))
    close_location = close_location_value(high, low, close)
    continuation_score = _continuation_score(open_, close, gap, gap_abs)
    return OpeningGapMetrics(
        gap=gap,
        gap_pct=gap_pct,
        gap_atr=gap_atr,
        fill_ratio=pressure.fill_ratio,
        close_location=close_location,
        continuation_score=continuation_score,
    )


def opening_gap_regime(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    atr_period: int = 14,
    min_gap_atr: float = 0.5,
    continuation_threshold: float = 0.5,
    exhaustion_threshold: float = 1.0,
) -> OpeningGapRegime:
    metrics = opening_gap_metrics(open_, high, low, close, atr_period)
    bullish_gap = metrics.gap.gt(0.0)
    bearish_gap = metrics.gap.lt(0.0)
    gap_filled = gap_pressure(open_, high, low, close).filled
    gap_faded = _gap_faded(close, close.shift(1), bullish_gap, bearish_gap)
    gap_continuation = _gap_continuation(
        metrics,
        min_gap_atr,
        continuation_threshold,
        gap_filled,
    )
    gap_exhaustion = gap_filled & metrics.gap_atr.ge(exhaustion_threshold)
    return OpeningGapRegime(
        metrics=metrics,
        bullish_gap=bullish_gap,
        bearish_gap=bearish_gap,
        gap_filled=gap_filled,
        gap_faded=gap_faded,
        gap_continuation=gap_continuation,
        gap_exhaustion=gap_exhaustion,
    )


def _continuation_score(
    open_: SeriesOrFrame,
    close: SeriesOrFrame,
    gap: SeriesOrFrame,
    gap_abs: SeriesOrFrame,
) -> SeriesOrFrame:
    signed_extension = (close - open_) * np.sign(gap)
    return signed_extension.div(gap_abs).fillna(0.0)


def _gap_faded(
    close: SeriesOrFrame,
    previous_close: SeriesOrFrame,
    bullish_gap: SeriesOrFrame,
    bearish_gap: SeriesOrFrame,
) -> SeriesOrFrame:
    return (bullish_gap & close.lt(previous_close)) | (
        bearish_gap & close.gt(previous_close)
    )


def _gap_continuation(
    metrics: OpeningGapMetrics,
    min_gap_atr: float,
    continuation_threshold: float,
    gap_filled: SeriesOrFrame,
) -> SeriesOrFrame:
    strong_gap = metrics.gap_atr.ge(min_gap_atr)
    holding_structure = metrics.fill_ratio.le(0.75)
    directional_follow_through = metrics.continuation_score.ge(
        continuation_threshold
    )
    return strong_gap & holding_structure & directional_follow_through & (~gap_filled)
