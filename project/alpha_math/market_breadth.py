from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

import numpy as np
import pandas as pd

from project.alpha_math.ohlcv import SeriesOrFrame
from project.alpha_math.price_action import bollinger_squeeze
from project.alpha_math.relative_strength import relative_strength_ratio


@dataclass(frozen=True)
class MarketBreadthMetrics:
    advance_decline_line: pd.Series
    advance_decline_ratio: pd.Series
    above_moving_average_ratio: pd.Series
    new_high_ratio: pd.Series
    new_low_ratio: pd.Series
    breadth_score: pd.Series
    bullish: pd.Series
    bearish: pd.Series


@dataclass(frozen=True)
class RelativeRotationMetrics:
    rs_ratio: SeriesOrFrame
    rs_momentum: SeriesOrFrame
    score: SeriesOrFrame
    leading: SeriesOrFrame
    improving: SeriesOrFrame
    lagging: SeriesOrFrame
    weakening: SeriesOrFrame


@dataclass(frozen=True)
class BreadthThrustMetrics:
    advance_decline_ratio: pd.Series
    thrust_average: pd.Series
    washout: pd.Series
    thrust: pd.Series
    signal: pd.Series
    score: pd.Series


@dataclass(frozen=True)
class BreadthThrustComposite:
    universe_thrust_average: pd.DataFrame
    universe_signal: pd.DataFrame
    universe_score: pd.DataFrame
    composite_score: pd.Series
    bullish: pd.Series
    bearish: pd.Series


@dataclass(frozen=True)
class BreadthDispersionMetrics:
    universe_breadth_score: pd.DataFrame
    breadth_mean: pd.Series
    breadth_std: pd.Series
    participation_decay: pd.Series
    dispersion_score: pd.Series
    bullish: pd.Series
    bearish: pd.Series


@dataclass(frozen=True)
class BreadthVolatilityRegime:
    breadth_thrust: BreadthThrustComposite
    squeeze: SeriesOrFrame
    regime_score: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame


@dataclass(frozen=True)
class NestedUniverseBreadthMetrics:
    universe_breadth_score: pd.DataFrame
    universe_member_count: pd.Series
    coverage_weight: pd.Series
    normalized_breadth_score: pd.DataFrame
    raw_composite_score: pd.Series
    normalized_composite_score: pd.Series
    expansion_factor: pd.Series


def market_breadth_metrics(
    close: SeriesOrFrame,
    moving_average_window: int = 50,
    high_low_window: int = 252,
    score_threshold: float = 0.25,
) -> MarketBreadthMetrics:
    frame = _frame_like(close)
    deltas = frame.diff()
    advancers = deltas.gt(0.0).sum(axis=1)
    decliners = deltas.lt(0.0).sum(axis=1)
    total = (advancers + decliners).replace(0.0, np.nan)
    advance_decline_ratio = advancers.div(total).fillna(0.5)
    above_ma_ratio = _ratio_above_moving_average(frame, moving_average_window)
    new_high_ratio, new_low_ratio = _extreme_ratios(frame, high_low_window)
    breadth_score = _breadth_score(
        advance_decline_ratio,
        above_ma_ratio,
        new_high_ratio,
        new_low_ratio,
    )
    return MarketBreadthMetrics(
        advance_decline_line=(advancers - decliners).cumsum(),
        advance_decline_ratio=advance_decline_ratio,
        above_moving_average_ratio=above_ma_ratio,
        new_high_ratio=new_high_ratio,
        new_low_ratio=new_low_ratio,
        breadth_score=breadth_score,
        bullish=breadth_score.ge(score_threshold),
        bearish=breadth_score.le(-score_threshold),
    )


def relative_rotation_metrics(
    close: SeriesOrFrame,
    benchmark_close: SeriesOrFrame,
    momentum_window: int = 14,
) -> RelativeRotationMetrics:
    rs_ratio = relative_strength_ratio(close, benchmark_close)
    rs_momentum = rs_ratio.diff(momentum_window)
    score = rs_ratio.sub(1.0).fillna(0.0) + rs_momentum.fillna(0.0)
    return RelativeRotationMetrics(
        rs_ratio=rs_ratio,
        rs_momentum=rs_momentum,
        score=score,
        leading=rs_ratio.gt(1.0) & rs_momentum.gt(0.0),
        improving=rs_ratio.le(1.0) & rs_momentum.gt(0.0),
        lagging=rs_ratio.le(1.0) & rs_momentum.le(0.0),
        weakening=rs_ratio.gt(1.0) & rs_momentum.le(0.0),
    )


