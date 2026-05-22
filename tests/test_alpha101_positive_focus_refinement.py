from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from pandas.testing import assert_frame_equal  # type: ignore[import-untyped]

ALPHA_ROOT = Path(__file__).resolve().parents[1] / "research" / "notebooks" / "alpha_001"
if str(ALPHA_ROOT) not in sys.path:
    sys.path.insert(0, str(ALPHA_ROOT))

from research.alpha101_engine import (  # type: ignore[import-untyped]  # noqa: E402
    equal_weight_targets,
    normalized_positive,
    overlay_weights,
    winsorized_zscore,
)
from research.alpha101_formulas import Alpha101Formulas  # type: ignore[import-untyped]  # noqa: E402


def _panel(rows: int = 130) -> SimpleNamespace:
    index = pd.date_range("2024-01-01", periods=rows, freq="D")
    base = np.arange(1, rows + 1, dtype=float)
    open_ = pd.DataFrame({"A": base, "B": base * 1.1 + 3.0}, index=index)
    high = open_ + 1.0
    low = open_ - 1.0
    close = open_ + 0.5
    volume = pd.DataFrame({"A": base * 10.0, "B": base * 12.0}, index=index)
    adj_close = close.copy()
    returns = adj_close.pct_change(fill_method=None)
    vwap = (high + low + close) / 3.0
    industry = pd.Series({"A": "tech", "B": "finance"})
    return SimpleNamespace(
        open=open_,
        high=high,
        low=low,
        close=close,
        adj_close=adj_close,
        volume=volume,
        returns=returns,
        vwap=vwap,
        industry=industry,
    )


def _flat_high_panel(rows: int = 25) -> SimpleNamespace:
    index = pd.date_range("2024-01-01", periods=rows, freq="D")
    open_ = pd.DataFrame({"A": np.full(rows, 9.0), "B": np.full(rows, 8.5)}, index=index)
    high = pd.DataFrame({"A": np.full(rows, 10.0), "B": np.full(rows, 10.0)}, index=index)
    low = pd.DataFrame({"A": np.full(rows, 8.0), "B": np.full(rows, 7.5)}, index=index)
    close = pd.DataFrame({"A": np.full(rows, 9.5), "B": np.full(rows, 9.0)}, index=index)
    volume = pd.DataFrame({"A": np.arange(1, rows + 1) * 10.0, "B": np.arange(1, rows + 1) * 12.0}, index=index)
    adj_close = close.copy()
    returns = adj_close.pct_change(fill_method=None)
    vwap = (high + low + close) / 3.0
    industry = pd.Series({"A": "tech", "B": "finance"})
    return SimpleNamespace(
        open=open_,
        high=high,
        low=low,
        close=close,
        adj_close=adj_close,
        volume=volume,
        returns=returns,
        vwap=vwap,
        industry=industry,
    )


def test_overlay_weights_winsorizes_before_sizing() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    signal = pd.DataFrame(
        {"A": [1.0, 1.0, 1.0], "B": [2.0, 2.0, 2.0], "C": [100.0, 100.0, 100.0]},
        index=index,
    )
    mask = pd.DataFrame(True, index=index, columns=signal.columns)

    z = winsorized_zscore(signal.where(mask)).where(mask, 0.0)
    active = z.div(z.abs().sum(axis=1).replace(0.0, np.nan), axis=0).fillna(0.0) * 0.20
    expected = normalized_positive(equal_weight_targets(mask) + active).where(mask, 0.0)

    assert_frame_equal(overlay_weights(signal, mask), expected)


def test_positive_focus_formulas_emit_signal() -> None:
    panel = _panel()
    formulas = Alpha101Formulas(panel)

    alpha018 = formulas.alpha018()
    alpha024 = formulas.alpha024()
    alpha040 = formulas.alpha040()

    assert alpha018.notna().any().any()
    assert alpha024.iloc[110:].notna().any().any()
    assert alpha040.notna().any().any()


def test_alpha023_stays_nan_outside_trigger_rows() -> None:
    out = Alpha101Formulas(_flat_high_panel()).alpha023()

    assert out.iloc[20:].isna().all().all()
