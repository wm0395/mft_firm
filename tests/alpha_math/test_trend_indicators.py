from __future__ import annotations

import pandas as pd
import pytest

from project.alpha_math.trend_indicators import (
    UltimateOscillatorResult,
    VortexResult,
    WilliamsRResult,
    aroon,
    chande_momentum_oscillator,
    commodity_channel_index,
    elder_ray,
    ichimoku_cloud,
    know_sure_thing,
    ultimate_oscillator,
    vortex_indicator,
    williams_r,
)


def test_aroon_and_momentum_oscillators_turn_positive_in_trend() -> None:
    high = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
    low = pd.Series([9.0, 8.0, 7.0, 8.0, 9.0])
    close = pd.Series([9.5, 10.5, 11.5, 12.5, 13.5])

    result = aroon(high, low, period=3)
    cci = commodity_channel_index(high, low, close, period=3)
    cmo = chande_momentum_oscillator(close, period=3)

    assert result.up.iloc[-1] == pytest.approx(100.0)
    assert result.down.iloc[-1] == pytest.approx(33.3333333333, rel=1e-6)
    assert result.oscillator.iloc[-1] > 0.0
    assert cci.iloc[-1] > 0.0
    assert cmo.iloc[-1] > 0.0


def test_ichimoku_elder_ray_and_kst_are_explicit() -> None:
    high = pd.Series([10.0, 12.0, 14.0, 16.0, 18.0, 20.0])
    low = pd.Series([8.0, 10.0, 12.0, 14.0, 16.0, 18.0])
    close = pd.Series([9.0, 11.0, 13.0, 15.0, 17.0, 19.0])

    ichimoku = ichimoku_cloud(
        high,
        low,
        close,
        tenkan_period=2,
        kijun_period=3,
        senkou_b_period=4,
        displacement=1,
    )
    elder = elder_ray(high, low, close, period=3)

    assert ichimoku.tenkan_sen.iloc[1] == pytest.approx(10.0)
    assert ichimoku.kijun_sen.iloc[2] == pytest.approx(11.0)
    assert ichimoku.senkou_span_a.iloc[3] == pytest.approx(11.5)
    assert ichimoku.chikou_span.iloc[1] == pytest.approx(13.0)
    assert elder.bull_power.iloc[-1] > elder.bear_power.iloc[-1]


def test_kst_is_positive_in_a_long_uptrend() -> None:
    close = pd.Series([float(value) for value in range(1, 61)])

    kst = know_sure_thing(close, signal_period=3)

    assert kst.kst.iloc[-1] > 0.0
    assert kst.signal.iloc[-1] > 0.0


def test_directional_oscillators_turn_bullish_in_uptrend() -> None:
    high = pd.Series([float(value) for value in range(10, 40)])
    low = pd.Series([float(value) for value in range(8, 38)])
    close = pd.Series([float(value) - 0.5 for value in range(10, 40)])

    vortex = vortex_indicator(high, low, close, period=5)
    ultimate = ultimate_oscillator(high, low, close)
    williams = williams_r(high, low, close)

    assert isinstance(vortex, VortexResult)
    assert isinstance(ultimate, UltimateOscillatorResult)
    assert isinstance(williams, WilliamsRResult)
    assert vortex.bullish.iloc[-1]
    assert vortex.spread.iloc[-1] > 0.0
    assert ultimate.oscillator.iloc[-1] > 50.0
    assert williams.overbought.iloc[-1]
    assert williams.above_centerline.iloc[-1]