def breadth_thrust_metrics(
    close: SeriesOrFrame,
    thrust_window: int = 10,
    washout_window: int = 10,
    washout_threshold: float = 0.4,
    thrust_threshold: float = 0.615,
) -> BreadthThrustMetrics:
    breadth = market_breadth_metrics(close).advance_decline_ratio
    thrust_average = breadth.rolling(thrust_window, min_periods=thrust_window).mean()
    washout = thrust_average.rolling(washout_window, min_periods=washout_window).min().lt(
        washout_threshold
    )
    thrust = thrust_average.ge(thrust_threshold)
    score = _thrust_score(thrust_average, washout_threshold, thrust_threshold)
    return BreadthThrustMetrics(
        advance_decline_ratio=breadth,
        thrust_average=thrust_average,
        washout=washout,
        thrust=thrust,
        signal=washout & thrust,
        score=score,
    )


def breadth_thrust_composite(
    universes: Mapping[str, SeriesOrFrame],
    thrust_window: int = 10,
    washout_window: int = 10,
    washout_threshold: float = 0.4,
    thrust_threshold: float = 0.615,
    bullish_threshold: float = 0.5,
    bearish_threshold: float = -0.5,
) -> BreadthThrustComposite:
    metrics = {
        name: breadth_thrust_metrics(
            close,
            thrust_window=thrust_window,
            washout_window=washout_window,
            washout_threshold=washout_threshold,
            thrust_threshold=thrust_threshold,
        )
        for name, close in universes.items()
    }
    thrust_average = pd.DataFrame(
        {name: metric.thrust_average for name, metric in metrics.items()}
    )
    signal = pd.DataFrame({name: metric.signal for name, metric in metrics.items()})
    score = pd.DataFrame({name: metric.score for name, metric in metrics.items()})
    composite_score = score.fillna(0.0).mean(axis=1)
    return BreadthThrustComposite(
        universe_thrust_average=thrust_average,
        universe_signal=signal,
        universe_score=score,
        composite_score=composite_score,
        bullish=composite_score.ge(bullish_threshold),
        bearish=composite_score.le(bearish_threshold),
    )


def breadth_dispersion_metrics(
    universes: Mapping[str, SeriesOrFrame],
    short_window: int = 5,
    long_window: int = 20,
    dispersion_threshold: float = 0.1,
) -> BreadthDispersionMetrics:
    universe_scores = pd.DataFrame(
        {
            name: market_breadth_metrics(close).breadth_score
            for name, close in universes.items()
        }
    )
    breadth_mean = universe_scores.mean(axis=1).fillna(0.0)
    breadth_std = universe_scores.std(axis=1, ddof=0).fillna(0.0)
    short_participation = breadth_mean.rolling(short_window, min_periods=short_window).mean()
    long_participation = breadth_mean.rolling(long_window, min_periods=long_window).mean()
    participation_decay = long_participation - short_participation
    dispersion_score = breadth_mean - breadth_std - participation_decay.fillna(0.0)
    return BreadthDispersionMetrics(
        universe_breadth_score=universe_scores,
        breadth_mean=breadth_mean,
        breadth_std=breadth_std,
        participation_decay=participation_decay,
        dispersion_score=dispersion_score,
        bullish=breadth_mean.ge(dispersion_threshold) & participation_decay.le(0.0),
        bearish=breadth_mean.le(-dispersion_threshold) & participation_decay.ge(0.0),
    )


