from __future__ import annotations

import pandas as pd
import pytest

from project.alpha_math.volatility_estimators import (
    close_to_close_volatility,
    garman_klass_volatility,
    parkinson_volatility,
    rogers_satchell_volatility,
    volatility_estimates,
    yang_zhang_volatility,
)


def test_range_based_volatility_matches_known_values() -> None:
    open_ = pd.Series([10.0, 10.0, 10.0, 10.0])
    high = pd.Series([12.0, 12.0, 12.0, 12.0])
    low = pd.Series([8.0, 8.0, 8.0, 8.0])
    close = pd.Series([11.0, 11.0, 11.0, 11.0])

    close_to_close = close_to_close_volatility(close, period=3)
    parkinson = parkinson_volatility(high, low, period=3)
    garman_klass = garman_klass_volatility(open_, high, low, close, period=3)
    rogers_satchell = rogers_satchell_volatility(open_, high, low, close, period=3)
    yang_zhang = yang_zhang_volatility(open_, high, low, close, period=3)

    assert close_to_close.iloc[-1] == pytest.approx(0.0)
    assert parkinson.iloc[-1] == pytest.approx(3.8655476541403453)
    assert garman_klass.iloc[-1] == pytest.approx(4.453128175076204)
    assert rogers_satchell.iloc[-1] == pytest.approx(4.680287004346153)
    assert yang_zhang.iloc[-1] == pytest.approx(4.435676650079243)


def test_volatility_estimates_support_dataframes() -> None:
    open_ = pd.DataFrame({"asset": [10.0, 10.0, 10.0, 10.0]})
    high = pd.DataFrame({"asset": [12.0, 12.0, 12.0, 12.0]})
    low = pd.DataFrame({"asset": [8.0, 8.0, 8.0, 8.0]})
    close = pd.DataFrame({"asset": [11.0, 11.0, 11.0, 11.0]})

    estimates = volatility_estimates(open_, high, low, close, period=3)

    assert isinstance(estimates.close_to_close, pd.DataFrame)
    assert estimates.close_to_close.columns.tolist() == ["asset"]
    assert estimates.close_to_close.iloc[-1, 0] == pytest.approx(0.0)
    assert estimates.yang_zhang.iloc[-1, 0] == pytest.approx(4.435676650079243)
