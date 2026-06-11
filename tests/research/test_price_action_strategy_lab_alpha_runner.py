from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.projects.price_action_strategy_lab.alpha_registry import alpha_spec
from research.projects.price_action_strategy_lab.alpha_registry import build_alpha_registry
from research.projects.price_action_strategy_lab.alpha_runner import AlphaSuiteConfig
from research.projects.price_action_strategy_lab.alpha_runner import run_alpha_suite
from research.projects.price_action_strategy_lab.alpha_runner import write_alpha_suite_reports


def test_alpha_suite_caches_signals_and_compares_modes(tmp_path: Path) -> None:
    registry = build_alpha_registry((_toy_alpha(),))
    config = AlphaSuiteConfig(
        alpha_names=("toy_reversal",),
        modes=("cross_sectional_quintile", "time_series_threshold"),
        horizons=(1,),
        cost_bps=(0.0,),
        cache_dir=tmp_path / "cache",
        max_workers=2,
        min_names=3,
    )

    first = run_alpha_suite(_panel(), registry, config)
    second = run_alpha_suite(_panel(), registry, config)
    paths = write_alpha_suite_reports(second, tmp_path / "reports")

    assert first.cache_events["cache_hit"].tolist() == [False]
    assert second.cache_events["cache_hit"].tolist() == [True]
    assert first.cache_events["rank_cache_hit"].tolist() == [False]
    assert second.cache_events["rank_cache_hit"].tolist() == [True]
    assert first.rows["backtest_cache_hit"].tolist() == [False, False]
    assert second.rows["backtest_cache_hit"].tolist() == [True, True]
    assert second.rows["compute_backend"].tolist() == ["cpu", "cpu"]
    assert set(second.rows["mode"]) == {"cross_sectional_quintile", "time_series_threshold"}
    assert second.mode_comparison.shape[0] == 2
    assert all(path.exists() for path in paths)


def _toy_alpha():
    @alpha_spec(
        name="toy_reversal",
        family="test",
        description="toy reversal",
        inputs=("close",),
        expression_modes=("cross_sectional_quintile", "time_series_threshold"),
    )
    def build(panel: Alpha101Panel) -> pd.DataFrame:
        return panel.close.rank(axis=1, pct=True)

    return build


def _panel() -> Alpha101Panel:
    dates = pd.date_range("2026-01-01", periods=6)
    close = pd.DataFrame(
        {
            "AAA": [10.0, 11.0, 12.0, 13.0, 12.0, 11.0],
            "BBB": [20.0, 19.0, 18.0, 17.0, 18.0, 19.0],
            "CCC": [30.0, 31.0, 30.0, 31.0, 30.0, 31.0],
        },
        index=dates,
    )
    active = pd.DataFrame(True, index=dates, columns=close.columns)
    return Alpha101Panel(
        name="toy_panel",
        open=close,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        adj_close=close,
        volume=close * 100.0,
        vwap=close,
        returns=close.pct_change(),
        active_mask=active,
        high_vol_mask=active,
        constituents=pd.DataFrame({"Symbol": close.columns}),
        industry=pd.Series("test", index=close.columns),
        pit_risk="test",
    )
