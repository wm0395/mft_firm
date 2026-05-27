from __future__ import annotations

import pandas as pd
import pytest

from project.alpha_math.gap_regimes import (
    opening_gap_metrics,
    opening_gap_regime,
)


def test_opening_gap_metrics_capture_bullish_continuation() -> None:
    open_ = pd.Series([10.0, 10.0, 10.0, 11.0])
    high = pd.Series([11.0, 11.0, 11.0, 12.0])
    low = pd.Series([9.0, 9.0, 9.0, 10.5])
    close = pd.Series([10.0, 10.0, 10.0, 11.8])

    metrics = opening_gap_metrics(open_, high, low, close, atr_period=3)
    regime = opening_gap_regime(
        open_,
        high,
        low,
        close,
        atr_period=3,
        min_gap_atr=0.5,
        continuation_threshold=0.5,
    )

    assert metrics.gap.iloc[3] == pytest.approx(1.0)
    assert metrics.gap_pct.iloc[3] == pytest.approx(0.1)
    assert metrics.gap_atr.iloc[3] == pytest.approx(0.5)
    assert metrics.fill_ratio.iloc[3] == pytest.approx(0.5)
    assert metrics.close_location.iloc[3] == pytest.approx(0.8666666667)
    assert metrics.continuation_score.iloc[3] == pytest.approx(0.8)
    assert bool(regime.bullish_gap.iloc[3])
    assert bool(regime.gap_continuation.iloc[3])
    assert not bool(regime.gap_filled.iloc[3])
    assert not bool(regime.gap_faded.iloc[3])


def test_opening_gap_regime_supports_frames_and_gap_fade() -> None:
    open_, high, low, close = _frame_inputs()

    regime = opening_gap_regime(open_, high, low, close, atr_period=3)

    assert isinstance(regime.metrics.gap, pd.DataFrame)
    assert pd.isna(regime.metrics.gap["asset"].iloc[0])
    assert regime.metrics.gap["asset"].iloc[3] == pytest.approx(-1.0)
    assert pd.isna(regime.metrics.fill_ratio["asset"].iloc[0])
    assert regime.metrics.fill_ratio["asset"].iloc[3] == pytest.approx(1.0)
    assert regime.metrics.continuation_score["asset"].iloc[0] == pytest.approx(0.0)
    assert regime.metrics.continuation_score["asset"].iloc[3] == pytest.approx(-1.1)
    assert bool(regime.bearish_gap["asset"].iloc[3])
    assert bool(regime.gap_filled["asset"].iloc[3])
    assert bool(regime.gap_faded["asset"].iloc[3])
    assert not bool(regime.gap_continuation["asset"].iloc[3])
    assert not bool(regime.gap_exhaustion["asset"].iloc[3])


def _frame_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    open_ = pd.DataFrame({"asset": [10.0, 10.0, 10.0, 9.0]})
    high = pd.DataFrame({"asset": [11.0, 11.0, 11.0, 10.2]})
    low = pd.DataFrame({"asset": [9.0, 9.0, 9.0, 8.8]})
    close = pd.DataFrame({"asset": [10.0, 10.0, 10.0, 10.1]})
    return open_, high, low, close
