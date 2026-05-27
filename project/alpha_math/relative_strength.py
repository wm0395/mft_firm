from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

import numpy as np
import pandas as pd

from project.alpha_math.ohlcv import SeriesOrFrame, ema, relative_volume
from project.alpha_math.transforms import rank_cross_sectional, rolling_zscore


@dataclass(frozen=True)
class RelativeStrengthOverlay:
    ratio: SeriesOrFrame
    spread: SeriesOrFrame
    ratio_zscore: SeriesOrFrame
    trend: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame


@dataclass(frozen=True)
class DivergenceScores:
    price_momentum_score: SeriesOrFrame
    price_volume_score: SeriesOrFrame
    composite_score: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame


@dataclass(frozen=True)
class RelativeStrengthRanking:
    horizon_returns: pd.DataFrame
    horizon_ranks: pd.DataFrame
    composite_rank: pd.DataFrame
    leader: pd.DataFrame
    laggard: pd.DataFrame


@dataclass(frozen=True)
class HigherOrderDivergenceScores:
    factor_scores: pd.DataFrame
    composite_score: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame


def relative_strength_ratio(
    close: SeriesOrFrame,
    benchmark_close: SeriesOrFrame,
) -> SeriesOrFrame:
    return _divide_like(close, benchmark_close)


def relative_strength_spread(
    close: SeriesOrFrame,
    benchmark_close: SeriesOrFrame,
) -> SeriesOrFrame:
    return _subtract_like(close, benchmark_close)


def relative_strength_overlay(
    close: SeriesOrFrame,
    benchmark_close: SeriesOrFrame,
    trend_fast: int = 20,
    trend_slow: int = 50,
    zscore_window: int = 120,
) -> RelativeStrengthOverlay:
    ratio = relative_strength_ratio(close, benchmark_close)
    spread = relative_strength_spread(close, benchmark_close)
    trend = ema(ratio, trend_fast) - ema(ratio, trend_slow)
    ratio_zscore = rolling_zscore(ratio, zscore_window)
    bullish = trend.gt(0.0) & ratio_zscore.gt(0.0)
    bearish = trend.lt(0.0) & ratio_zscore.lt(0.0)
    return RelativeStrengthOverlay(
        ratio=ratio,
        spread=spread,
        ratio_zscore=ratio_zscore,
        trend=trend,
        bullish=bullish,
        bearish=bearish,
    )


def divergence_scores(
    close: SeriesOrFrame,
    momentum: SeriesOrFrame,
    volume: SeriesOrFrame,
    lookback: int = 20,
) -> DivergenceScores:
    price_momentum = _divergence_score(close, momentum, lookback)
    volume_signal = relative_volume(volume, lookback).fillna(1.0)
    price_volume = _divergence_score(close, volume_signal, lookback)
    composite = 0.5 * (price_momentum + price_volume)
    bullish = composite.gt(0.0)
    bearish = composite.lt(0.0)
    return DivergenceScores(
        price_momentum_score=price_momentum,
        price_volume_score=price_volume,
        composite_score=composite,
        bullish=bullish,
        bearish=bearish,
    )


def multi_horizon_relative_strength_rank(
    close: SeriesOrFrame,
    horizons: tuple[int, ...] = (1, 3, 6, 12),
    weights: tuple[float, ...] | None = None,
    benchmark_close: SeriesOrFrame | None = None,
    leader_threshold: float = 0.8,
    laggard_threshold: float = 0.5,
) -> RelativeStrengthRanking:
    close_frame = _frame_like(close)
    benchmark_frame = _frame_like(benchmark_close) if benchmark_close is not None else None
    normalized_weights = _normalize_weights(horizons, weights)
    horizon_returns: dict[str, pd.DataFrame] = {}
    horizon_ranks: dict[str, pd.DataFrame] = {}
    composite = pd.DataFrame(0.0, index=close_frame.index, columns=close_frame.columns)
    for horizon, weight in normalized_weights:
        returns = _horizon_returns(close_frame, horizon)
        if benchmark_frame is not None:
            returns = _benchmark_excess(returns, benchmark_frame, horizon)
        ranks = rank_cross_sectional(returns).fillna(0.0)
        horizon_returns[str(horizon)] = returns
        horizon_ranks[str(horizon)] = ranks
        composite = composite + (weight * ranks)
    return RelativeStrengthRanking(
        horizon_returns=_stack_horizon_frames(horizon_returns),
        horizon_ranks=_stack_horizon_frames(horizon_ranks),
        composite_rank=composite,
        leader=composite.ge(leader_threshold),
        laggard=composite.le(laggard_threshold),
    )


def higher_order_divergence_scores(
    close: SeriesOrFrame,
    factors: pd.DataFrame | Mapping[str, SeriesOrFrame],
    lookback: int = 20,
    weights: Mapping[str, float] | None = None,
) -> HigherOrderDivergenceScores:
    price = _single_series(close)
    factor_frame = _factor_frame(factors)
    factor_scores = pd.DataFrame(
        {
            column: _divergence_score(price, factor_frame[column], lookback)
            for column in factor_frame.columns
        }
    )
    composite = _weighted_factor_average(factor_scores, weights)
    bullish = composite.gt(0.0)
    bearish = composite.lt(0.0)
    return HigherOrderDivergenceScores(
        factor_scores=factor_scores,
        composite_score=composite,
        bullish=bullish,
        bearish=bearish,
    )


