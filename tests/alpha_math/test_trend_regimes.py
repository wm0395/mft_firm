from __future__ import annotations

import pandas as pd

from project.alpha_math.trend_regimes import (
    ChoppinessIndexResult,
    KeltnerChannelResult,
    SuperTrendResult,
    TRIXResult,
    choppiness_index,
    keltner_channels,
    supertrend,
    trix,
)


def test_keltner_channels_and_supertrend_follow_a_strong_trend() -> None:
    base = pd.Series([float(value) for value in range(100, 130)])
    high = pd.DataFrame({"a": base + 1.0, "b": base + 2.0})
    low = high - 2.0
    close = high - 0.25

    keltner = keltner_channels(
        high,
        low,
        close,
        ema_period=5,
        atr_period=3,
        multiplier=0.1,
    )
    trend = supertrend(high, low, close, atr_period=3, multiplier=0.5)

    assert isinstance(keltner, KeltnerChannelResult)
    assert isinstance(trend, SuperTrendResult)
    assert keltner.middle.iloc[-1].gt(keltner.middle.iloc[10]).all()
    assert keltner.breakout_above.iloc[-1].all()
    assert trend.bullish.iloc[-1].all()
    assert trend.supertrend.iloc[-1].lt(close.iloc[-1]).all()


def test_choppiness_and_trix_separate_trend_from_range() -> None:
    trend_high = pd.Series([float(value) for value in range(100, 130)])
    trend_low = trend_high - 2.0
    trend_close = trend_high - 0.25
    range_high = pd.Series(
        [101.5 if index % 2 == 0 else 101.0 for index in range(30)]
    )
    range_low = pd.Series(
        [98.5 if index % 2 == 0 else 99.0 for index in range(30)]
    )
    range_close = pd.Series(
        [100.0 if index % 2 == 0 else 100.2 for index in range(30)]
    )

    chop_trend = choppiness_index(trend_high, trend_low, trend_close, period=14)
    chop_range = choppiness_index(range_high, range_low, range_close, period=14)
    oscillator = trix(trend_close, period=5, signal_period=3)

    assert isinstance(chop_trend, ChoppinessIndexResult)
    assert isinstance(chop_range, ChoppinessIndexResult)
    assert isinstance(oscillator, TRIXResult)
    assert chop_trend.trending.iloc[-1]
    assert chop_range.choppy.iloc[-1]
    assert oscillator.positive.iloc[-1]
    assert oscillator.signal.iloc[-1] > 0.0