def breadth_thrust_volatility_regime(
    benchmark_close: SeriesOrFrame,
    universes: Mapping[str, SeriesOrFrame],
    thrust_window: int = 10,
    washout_window: int = 10,
    squeeze_window: int = 20,
    squeeze_lookback: int = 20,
    washout_threshold: float = 0.4,
    thrust_threshold: float = 0.615,
) -> BreadthVolatilityRegime:
    breadth = breadth_thrust_composite(
        universes,
        thrust_window=thrust_window,
        washout_window=washout_window,
        washout_threshold=washout_threshold,
        thrust_threshold=thrust_threshold,
    )
    squeeze = bollinger_squeeze(
        benchmark_close,
        period=squeeze_window,
        lookback=squeeze_lookback,
    )
    regime_score = breadth.composite_score + squeeze.astype(float).fillna(0.0)
    bullish = breadth.bullish & squeeze
    bearish = breadth.bearish & ~squeeze
    return BreadthVolatilityRegime(
        breadth_thrust=breadth,
        squeeze=squeeze,
        regime_score=regime_score,
        bullish=bullish,
        bearish=bearish,
    )


def nested_universe_breadth_metrics(
    universes: Mapping[str, SeriesOrFrame],
    moving_average_window: int = 50,
    high_low_window: int = 252,
    coverage_power: float = 0.5,
) -> NestedUniverseBreadthMetrics:
    if not universes:
        raise ValueError("universes must not be empty")
    if coverage_power < 0.0:
        raise ValueError("coverage_power must be non-negative")
    universe_scores = pd.DataFrame(
        {
            name: market_breadth_metrics(
                close,
                moving_average_window=moving_average_window,
                high_low_window=high_low_window,
            ).breadth_score
            for name, close in universes.items()
        }
    )
    member_count = pd.Series(
        {name: _member_count(close) for name, close in universes.items()},
        dtype=float,
    )
    coverage_weight = member_count.div(member_count.max()).pow(coverage_power)
    normalized_score = universe_scores.mul(coverage_weight, axis=1)
    raw_composite = universe_scores.mean(axis=1).fillna(0.0)
    normalized_composite = normalized_score.mean(axis=1).fillna(0.0)
    expansion_factor = normalized_composite.div(raw_composite.replace(0.0, np.nan))
    return NestedUniverseBreadthMetrics(
        universe_breadth_score=universe_scores,
        universe_member_count=member_count,
        coverage_weight=coverage_weight,
        normalized_breadth_score=normalized_score,
        raw_composite_score=raw_composite,
        normalized_composite_score=normalized_composite,
        expansion_factor=expansion_factor.replace([np.inf, -np.inf], np.nan).fillna(1.0),
    )


def _breadth_score(
    advance_decline_ratio: pd.Series,
    above_ma_ratio: pd.Series,
    new_high_ratio: pd.Series,
    new_low_ratio: pd.Series,
) -> pd.Series:
    ad_component = (advance_decline_ratio - 0.5) * 2.0
    ma_component = (above_ma_ratio - 0.5) * 2.0
    extreme_component = new_high_ratio - new_low_ratio
    return (0.45 * ad_component) + (0.45 * ma_component) + (0.10 * extreme_component)


def _ratio_above_moving_average(
    frame: pd.DataFrame,
    moving_average_window: int,
) -> pd.Series:
    moving_average = frame.rolling(moving_average_window, min_periods=moving_average_window).mean()
    return frame.gt(moving_average).mean(axis=1)


def _extreme_ratios(
    frame: pd.DataFrame,
    high_low_window: int,
) -> tuple[pd.Series, pd.Series]:
    rolling_high = frame.rolling(high_low_window, min_periods=high_low_window).max()
    rolling_low = frame.rolling(high_low_window, min_periods=high_low_window).min()
    return frame.ge(rolling_high).mean(axis=1), frame.le(rolling_low).mean(axis=1)


def _thrust_score(
    thrust_average: pd.Series,
    washout_threshold: float,
    thrust_threshold: float,
) -> pd.Series:
    spread = thrust_threshold - washout_threshold
    if spread <= 0.0:
        raise ValueError("thrust_threshold must exceed washout_threshold")
    return (
        thrust_average.sub(washout_threshold).div(spread).clip(-1.0, 1.0)
    )


def _frame_like(values: SeriesOrFrame) -> pd.DataFrame:
    if isinstance(values, pd.DataFrame):
        return values
    return values.to_frame()


def _member_count(values: SeriesOrFrame) -> int:
    return int(_frame_like(values).shape[1])
