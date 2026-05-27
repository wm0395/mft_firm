from __future__ import annotations

import pandas as pd
import pytest

from project.alpha_math.regime_filters import (
    HigherTimeframeRegimeFilters,
    RegimeFilters,
    higher_timeframe_regime_filters,
    hurst_exponent,
    variance_ratio,
    volatility_regime_filters,
)


def test_variance_ratio_and_hurst_exponent_are_explicit() -> None:
    close = pd.Series([100.0, 101.0, 103.0, 106.0, 110.0, 115.0, 121.0, 128.0])

    vr = variance_ratio(close, window=5, lag=2)
    hurst = hurst_exponent(close, window=5)

    assert vr.iloc[-1] == pytest.approx(1.0639117034613268)
    assert hurst.iloc[-1] == pytest.approx(0.4800184306057962)


def test_volatility_regime_filters_support_frames() -> None:
    assert isinstance(_frame_regime().range_volatility, pd.DataFrame)


def test_volatility_regime_filters_flags_trend() -> None:
    regime = _frame_regime()
    assert regime.trending["asset"].tolist() == [
        False,
        False,
        False,
        False,
        True,
        True,
        True,
        True,
    ]


def test_volatility_regime_filters_flags_volatility() -> None:
    regime = _frame_regime()
    assert regime.high_volatility["asset"].tolist() == [
        False,
        False,
        False,
        False,
        False,
        True,
        True,
        True,
    ]
    assert regime.expanding_volatility["asset"].tolist() == [
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
    ]


def test_higher_timeframe_regime_filters_align_trends() -> None:
    close = pd.DataFrame({"asset": [100.0, 101.0, 103.0, 106.0, 110.0, 115.0]})
    higher_close = pd.DataFrame({"asset": [100.0, 101.0, 102.0, 104.0, 107.0, 111.0]})

    regime = higher_timeframe_regime_filters(
        close,
        higher_close,
        lower_fast=2,
        lower_slow=3,
        higher_fast=2,
        higher_slow=4,
        trend_window=3,
        baseline_window=4,
    )

    assert isinstance(regime, HigherTimeframeRegimeFilters)
    assert regime.bullish_regime["asset"].iloc[-1]
    assert not regime.bearish_regime["asset"].iloc[-1]
    assert regime.alignment_score["asset"].iloc[-1] > 0.0


def _frame_regime() -> RegimeFilters:
    high, low, close = _frame_inputs()
    return volatility_regime_filters(
        high,
        low,
        close,
        vol_window=3,
        baseline_window=4,
        persistence_window=5,
        variance_lag=2,
        hurst_trend=0.48,
    )


def _frame_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    close = pd.DataFrame(
        {"asset": [100.0, 101.0, 103.0, 106.0, 110.0, 115.0, 121.0, 128.0]}
    )
    high = close + pd.DataFrame(
        {"asset": [1.0, 1.0, 1.5, 1.5, 2.0, 2.0, 2.5, 2.5]}
    )
    low = close - pd.DataFrame(
        {"asset": [1.0, 1.0, 1.5, 1.5, 2.0, 2.0, 2.5, 2.5]}
    )
    return high, low, close
