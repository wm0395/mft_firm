from __future__ import annotations

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.projects.price_action_strategy_lab.price_action_pattern_specs import (
    doji_reversal_score,
    engulfing_reversal_score,
    hammer_shooting_star_score,
    inside_outside_bar_score,
    piercing_dark_cloud_score,
)


def test_doji_reversal_score_tracks_trend_direction() -> None:
    down = _panel(
        [10.0, 9.5, 9.0, 8.5, 8.0, 7.5],
        [10.02, 9.52, 9.02, 8.52, 8.02, 7.52],
        [10.5, 10.0, 9.5, 9.0, 8.5, 8.0],
        [9.5, 9.0, 8.5, 8.0, 7.5, 7.0],
    )
    up = _panel(
        [7.5, 8.0, 8.5, 9.0, 9.5, 10.0],
        [7.48, 7.98, 8.48, 8.98, 9.48, 9.98],
        [8.0, 8.5, 9.0, 9.5, 10.0, 10.5],
        [7.0, 7.5, 8.0, 8.5, 9.0, 9.5],
    )

    assert doji_reversal_score.builder(down)["asset"].iloc[-1] > 0.0
    assert doji_reversal_score.builder(up)["asset"].iloc[-1] < 0.0


def test_engulfing_reversal_score_distinguishes_direction() -> None:
    bullish = _panel(
        [10.0, 9.5, 9.0, 8.9, 8.5, 7.8],
        [10.5, 10.0, 9.5, 9.3, 9.0, 9.3],
        [9.5, 9.0, 8.5, 8.2, 7.8, 7.4],
        [9.6, 9.1, 8.6, 8.4, 8.0, 9.2],
    )
    bearish = _panel(
        [7.0, 7.5, 8.0, 8.5, 8.8, 9.4],
        [7.5, 8.0, 8.5, 8.9, 9.2, 9.8],
        [6.5, 7.0, 7.5, 8.0, 8.6, 8.2],
        [6.8, 7.3, 7.8, 8.2, 9.1, 8.5],
    )

    assert engulfing_reversal_score.builder(bullish)["asset"].iloc[-1] > 0.0
    assert engulfing_reversal_score.builder(bearish)["asset"].iloc[-1] < 0.0


def test_hammer_and_shooting_star_scores_flip_sign() -> None:
    hammer = _panel(
        [10.0, 9.5, 9.0, 8.5, 8.0, 7.8],
        [10.5, 10.0, 9.5, 9.0, 8.5, 8.05],
        [9.5, 9.0, 8.5, 8.0, 7.5, 7.0],
        [9.6, 9.1, 8.6, 8.2, 7.9, 7.95],
    )
    shooting = _panel(
        [7.5, 8.0, 8.5, 9.0, 9.4, 9.2],
        [7.9, 8.4, 8.9, 9.4, 9.9, 9.9],
        [7.0, 7.5, 8.0, 8.5, 9.0, 8.9],
        [7.4, 7.9, 8.4, 8.9, 9.3, 9.1],
    )

    assert hammer_shooting_star_score.builder(hammer)["asset"].iloc[-1] > 0.0
    assert hammer_shooting_star_score.builder(shooting)["asset"].iloc[-1] < 0.0


def test_inside_outside_bar_score_captures_breakouts_and_reversals() -> None:
    breakout = _panel(
        [10.0, 9.4, 9.6, 9.7],
        [10.5, 9.5, 10.0, 10.1],
        [8.0, 8.6, 9.2, 9.3],
        [9.0, 9.0, 9.8, 9.9],
    )
    reversal = _panel(
        [10.0, 9.8, 10.4, 10.2],
        [10.5, 9.9, 10.6, 10.3],
        [8.0, 8.8, 7.4, 7.2],
        [9.0, 9.2, 7.5, 7.3],
    )

    assert inside_outside_bar_score.builder(breakout)["asset"].iloc[2] > 0.0
    assert inside_outside_bar_score.builder(reversal)["asset"].iloc[2] < 0.0


def test_piercing_dark_cloud_score_flips_with_pattern_direction() -> None:
    bullish = _panel(
        [10.0, 9.5, 9.0, 8.9, 8.5, 7.8],
        [10.5, 10.0, 9.5, 9.3, 9.0, 8.9],
        [9.5, 9.0, 8.5, 8.2, 7.8, 7.4],
        [9.6, 9.1, 8.6, 8.4, 8.0, 8.9],
    )
    bearish = _panel(
        [7.0, 7.5, 8.0, 8.5, 8.8, 9.4],
        [7.5, 8.0, 8.5, 8.9, 9.2, 9.8],
        [6.5, 7.0, 7.5, 8.0, 8.6, 8.2],
        [6.8, 7.3, 7.8, 8.2, 9.1, 8.5],
    )

    assert piercing_dark_cloud_score.builder(bullish)["asset"].iloc[-1] > 0.0
    assert piercing_dark_cloud_score.builder(bearish)["asset"].iloc[-1] < 0.0


def _panel(
    open_values: list[float],
    high_values: list[float],
    low_values: list[float],
    close_values: list[float],
) -> Alpha101Panel:
    dates = pd.date_range("2024-01-01", periods=len(close_values))
    open_ = pd.DataFrame({"asset": open_values}, index=dates)
    high = pd.DataFrame({"asset": high_values}, index=dates)
    low = pd.DataFrame({"asset": low_values}, index=dates)
    close = pd.DataFrame({"asset": close_values}, index=dates)
    active = pd.DataFrame(True, index=dates, columns=["asset"])
    volume = pd.DataFrame({"asset": [1000.0 + value for value in range(len(close_values))]}, index=dates)
    return Alpha101Panel(
        name="candlestick",
        open=open_,
        high=high,
        low=low,
        close=close,
        adj_close=close,
        volume=volume,
        vwap=close,
        returns=close.pct_change(),
        active_mask=active,
        high_vol_mask=active,
        constituents=("asset",),
        industry={"asset": "test"},
        pit_risk="test",
    )
