from __future__ import annotations

import pandas as pd
import pytest

from project.alpha_math.market_structure import (
    failed_breakout_signal,
    gap_pressure,
    multi_timeframe_confirmation,
    support_resistance_levels,
    support_resistance_trendlines,
)


def test_support_resistance_levels_project_from_prior_window() -> None:
    high = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
    low = pd.Series([9.0, 8.0, 9.0, 10.0, 11.0])
    close = pd.Series([9.5, 10.0, 11.0, 12.0, 13.0])

    levels = support_resistance_levels(high, low, close, lookback=3)

    assert levels.support.iloc[3] == pytest.approx(8.0)
    assert levels.resistance.iloc[3] == pytest.approx(12.0)
    assert levels.midpoint.iloc[3] == pytest.approx(10.0)
    assert levels.position.iloc[3] == pytest.approx(1.0)


def test_failed_breakouts_capture_false_moves() -> None:
    high = pd.Series([10.0, 11.0, 12.0, 13.0, 11.0, 10.0])
    low = pd.Series([9.0, 8.0, 9.0, 10.0, 7.0, 6.0])
    close = pd.Series([9.5, 10.0, 11.0, 11.5, 10.5, 10.0])

    signal = failed_breakout_signal(high, low, close, lookback=3, atr_period=3)

    assert signal.failed_up.iloc[3]
    assert signal.failed_down.iloc[4]
    assert signal.range_expansion.iloc[3] > 0.0


def test_multi_timeframe_confirmation_scores_trend_stack() -> None:
    uptrend = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    downtrend = pd.Series([15.0, 14.0, 13.0, 12.0, 11.0, 10.0])

    bullish = multi_timeframe_confirmation(uptrend, windows=(2, 3, 4))
    bearish = multi_timeframe_confirmation(downtrend, windows=(2, 3, 4))

    assert bullish.score.iloc[-1] > 0.0
    assert bullish.bullish.iloc[-1]
    assert bearish.score.iloc[-1] < 0.0
    assert bearish.bearish.iloc[-1]


def test_gap_pressure_detects_fill_and_gap_direction() -> None:
    open_ = pd.Series([10.0, 12.0, 9.0])
    high = pd.Series([11.0, 13.0, 13.0])
    low = pd.Series([9.5, 10.0, 8.5])
    close = pd.Series([10.5, 12.5, 9.5])

    gap = gap_pressure(open_, high, low, close)

    assert gap.gap.iloc[1] == pytest.approx(1.5)
    assert gap.fill_ratio.iloc[1] == pytest.approx(1.0)
    assert gap.filled.iloc[1]
    assert gap.gap.iloc[2] == pytest.approx(-3.5)
    assert gap.filled.iloc[2]


def test_support_resistance_trendlines_follow_linear_channels() -> None:
    high = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
    low = pd.Series([9.0, 10.0, 11.0, 12.0, 13.0])

    trendlines = support_resistance_trendlines(high, low, lookback=3)

    assert trendlines.support.iloc[2] == pytest.approx(11.0)
    assert trendlines.resistance.iloc[2] == pytest.approx(12.0)
    assert trendlines.support.iloc[-1] == pytest.approx(13.0)
    assert trendlines.resistance.iloc[-1] == pytest.approx(14.0)
