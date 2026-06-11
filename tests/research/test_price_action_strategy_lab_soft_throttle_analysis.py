from __future__ import annotations

from pathlib import Path
from typing import cast

import pandas as pd

from research.projects.price_action_strategy_lab.soft_throttle_analysis import SoftThrottleConfig
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _exposure_row
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _variant_multipliers


def test_variant_multipliers_map_good_neutral_and_adverse_states() -> None:
    intensity = pd.Series([0.0, 0.2, 0.5, 0.8, 1.0])
    recommendation = _recommendation(side="high", threshold=0.8, quantile=0.8)

    multipliers = _variant_multipliers(intensity, recommendation)

    assert multipliers["hard_gate"].tolist() == [0.0, 0.0, 0.0, 1.0, 1.0]
    assert multipliers["soft_conservative"].tolist() == [0.5, 0.5, 0.5, 1.0, 1.0]
    assert multipliers["soft_aggressive"].tolist() == [0.25, 1.0, 1.0, 1.25, 1.25]
    assert multipliers["drawdown_only_throttle"].tolist() == [0.5, 1.0, 1.0, 1.0, 1.0]


def test_exposure_row_reports_reduced_positive_and_negative_windows() -> None:
    index = pd.date_range("2024-01-01", periods=30, freq="D")
    baseline = pd.Series([0.01] * 15 + [-0.01] * 15, index=index)
    multiplier = pd.Series([0.5] * 10 + [1.0] * 10 + [0.5] * 10, index=index)
    returns = baseline * multiplier
    turnover = pd.Series(0.10, index=index)
    config = SoftThrottleConfig(alpha_names=("alpha_a",), cache_dir=Path("."))

    row = _exposure_row("alpha_a", "soft_conservative", baseline, returns, turnover, multiplier, config)

    assert row["active_day_pct"] == 100.0
    assert cast(float, row["avg_exposure_multiplier"]) < 1.0
    assert cast(int, row["positive_windows_reduced"]) > 0
    assert cast(int, row["negative_windows_reduced"]) > 0


def _recommendation(side: str, threshold: float, quantile: float) -> pd.Series:
    return pd.Series(
        {
            "indicator": "test_indicator",
            "side": side,
            "threshold": threshold,
            "quantile": quantile,
        }
    )
