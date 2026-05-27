from __future__ import annotations

import pandas as pd
import pytest

from project.alpha_math.price_action import (
    atr_position_size,
    bollinger_bandwidth,
    bollinger_percent_b,
    bollinger_squeeze,
    chandelier_exit,
    opening_range_breakout,
    parabolic_sar,
    pivot_points,
)


def test_bollinger_compression_marks_a_squeeze() -> None:
    close = pd.Series([100.0] * 150)

    bandwidth = bollinger_bandwidth(close, period=20)
    percent_b = bollinger_percent_b(close, period=20)
    squeeze = bollinger_squeeze(close, period=20, lookback=125)

    assert bandwidth.iloc[-1] == pytest.approx(0.0)
    assert percent_b.iloc[-1] == pytest.approx(0.5)
    assert squeeze.iloc[-1]


def test_pivot_points_and_atr_sizing_are_explicit() -> None:
    high = pd.Series([11.0, 12.0, 13.0])
    low = pd.Series([9.0, 8.0, 10.0])
    close = pd.Series([10.0, 10.0, 11.0])

    levels = pivot_points(high, low, close)
    size = atr_position_size(100_000.0, pd.Series([2.0, 4.0]), 0.01, 2.0)

    assert levels.pivot.iloc[2] == pytest.approx(10.0)
    assert levels.resistance_1.iloc[2] == pytest.approx(12.0)
    assert levels.support_1.iloc[2] == pytest.approx(8.0)
    assert size.iloc[0] == pytest.approx(250.0)
    assert size.iloc[1] == pytest.approx(125.0)


def test_chandelier_exit_tracks_trend_and_distance() -> None:
    high = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
    low = pd.Series([9.0, 10.0, 11.0, 12.0, 13.0])
    close = pd.Series([9.5, 10.5, 11.5, 12.5, 13.5])

    result = chandelier_exit(high, low, close, period=3, multiple=3.0)

    assert result.long_stop.iloc[-1] < close.iloc[-1]
    assert result.short_stop.iloc[-1] > close.iloc[-1]


def test_parabolic_sar_flips_after_a_reversal_bar() -> None:
    high = pd.Series([10.0, 11.0, 12.0, 13.0, 9.0, 8.5, 8.0, 7.5])
    low = pd.Series([9.0, 10.0, 11.0, 12.0, 8.5, 8.0, 7.5, 7.0])
    close = pd.Series([9.5, 10.5, 11.5, 12.5, 8.8, 8.2, 7.8, 7.2])

    result = parabolic_sar(high, low, close)

    assert result.trend.iloc[0] == pytest.approx(1.0)
    assert result.trend.iloc[4] == pytest.approx(-1.0)
    assert result.acceleration_factor.iloc[4] == pytest.approx(0.02)


def test_opening_range_breakout_uses_session_labels() -> None:
    session = pd.Series(["A", "A", "A", "A", "B", "B", "B", "B"])
    high = pd.Series([10.0, 11.0, 12.0, 11.0, 20.0, 21.0, 21.0, 21.0])
    low = pd.Series([9.0, 9.5, 10.0, 10.5, 19.0, 18.0, 17.0, 16.0])
    close = pd.Series([9.5, 10.5, 11.5, 11.0, 19.5, 18.5, 17.5, 15.5])

    result = opening_range_breakout(high, low, close, session, bars=2)

    assert result.opening_high.iloc[2] == pytest.approx(11.0)
    assert result.opening_low.iloc[2] == pytest.approx(9.0)
    assert result.long_breakout.iloc[2]
    assert result.short_breakout.iloc[6]
