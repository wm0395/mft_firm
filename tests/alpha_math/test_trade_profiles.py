from __future__ import annotations

import pandas as pd
import pytest

from project.alpha_math.trade_profiles import (
    failed_breakout_score,
    failed_reversal_score,
    hybrid_trend_volume_scores,
    pyramiding_ladder,
    trend_volume_composite,
)


def test_failed_breakout_score_distinguishes_failed_up_and_down_breakouts() -> None:
    high = pd.Series([10.0, 11.0, 12.0, 13.0, 11.0, 10.0])
    low = pd.Series([9.0, 8.0, 9.0, 10.0, 7.0, 6.0])
    close = pd.Series([9.5, 10.0, 11.0, 11.5, 10.5, 8.5])
    volume = pd.Series([100.0, 120.0, 140.0, 160.0, 180.0, 200.0])

    score = failed_breakout_score(
        high,
        low,
        close,
        volume,
        lookback=3,
        atr_period=3,
        volume_period=3,
    )

    assert score.bearish_score.iloc[3] > 0.0
    assert score.score.iloc[3] < 0.0
    assert score.bullish_score.iloc[4] > 0.0
    assert score.score.iloc[4] > 0.0


def test_failed_reversal_score_tracks_trend_context() -> None:
    up_close = pd.Series(range(10, 20), dtype=float)
    up_open = up_close - 0.5
    up_high = up_close + 1.0
    up_low = up_open - 1.0
    volume = pd.Series(range(100, 110), dtype=float)

    bullish = failed_reversal_score(
        up_open,
        up_high,
        up_low,
        up_close,
        volume,
        trend_period=3,
        volume_period=3,
    )

    down_close = pd.Series(range(20, 10, -1), dtype=float)
    down_open = down_close + 0.5
    down_high = down_open + 1.0
    down_low = down_close - 1.0

    bearish = failed_reversal_score(
        down_open,
        down_high,
        down_low,
        down_close,
        volume,
        trend_period=3,
        volume_period=3,
    )

    assert bullish.bullish_score.iloc[-1] > 0.0
    assert bullish.score.iloc[-1] > 0.0
    assert bearish.bearish_score.iloc[-1] > 0.0
    assert bearish.score.iloc[-1] < 0.0


def test_trend_volume_composite_supports_frames() -> None:
    close = pd.DataFrame({"asset": [100.0 + value for value in range(30)]})
    high = close + 1.0
    low = close - 1.0
    volume = pd.DataFrame({"asset": [1000.0 + (10.0 * value) for value in range(30)]})

    composite = trend_volume_composite(
        high,
        low,
        close,
        volume,
        trend_fast=5,
        trend_slow=8,
        flow_period=5,
    )

    assert isinstance(composite.score, pd.DataFrame)
    assert composite.score["asset"].iloc[-1] > 0.0
    assert composite.bullish["asset"].iloc[-1]


def test_hybrid_trend_volume_scores_stack_multiple_composites() -> None:
    close = pd.DataFrame({"asset": [100.0 + value for value in range(30)]})
    high = close + 1.0
    low = close - 1.0
    volume = pd.DataFrame({"asset": [1000.0 + (20.0 * value) for value in range(30)]})

    scores = hybrid_trend_volume_scores(
        high,
        low,
        close,
        volume,
        trend_fast=5,
        trend_slow=8,
        volume_period=5,
        oscillator_period=5,
    )

    assert isinstance(scores.confirmation_score, pd.DataFrame)
    assert scores.breakout_score["asset"].iloc[-1] > 0.0
    assert scores.bullish["asset"].iloc[-1]


def test_pyramiding_ladder_projects_adds_and_scale_outs() -> None:
    ladder = pyramiding_ladder(
        pd.Series([100.0]),
        pd.Series([2.0]),
        100_000.0,
        direction=1.0,
        risk_fraction=0.01,
        stop_multiple=2.0,
    )

    assert ladder.stop_loss.iloc[0] == pytest.approx(96.0)
    assert ladder.add_1.iloc[0] == pytest.approx(104.0)
    assert ladder.add_2.iloc[0] == pytest.approx(108.0)
    assert ladder.scale_out_1.iloc[0] == pytest.approx(106.0)
    assert ladder.scale_out_2.iloc[0] == pytest.approx(112.0)
    assert ladder.initial_size.iloc[0] == pytest.approx(250.0)