def _divergence_score(
    primary: SeriesOrFrame,
    secondary: SeriesOrFrame,
    lookback: int,
) -> SeriesOrFrame:
    bullish = _bullish_divergence(primary, secondary, lookback)
    bearish = _bearish_divergence(primary, secondary, lookback)
    return bullish - bearish


def _bullish_divergence(
    primary: SeriesOrFrame,
    secondary: SeriesOrFrame,
    lookback: int,
) -> SeriesOrFrame:
    recent_primary = primary.rolling(lookback, min_periods=lookback).min()
    prior_primary = primary.shift(lookback).rolling(lookback, min_periods=lookback).min()
    recent_secondary = secondary.rolling(lookback, min_periods=lookback).min()
    prior_secondary = secondary.shift(lookback).rolling(lookback, min_periods=lookback).min()
    primary_component = _normalized_gap(prior_primary, recent_primary)
    secondary_component = _normalized_gap(recent_secondary, prior_secondary)
    return (primary_component + secondary_component).clip(lower=0.0)


def _bearish_divergence(
    primary: SeriesOrFrame,
    secondary: SeriesOrFrame,
    lookback: int,
) -> SeriesOrFrame:
    recent_primary = primary.rolling(lookback, min_periods=lookback).max()
    prior_primary = primary.shift(lookback).rolling(lookback, min_periods=lookback).max()
    recent_secondary = secondary.rolling(lookback, min_periods=lookback).max()
    prior_secondary = secondary.shift(lookback).rolling(lookback, min_periods=lookback).max()
    primary_component = _normalized_gap(recent_primary, prior_primary)
    secondary_component = _normalized_gap(prior_secondary, recent_secondary)
    return (primary_component + secondary_component).clip(lower=0.0)


def _normalized_gap(current: SeriesOrFrame, reference: SeriesOrFrame) -> SeriesOrFrame:
    spread = reference.abs().replace(0.0, np.nan)
    return (current - reference).div(spread)


def _divide_like(
    left: SeriesOrFrame,
    right: SeriesOrFrame,
) -> SeriesOrFrame:
    if isinstance(left, pd.DataFrame) and isinstance(right, pd.Series):
        return left.div(right.replace(0.0, np.nan), axis=0)
    if isinstance(left, pd.DataFrame) and isinstance(right, pd.DataFrame):
        aligned_left, aligned_right = left.align(right, join="inner")
        return aligned_left.div(aligned_right.replace(0.0, np.nan))
    return left.div(right.replace(0.0, np.nan))


def _subtract_like(
    left: SeriesOrFrame,
    right: SeriesOrFrame,
) -> SeriesOrFrame:
    if isinstance(left, pd.DataFrame) and isinstance(right, pd.Series):
        return left.sub(right, axis=0)
    if isinstance(left, pd.DataFrame) and isinstance(right, pd.DataFrame):
        aligned_left, aligned_right = left.align(right, join="inner")
        return aligned_left.sub(aligned_right)
    return left - right


def _frame_like(values: SeriesOrFrame | None) -> pd.DataFrame:
    if values is None:
        raise ValueError("values cannot be None")
    if isinstance(values, pd.DataFrame):
        return values.copy()
    return values.to_frame()


def _horizon_returns(values: pd.DataFrame, horizon: int) -> pd.DataFrame:
    return values.pct_change(periods=horizon, fill_method=None)


def _benchmark_excess(
    returns: pd.DataFrame,
    benchmark_close: pd.DataFrame,
    horizon: int,
) -> pd.DataFrame:
    benchmark_returns = _horizon_returns(benchmark_close, horizon)
    if benchmark_returns.shape[1] == 1:
        return returns.sub(benchmark_returns.iloc[:, 0], axis=0)
    aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join="inner")
    return aligned_returns - aligned_benchmark


def _stack_horizon_frames(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(frames, axis=1)


def _normalize_weights(
    horizons: tuple[int, ...],
    weights: tuple[float, ...] | None,
) -> tuple[tuple[int, float], ...]:
    if weights is None:
        weights = tuple(1.0 for _ in horizons)
    if len(weights) != len(horizons):
        raise ValueError("weights must match horizons")
    total = float(sum(weights))
    if total == 0.0:
        raise ValueError("weights must not sum to zero")
    return tuple((horizon, weight / total) for horizon, weight in zip(horizons, weights, strict=True))


def _factor_frame(factors: pd.DataFrame | Mapping[str, SeriesOrFrame]) -> pd.DataFrame:
    if isinstance(factors, pd.DataFrame):
        return factors
    return pd.DataFrame(factors)


def _single_series(values: SeriesOrFrame) -> pd.Series:
    if isinstance(values, pd.Series):
        return values
    if values.shape[1] != 1:
        raise ValueError("close must be a Series or single-column DataFrame")
    return values.iloc[:, 0]


def _weighted_factor_average(
    scores: pd.DataFrame,
    weights: Mapping[str, float] | None,
) -> pd.Series:
    frame = scores.fillna(0.0)
    if weights is None:
        return frame.mean(axis=1)
    ordered_weights = pd.Series(
        {column: float(weights.get(column, 1.0)) for column in frame.columns},
        index=frame.columns,
    )
    if float(ordered_weights.sum()) == 0.0:
        raise ValueError("weights must not sum to zero")
    normalized = ordered_weights / ordered_weights.sum()
    return frame.mul(normalized, axis=1).sum(axis=1)
