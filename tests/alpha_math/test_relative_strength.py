from __future__ import annotations

import pandas as pd

from project.alpha_math.relative_strength import (
    HigherOrderDivergenceScores,
    divergence_scores,
    higher_order_divergence_scores,
    multi_horizon_relative_strength_rank,
    relative_strength_overlay,
    relative_strength_ratio,
    RelativeStrengthRanking,
)


def test_relative_strength_ratio_and_overlay_track_benchmark_outperformance() -> None:
    close = pd.Series([100.0, 102.0, 104.0, 106.0, 108.0, 110.0])
    benchmark = pd.Series([100.0, 100.0, 101.0, 102.0, 103.0, 104.0])

    ratio = relative_strength_ratio(close, benchmark)
    overlay = relative_strength_overlay(
        close,
        benchmark,
        trend_fast=2,
        trend_slow=3,
        zscore_window=3,
    )

    assert ratio.iloc[-1] > 1.0
    assert overlay.trend.iloc[-1] > 0.0
    assert overlay.bullish.iloc[-1]


def test_relative_strength_overlay_supports_frames_against_a_benchmark_series() -> None:
    close = pd.DataFrame(
        {
            "leader": [100.0, 102.0, 104.0, 106.0, 108.0, 110.0],
            "laggard": [100.0, 99.0, 98.0, 97.0, 96.0, 95.0],
        }
    )
    benchmark = pd.Series([100.0, 100.0, 100.0, 100.0, 100.0, 100.0])

    overlay = relative_strength_overlay(
        close,
        benchmark,
        trend_fast=2,
        trend_slow=3,
        zscore_window=3,
    )

    assert isinstance(overlay.ratio, pd.DataFrame)
    assert overlay.bullish["leader"].iloc[-1]
    assert overlay.bearish["laggard"].iloc[-1]


def test_divergence_scores_detect_bullish_and_bearish_divergence() -> None:
    bullish_close = pd.Series([10.0, 9.0, 8.0, 9.0, 7.0, 8.0])
    bullish_momentum = pd.Series([20.0, 15.0, 10.0, 14.0, 12.0, 13.0])
    bullish_volume = pd.Series([100.0, 90.0, 80.0, 120.0, 130.0, 140.0])

    bullish = divergence_scores(
        bullish_close,
        bullish_momentum,
        bullish_volume,
        lookback=3,
    )

    bearish_close = pd.Series([8.0, 9.0, 10.0, 9.0, 11.0, 10.0])
    bearish_momentum = pd.Series([30.0, 28.0, 26.0, 25.0, 23.0, 22.0])
    bearish_volume = pd.Series([140.0, 130.0, 120.0, 100.0, 90.0, 80.0])

    bearish = divergence_scores(
        bearish_close,
        bearish_momentum,
        bearish_volume,
        lookback=3,
    )

    assert bullish.price_momentum_score.iloc[-1] > 0.0
    assert bullish.price_volume_score.iloc[-1] > 0.0
    assert bullish.composite_score.iloc[-1] > 0.0
    assert bullish.bullish.iloc[-1]
    assert bearish.price_momentum_score.iloc[-1] < 0.0
    assert bearish.price_volume_score.iloc[-1] < 0.0
    assert bearish.composite_score.iloc[-1] < 0.0
    assert bearish.bearish.iloc[-1]


def test_multi_horizon_relative_strength_rank_scores_leaders() -> None:
    close = pd.DataFrame(
        {
            "leader": [100.0, 105.0, 111.0, 118.0, 126.0, 135.0],
            "laggard": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
        }
    )

    ranking = multi_horizon_relative_strength_rank(close, horizons=(1, 2, 3))

    assert isinstance(ranking, RelativeStrengthRanking)
    assert ranking.horizon_ranks.columns.nlevels == 2
    assert ranking.composite_rank["leader"].iloc[-1] > ranking.composite_rank["laggard"].iloc[-1]
    assert ranking.leader["leader"].iloc[-1]
    assert ranking.laggard["laggard"].iloc[-1]


def test_higher_order_divergence_scores_stack_multiple_factors() -> None:
    close = pd.Series([10.0, 9.0, 8.0, 9.0, 7.0, 8.0])
    bullish_factors = pd.DataFrame(
        {
            "osc_1": [20.0, 19.0, 18.0, 21.0, 22.0, 23.0],
            "osc_2": [40.0, 39.0, 38.0, 41.0, 42.0, 43.0],
        }
    )
    bearish_factors = pd.DataFrame(
        {
            "osc_1": [30.0, 29.0, 28.0, 27.0, 26.0, 25.0],
            "osc_2": [50.0, 49.0, 48.0, 47.0, 46.0, 45.0],
        }
    )

    bullish = higher_order_divergence_scores(close, bullish_factors, lookback=3)
    bearish_close = pd.Series([8.0, 9.0, 10.0, 9.0, 11.0, 12.0])
    bearish = higher_order_divergence_scores(bearish_close, bearish_factors, lookback=3)

    assert isinstance(bullish, HigherOrderDivergenceScores)
    assert bullish.factor_scores["osc_1"].iloc[-1] > 0.0
    assert bullish.composite_score.iloc[-1] > 0.0
    assert bullish.bullish.iloc[-1]
    assert bearish.factor_scores["osc_1"].iloc[-1] < 0.0
    assert bearish.composite_score.iloc[-1] < 0.0
    assert bearish.bearish.iloc[-1]
