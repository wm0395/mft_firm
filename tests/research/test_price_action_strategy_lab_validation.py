from __future__ import annotations

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.projects.price_action_strategy_lab.backtest_modes import BacktestConfig
from research.projects.price_action_strategy_lab.backtest_modes import run_backtest
from research.projects.price_action_strategy_lab.costs import turnover_cost
from research.projects.price_action_strategy_lab.selectors import SELECTORS
from research.projects.price_action_strategy_lab.validation_pipeline import SelectorHardeningConfig
from research.projects.price_action_strategy_lab.validation_pipeline import SignalBundle
from research.projects.price_action_strategy_lab.validation_pipeline import ValidationConfig
from research.projects.price_action_strategy_lab.validation_pipeline import run_validation_suite
from research.projects.price_action_strategy_lab.validation_reports import write_validation_reports


def test_validation_suite_builds_reports(tmp_path) -> None:
    panel = _panel()
    bundles = (_bundle(panel),)
    rows = pd.DataFrame(
        [
            {"alpha": "toy", "mode": "cross_sectional_quintile", "horizon": 1, "cost_bps": 0.0},
            {"alpha": "toy", "mode": "ranked_long_only", "horizon": 1, "cost_bps": 0.0},
        ]
    )
    config = ValidationConfig(
        enabled=True,
        schemes=("walk_forward", "purged", "embargo"),
        outer_folds=2,
        train_size=4,
        test_size=2,
        step_size=2,
        lookahead=1,
        embargo=1,
        bootstrap_reps=20,
        bootstrap_block_length=2,
        target_cost_bps=0.0,
        min_active_days=1,
    )
    hardening = SelectorHardeningConfig(
        lower_bound_margin_bps=0.0,
        turnover_penalty_bps=0.0,
        instability_penalty_bps=0.0,
        minimum_fold_pass_rate=0.0,
        abstain_lower_bound_bps=-10_000.0,
        primary_scheme="embargo",
    )

    artifacts = run_validation_suite(panel, bundles, rows, config, hardening, workers=1)
    paths = write_validation_reports(tmp_path, artifacts)

    assert not artifacts.folds.empty
    assert not artifacts.summary.empty
    assert not artifacts.selector_results.empty
    assert artifacts.decision.iloc[0]["decision"] in {"promote", "research_only"}
    assert all(path.exists() for path in paths.values())


def test_lower_bound_selector_abstains_on_negative_candidate() -> None:
    dates = pd.date_range("2026-01-01", periods=4)
    signal = pd.DataFrame({"AAA": [-1.0, -1.0, -1.0, -1.0]}, index=dates)
    forward = pd.DataFrame({"AAA": [-0.02, -0.01, -0.03, -0.02]}, index=dates)
    result = run_backtest(
        signal,
        forward,
        BacktestConfig("bad", "ranked_long_only", 1, turnover_cost(0.0), min_names=1),
    )

    decision = next(spec for spec in SELECTORS if spec.name == "lower_bound_net_bps_abstain").builder((result,))

    assert decision.abstain
    assert decision.reason_code == "no_positive_lower_bound"


def _bundle(panel: Alpha101Panel) -> SignalBundle:
    signal = pd.DataFrame(
        {"AAA": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0], "BBB": [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0]},
        index=panel.close.index,
    )
    return SignalBundle(
        alpha="toy",
        signal=signal,
        rank_pct=signal.rank(axis=1, pct=True, method="average"),
        backend="cpu",
    )


def _panel() -> Alpha101Panel:
    dates = pd.date_range("2026-01-01", periods=6)
    close = pd.DataFrame(
        {
            "AAA": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
            "BBB": [20.0, 19.0, 18.0, 17.0, 16.0, 15.0],
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
