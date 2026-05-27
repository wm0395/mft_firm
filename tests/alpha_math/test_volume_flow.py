from __future__ import annotations

import pandas as pd

from project.alpha_math.volume_flow import (
    accumulation_distribution_line,
    chaikin_money_flow,
    chaikin_oscillator,
    ease_of_movement,
    force_index,
    price_volume_trend,
)


def test_accumulation_distribution_and_chaikin_flow_are_positive_in_uptrend() -> None:
    high = pd.Series([11.0, 12.0, 13.0, 14.0, 15.0])
    low = pd.Series([9.0, 10.0, 11.0, 12.0, 13.0])
    close = pd.Series([10.5, 11.5, 12.5, 13.5, 14.5])
    volume = pd.Series([100.0, 120.0, 140.0, 160.0, 180.0])

    adl = accumulation_distribution_line(high, low, close, volume)
    cmf = chaikin_money_flow(high, low, close, volume, period=3)
    oscillator = chaikin_oscillator(high, low, close, volume, fast=2, slow=3)

    assert adl.adl.iloc[-1] > 0.0
    assert cmf.cmf.iloc[-1] > 0.0
    assert oscillator.oscillator.iloc[-1] > 0.0


def test_force_index_eom_and_pvt_track_price_volume_pressure() -> None:
    high = pd.Series([11.0, 12.0, 13.0, 14.0, 15.0])
    low = pd.Series([9.0, 10.0, 11.0, 12.0, 13.0])
    close = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
    volume = pd.Series([100.0, 120.0, 140.0, 160.0, 180.0])

    force = force_index(close, volume, period=3)
    eom = ease_of_movement(high, low, volume, period=3)
    pvt = price_volume_trend(close, volume)

    assert force.force_index.iloc[-1] > 0.0
    assert force.smoothed_force_index.iloc[-1] > 0.0
    assert eom.eom.iloc[-1] > 0.0
    assert eom.smoothed_eom.iloc[-1] > 0.0
    assert pvt.pvt.iloc[-1] > 0.0
