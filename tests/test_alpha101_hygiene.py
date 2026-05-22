from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

ALPHA_ROOT = Path(__file__).resolve().parents[1] / "research" / "notebooks" / "alpha_001"
if str(ALPHA_ROOT) not in sys.path:
    sys.path.insert(0, str(ALPHA_ROOT))

from research.alpha101_formulas import Alpha101Formulas  # type: ignore[import-not-found]  # noqa: E402


def _panel(rows: int = 21) -> SimpleNamespace:
    index = pd.date_range("2024-01-01", periods=rows, freq="D")
    base = np.arange(1, rows + 1, dtype=float)
    open_ = pd.DataFrame({"A": base, "B": base + 1.0}, index=index)
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


def test_alpha006_preserves_initial_nan_window() -> None:
    out = Alpha101Formulas(_panel()).alpha006()
    assert out.iloc[:9].isna().all().all()
    assert out.iloc[9:].notna().any().any()


def test_alpha023_preserves_warmup_nan_rows() -> None:
    out = Alpha101Formulas(_panel()).alpha023()
    assert out.iloc[:2].isna().all().all()
    assert out.iloc[19:].notna().any().any()


def test_alpha034_keeps_warmup_rows_nan() -> None:
    out = Alpha101Formulas(_panel()).alpha034()
    assert out.iloc[:4].isna().all().all()
    assert out.iloc[4:].notna().any().any()
