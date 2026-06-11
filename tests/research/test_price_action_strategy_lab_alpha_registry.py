from __future__ import annotations

from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.projects.price_action_strategy_lab.alpha_registry import alpha_spec
from research.projects.price_action_strategy_lab.alpha_registry import build_alpha_registry
from research.projects.price_action_strategy_lab.alpha_specs import DEFAULT_ALPHA_SPECS
from research.projects.price_action_strategy_lab.alpha_specs import default_alpha_registry
from research.projects.price_action_strategy_lab.expression_modes import (
    cross_sectional_quintile,
)
from research.projects.price_action_strategy_lab.expression_modes import (
    time_series_threshold,
)


def test_default_alpha_registry_is_explicit_and_immutable() -> None:
    registry = default_alpha_registry()

    assert len(registry.specs) == 25
    assert "fisher_transform_reversal_10" in registry.by_name
    assert registry.by_name["fisher_transform_reversal_10"].family == "reversal_exhaustion"
    assert "failed_breakout_score_20" in registry.by_name
    assert registry.by_name["failed_breakout_score_20"].family == "breakout_continuation"
    assert "hybrid_confirmation" in registry.by_name
    assert registry.by_name["hybrid_confirmation"].family == "volume_confirmation"
    assert "breakout_20" in registry.by_name
    assert registry.by_name["breakout_20"].family == "breakout_continuation"
    assert "supertrend_direction_10" in registry.by_name
    assert registry.by_name["supertrend_direction_10"].family == "trend_following"
    assert "opening_gap_regime_score" in registry.by_name
    assert registry.by_name["opening_gap_regime_score"].family == "gap_reaction"
    assert "doji_reversal_score" in registry.by_name
    assert registry.by_name["doji_reversal_score"].family == "reversal_exhaustion"
    with pytest.raises(TypeError):
        registry.by_name["new"] = registry.specs[0]  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        registry.specs[0].name = "changed"  # type: ignore[misc]


def test_registry_rejects_duplicate_alpha_names() -> None:
    with pytest.raises(ValueError, match="duplicate alpha spec"):
        build_alpha_registry((DEFAULT_ALPHA_SPECS[0], DEFAULT_ALPHA_SPECS[0]))


def test_alpha_spec_decorator_returns_buildable_spec() -> None:
    @alpha_spec(
        name="toy",
        family="test",
        description="toy alpha",
        inputs=("close",),
        expression_modes=("time_series_threshold",),
    )
    def toy_alpha(panel: Alpha101Panel) -> pd.DataFrame:
        return panel.close.pct_change()

    signal = toy_alpha.builder(_panel())

    assert toy_alpha.name == "toy"
    assert toy_alpha.inputs == ("close",)
    assert signal.shape == (6, 5)


def test_cross_sectional_quintile_builds_long_short_result() -> None:
    signal = pd.DataFrame(
        [[1.0, 2.0, 3.0, 4.0, 5.0], [5.0, 4.0, 3.0, 2.0, 1.0]],
        columns=list("abcde"),
    )
    future = pd.DataFrame(0.01, index=signal.index, columns=signal.columns)

    result = cross_sectional_quintile(signal, future, min_names=5, cost_bps=0.0)

    assert result.mode == "cross_sectional_quintile"
    assert result.positions.iloc[0]["e"] == pytest.approx(0.5)
    assert result.positions.iloc[0]["d"] == pytest.approx(0.5)
    assert result.positions.iloc[0]["a"] == pytest.approx(-1.0)
    assert result.active.tolist() == [True, True]
    assert result.gross_return.iloc[0] == pytest.approx(0.0)


def test_time_series_threshold_uses_stock_local_signal() -> None:
    signal = pd.DataFrame(
        [[1.0, -1.0, 0.0], [2.0, -2.0, 1.0]],
        columns=list("abc"),
    )
    future = pd.DataFrame(
        [[0.03, -0.01, 0.10], [0.02, -0.02, 0.01]],
        columns=list("abc"),
    )

    result = time_series_threshold(signal, future, min_names=1, cost_bps=0.0)

    assert result.mode == "time_series_threshold"
    assert result.positions.iloc[0]["a"] == pytest.approx(1.0)
    assert result.positions.iloc[0]["b"] == pytest.approx(-1.0)
    assert result.positions.iloc[0]["c"] == pytest.approx(0.0)
    assert result.net_return.iloc[0] == pytest.approx(0.04)


def _panel() -> Alpha101Panel:
    dates = pd.date_range("2024-01-01", periods=6)
    frame = pd.DataFrame(
        {
            "a": [10.0, 11.0, 12.0, 11.0, 10.0, 9.0],
            "b": [20.0, 19.0, 18.0, 19.0, 20.0, 21.0],
            "c": [30.0, 31.0, 30.0, 31.0, 30.0, 31.0],
            "d": [40.0, 39.0, 40.0, 39.0, 40.0, 39.0],
            "e": [50.0, 51.0, 52.0, 53.0, 54.0, 55.0],
        },
        index=dates,
    )
    active = pd.DataFrame(True, index=frame.index, columns=frame.columns)
    returns = frame.pct_change()
    return Alpha101Panel(
        name="toy",
        open=frame,
        high=frame + 1.0,
        low=frame - 1.0,
        close=frame,
        adj_close=frame,
        volume=frame * 100.0,
        vwap=frame,
        returns=returns,
        active_mask=active,
        high_vol_mask=active,
        constituents=tuple(frame.columns),
        industry={symbol: "test" for symbol in frame.columns},
        pit_risk="test",
    )
