from __future__ import annotations

import numpy as np
import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.projects.price_action_strategy_lab.activator_specs import default_activator_registry
from research.projects.price_action_strategy_lab.activator_suite import build_activator_masks
from research.projects.price_action_strategy_lab.activator_suite import select_family_activators


def test_build_activator_masks_returns_boolean_frames() -> None:
    panel = _panel()
    masks = build_activator_masks(panel, default_activator_registry())
    assert "trend_alignment" in masks
    assert "mean_reversion_environment" in masks
    for mask in masks.values():
        assert mask.shape == panel.close.shape
        assert mask.dtypes.nunique() == 1
    assert bool(masks["trend_alignment"].fillna(False).any().any())


def test_select_family_activators_prefers_positive_lift() -> None:
    screen = pd.DataFrame(
        [
            {
                "family": "trend_following",
                "activator": "trend_alignment",
                "lift_bps": 12.0,
                "gated_net_mean_bps": 20.0,
                "activation_corr": 0.4,
                "activation_coverage": 0.5,
                "alpha": "alpha_a",
            },
            {
                "family": "trend_following",
                "activator": "volatility_expansion",
                "lift_bps": -3.0,
                "gated_net_mean_bps": 5.0,
                "activation_corr": -0.2,
                "activation_coverage": 0.2,
                "alpha": "alpha_a",
            },
            {
                "family": "reversal_exhaustion",
                "activator": "mean_reversion_environment",
                "lift_bps": -5.0,
                "gated_net_mean_bps": -1.0,
                "activation_corr": -0.1,
                "activation_coverage": 0.3,
                "alpha": "alpha_b",
            },
        ]
    )
    selection = select_family_activators(screen)
    trend = selection.loc[selection["family"].eq("trend_following")].iloc[0]
    reversal = selection.loc[selection["family"].eq("reversal_exhaustion")].iloc[0]
    assert trend["selected_activator"] == "trend_alignment"
    assert trend["decision"] == "activate"
    assert reversal["selected_activator"] == "none"
    assert reversal["decision"] == "abstain"


def _panel() -> Alpha101Panel:
    index = pd.date_range("2024-01-01", periods=80, freq="B")
    columns = ["AAA", "BBB", "CCC"]
    close = pd.DataFrame(
        {
            "AAA": np.linspace(100.0, 150.0, len(index)),
            "BBB": np.linspace(150.0, 90.0, len(index)),
            "CCC": 110.0 + 5.0 * np.sin(np.linspace(0.0, 8.0, len(index))),
        },
        index=index,
    )
    open_ = close.shift(1).fillna(close.iloc[0])
    high = close * 1.01
    low = close * 0.99
    volume = pd.DataFrame(
        1_000_000.0 + np.repeat(np.arange(len(index))[:, None] * 1_000.0, len(columns), axis=1),
        index=index,
        columns=columns,
    )
    returns = close.pct_change().fillna(0.0)
    active = pd.DataFrame(True, index=index, columns=columns)
    high_vol = pd.DataFrame(True, index=index, columns=columns)
    industry = pd.Series({"AAA": "Tech", "BBB": "Finance", "CCC": "Energy"})
    constituents = pd.DataFrame(True, index=index, columns=columns)
    return Alpha101Panel(
        name="test",
        open=open_,
        high=high,
        low=low,
        close=close,
        adj_close=close,
        volume=volume,
        vwap=close,
        returns=returns,
        active_mask=active,
        high_vol_mask=high_vol,
        constituents=constituents,
        industry=industry,
        pit_risk="none",
    )
