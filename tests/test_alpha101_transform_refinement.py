from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
import sys

import pandas as pd  # type: ignore[import-untyped]
import pytest


NOTEBOOK_ROOT = Path(__file__).resolve().parents[1] / "research/notebooks/alpha_001"
if str(NOTEBOOK_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_ROOT))

MODULE_PATH = NOTEBOOK_ROOT / "research/alpha101_factory.py"
SPEC = spec_from_file_location("alpha101_factory_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE: Any = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_family_transforms_include_smoothed_threshold_variants() -> None:
    transforms = MODULE.family_transforms("price_reversal")
    assert "ewm3_threshold_top_bottom" in transforms
    assert "ewm5_threshold_top_bottom" in transforms
    assert "ewm10_threshold_top_bottom" in transforms
    volume = MODULE.family_transforms("volume_liquidity")
    volatility = MODULE.family_transforms("volatility_range")
    residual = MODULE.family_transforms("correlation_relative_value")
    assert "ewm3_threshold_top_bottom" in volume
    assert "ewm5_threshold_top_bottom" in volatility
    assert "ewm10_threshold_top_bottom" in residual


def test_portfolio_signal_transforms_include_smoothed_threshold_variants() -> None:
    volume = MODULE.portfolio_signal_transforms("volume_liquidity")
    vol = MODULE.portfolio_signal_transforms("volatility_range")
    price = MODULE.portfolio_signal_transforms("price_reversal")
    assert "ewm3_threshold_top_bottom" in volume
    assert "ewm5_threshold_top_bottom" in vol
    assert "ewm10_threshold_top_bottom" in price
    residual = MODULE.portfolio_signal_transforms("correlation_relative_value")
    assert "ewm3_threshold_top_bottom" in residual
    assert "ewm5_threshold_top_bottom" in residual
    assert "ewm10_threshold_top_bottom" in residual


def test_smoothed_threshold_top_bottom_keeps_extremes() -> None:
    frame = pd.DataFrame({"A": [1.0, 2.0, 3.0, 4.0], "B": [4.0, 3.0, 2.0, 1.0], "C": [2.0, 2.0, 2.0, 2.0]})
    result = MODULE.smoothed_threshold_top_bottom(frame, 3, 2)
    assert result.iloc[-1].dropna().index.tolist() == ["A"]
    assert result.iloc[-1].isna().sum() == 2


def test_portfolio_row_from_backtests_matches_direct_row() -> None:
    index = pd.date_range("2024-01-01", periods=5)
    weights = pd.DataFrame({"A": [0.5, 0.6, 0.4, 0.0, 0.5], "B": [0.5, 0.4, 0.6, 1.0, 0.5]}, index=index)
    benchmark = pd.DataFrame({"A": [0.5] * 5, "B": [0.5] * 5}, index=index)
    next_returns = pd.DataFrame({"A": [0.01, 0.02, -0.01, 0.03, 0.0], "B": [0.0, 0.01, 0.02, -0.01, 0.0]}, index=index)
    direct = MODULE.portfolio_row("p", "a", "f", "t", "m", "s", 20.0, weights, benchmark, next_returns)
    alpha_bt = MODULE.backtests_by_cost(weights, next_returns, MODULE.COST_GRID)[20.0]
    benchmark_bt = MODULE.backtests_by_cost(benchmark, next_returns, MODULE.COST_GRID)[20.0]
    labels = {"panel": "p", "alpha_id": "a", "family": "f", "signal_transform": "t", "mask": "m", "strategy": "s"}
    optimized = MODULE.portfolio_row_from_backtests(labels, 20.0, alpha_bt, benchmark_bt, MODULE.average_names(weights))

    assert optimized.keys() == direct.keys()
    for key, value in direct.items():
        assert optimized[key] == value or pd.isna(optimized[key]) and pd.isna(value)


def test_partial_rebalance_matches_legacy_daily_loop() -> None:
    index = pd.date_range("2024-01-01", periods=8)
    targets = pd.DataFrame(
        {
            "A": [0.6, 0.7, 0.8, 0.2, 0.4, 0.5, 0.1, 0.3],
            "B": [0.4, 0.3, 0.2, 0.8, 0.6, 0.5, 0.9, 0.7],
        },
        index=index,
    )
    rebalance = pd.Series([True, False, False, True, False, False, True, False], index=index)
    expected = legacy_carry_on_rebalance(targets, rebalance, 0.5)
    result = MODULE.carry_on_rebalance(targets, rebalance, partial=0.5)

    pd.testing.assert_frame_equal(result, expected)


def test_build_portfolio_weights_matches_legacy_daily_targets() -> None:
    index = pd.bdate_range("2024-01-01", periods=15)
    signal = pd.DataFrame(
        {
            "A": range(15),
            "B": range(15, 0, -1),
            "C": [1, 3, 2, 5, 4, 8, 7, 6, 9, 11, 10, 12, 14, 13, 15],
        },
        index=index,
        dtype=float,
    )
    mask = pd.DataFrame(True, index=index, columns=signal.columns)
    for strategy in ("equal_weight", "top10", "long_short_10", "score_tilt", "overlay20", "ewm3_overlay20", "ewm5_overlay20"):
        expected = legacy_build_portfolio_weights(signal, mask, strategy)
        result = MODULE.build_portfolio_weights(signal, mask, strategy)
        pd.testing.assert_frame_equal(result, expected)


def test_write_alpha_panel_cache_writes_without_readback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def fake_evaluate(args: tuple[str, str]) -> dict[str, pd.DataFrame]:
        calls.append(args)
        return {name: pd.DataFrame({"alpha_id": [args[0]], "panel": [args[1]]}) for name in MODULE.TASK_TABLES}

    monkeypatch.setattr(MODULE, "ALPHA101_ARTIFACT_DIR", tmp_path)
    monkeypatch.setattr(MODULE, "evaluate_alpha_panel", fake_evaluate)

    assert MODULE.write_alpha_panel_cache(("alpha001", "nifty500")) == ("alpha001", "nifty500")
    assert calls == [("alpha001", "nifty500")]
    for path in MODULE.task_cache_paths("alpha001", "nifty500").values():
        assert path.exists()

    assert MODULE.write_alpha_panel_cache(("alpha001", "nifty500")) == ("alpha001", "nifty500")
    assert calls == [("alpha001", "nifty500")]


def legacy_build_portfolio_weights(signal: pd.DataFrame, mask: pd.DataFrame, strategy: str) -> pd.DataFrame:
    rebalance = MODULE.weekly_rebalance_mask(signal.index)
    if strategy == "equal_weight":
        return MODULE.carry_on_rebalance(MODULE.equal_weight_targets(mask), rebalance)
    if strategy == "top10":
        return MODULE.carry_on_rebalance(MODULE.top_bucket_weights(signal, mask, 10), rebalance)
    if strategy == "long_short_10":
        return MODULE.carry_on_rebalance(MODULE.long_short_weights(signal, mask, 10), rebalance)
    if strategy == "score_tilt":
        return MODULE.carry_on_rebalance(MODULE.score_tilt_weights(signal, mask, 0.25), rebalance)
    if strategy == "overlay20":
        return MODULE.carry_on_rebalance(MODULE.overlay_weights(signal, mask, 0.20), rebalance, partial=0.50)
    if strategy == "ewm3_overlay20":
        signal = signal.ewm(span=3, min_periods=2, adjust=False).mean()
        return MODULE.carry_on_rebalance(MODULE.overlay_weights(signal, mask, 0.20), rebalance, partial=0.50)
    if strategy == "ewm5_overlay20":
        signal = signal.ewm(span=5, min_periods=3, adjust=False).mean()
        return MODULE.carry_on_rebalance(MODULE.overlay_weights(signal, mask, 0.20), rebalance, partial=0.50)
    raise ValueError(strategy)


def legacy_carry_on_rebalance(targets: pd.DataFrame, rebalance_mask: pd.Series, partial: float) -> pd.DataFrame:
    weights = pd.DataFrame(0.0, index=targets.index, columns=targets.columns)
    last = pd.Series(0.0, index=targets.columns)
    for i, date in enumerate(targets.index):
        if i == 0 or bool(rebalance_mask.loc[date]):
            target = targets.loc[date].fillna(0.0)
            target = last + partial * (target - last)
            total = target.abs().sum()
            if total > 0 and target.sum() > 0:
                target = target / target.sum()
            last = target.reindex(targets.columns).fillna(0.0)
        weights.loc[date] = last
    return weights
