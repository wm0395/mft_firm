from __future__ import annotations

import pandas as pd
import pytest

from project.alpha_math.ohlcv import (
    average_directional_index,
    average_true_range,
    breakout_above,
    bollinger_bands,
    candle_body,
    close_location_value,
    directional_movement_index,
    donchian_channels,
    gap_down,
    gap_up,
    is_bearish_engulfing,
    is_bullish_engulfing,
    is_doji,
    is_inside_bar,
    is_outside_bar,
    macd,
    money_flow_index,
    on_balance_volume,
    relative_strength_index,
    relative_volume,
    stochastic_oscillator,
    typical_price,
    true_range,
)


def _panel() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    index = pd.RangeIndex(8)
    up_close = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0], index=index)
    down_close = pd.Series(
        [17.0, 16.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0],
        index=index,
    )
    close = pd.DataFrame({"up": up_close, "down": down_close})
    high = close + 1.0
    low = close - 1.0
    open_ = close - 0.5
    volume = pd.DataFrame(
        {
            "up": [100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0],
            "down": [170.0, 160.0, 150.0, 140.0, 130.0, 120.0, 110.0, 100.0],
        },
        index=index,
    )
    return open_, high, low, close, volume


def test_core_ohlcv_indicators_work_on_frames() -> None:
    _open, high, low, close, volume = _panel()

    tr = true_range(high, low, close)
    atr = average_true_range(high, low, close, period=3)
    rsi = relative_strength_index(close, period=3)
    dm = directional_movement_index(high, low, close, period=3)
    adx = average_directional_index(high, low, close, period=3)
    mfi = money_flow_index(high, low, close, volume, period=3)
    obv = on_balance_volume(close, volume)
    rel_vol = relative_volume(volume, period=3)
    macd_result = macd(close, fast=3, slow=5, signal=2)

    assert tr.loc[1, "up"] == pytest.approx(2.0)
    assert atr.loc[2, "up"] == pytest.approx(2.0)
    assert rsi.loc[7, "up"] == pytest.approx(100.0)
    assert rsi.loc[7, "down"] == pytest.approx(0.0)
    assert dm.plus_di.loc[7, "up"] > dm.minus_di.loc[7, "up"]
    assert dm.minus_di.loc[7, "down"] > dm.plus_di.loc[7, "down"]
    assert adx.loc[7, "up"] == pytest.approx(100.0)
    assert mfi.loc[7, "up"] == pytest.approx(100.0)
    assert obv.loc[7, "up"] > 0.0
    assert rel_vol.loc[7, "up"] == pytest.approx(170.0 / 160.0)
    assert macd_result.histogram.loc[7, "up"] > 0.0


def test_price_channels_and_breakouts_are_deterministic() -> None:
    _open, high, low, close, volume = _panel()
    bands = bollinger_bands(close["up"], period=3, stddevs=2.0)
    channels = donchian_channels(high["up"], low["up"], period=3)
    stochastic = stochastic_oscillator(
        high["up"],
        low["up"],
        close["up"],
        period=3,
        smooth=2,
    )

    assert bands.middle.iloc[2] == pytest.approx(11.0)
    assert bands.upper.iloc[2] > bands.middle.iloc[2] > bands.lower.iloc[2]
    assert channels.upper.iloc[2] == pytest.approx(13.0)
    assert channels.lower.iloc[2] == pytest.approx(9.0)
    assert stochastic.percent_k.iloc[7] == pytest.approx(75.0)
    assert stochastic.percent_d.iloc[7] == pytest.approx(75.0)
    assert breakout_above(close["up"], lookback=3).iloc[4]
    assert relative_volume(volume["up"], period=3).iloc[7] == pytest.approx(
        170.0 / 160.0
    )


def test_price_action_patterns_capture_common_bars() -> None:
    open_ = pd.Series([10.0, 10.1, 9.8, 10.6], index=pd.RangeIndex(4))
    high = pd.Series([10.5, 10.3, 10.8, 10.9], index=pd.RangeIndex(4))
    low = pd.Series([9.7, 9.9, 9.6, 9.5], index=pd.RangeIndex(4))
    close = pd.Series([10.2, 10.1, 10.7, 9.7], index=pd.RangeIndex(4))

    assert candle_body(open_, close).iloc[2] == pytest.approx(0.9)
    assert close_location_value(high, low, close).iloc[2] > 0.5
    assert gap_up(open_, close).iloc[2] == pytest.approx(0.0)
    assert gap_down(open_, close).iloc[3] == pytest.approx(0.1)
    assert is_doji(open_, high, low, close, threshold=0.2).iloc[1]
    assert is_inside_bar(high, low).iloc[1]
    assert is_outside_bar(high, low).iloc[2]
    assert typical_price(high, low, close).iloc[0] == pytest.approx(
        (10.5 + 9.7 + 10.2) / 3.0
    )


def test_engulfing_patterns_are_detected() -> None:
    bullish_open = pd.Series([10.0, 10.1, 9.8], index=pd.RangeIndex(3))
    bullish_high = pd.Series([10.4, 10.2, 10.9], index=pd.RangeIndex(3))
    bullish_low = pd.Series([9.8, 9.9, 9.6], index=pd.RangeIndex(3))
    bullish_close = pd.Series([10.2, 10.0, 10.8], index=pd.RangeIndex(3))

    bearish_open = pd.Series([10.0, 10.2, 10.9], index=pd.RangeIndex(3))
    bearish_high = pd.Series([10.4, 10.6, 11.0], index=pd.RangeIndex(3))
    bearish_low = pd.Series([9.8, 9.9, 9.5], index=pd.RangeIndex(3))
    bearish_close = pd.Series([10.2, 10.4, 9.6], index=pd.RangeIndex(3))

    assert is_bullish_engulfing(
        bullish_open,
        bullish_high,
        bullish_low,
        bullish_close,
    ).iloc[2]
    assert is_bearish_engulfing(
        bearish_open,
        bearish_high,
        bearish_low,
        bearish_close,
    ).iloc[2]
