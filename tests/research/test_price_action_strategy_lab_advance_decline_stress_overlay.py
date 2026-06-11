from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.projects.price_action_strategy_lab.advance_decline_stress_overlay import _config
from research.projects.price_action_strategy_lab.advance_decline_stress_overlay import _fast_trade_diagnostics
from research.projects.price_action_strategy_lab.advance_decline_stress_overlay import _multiplier
from research.projects.price_action_strategy_lab.advance_decline_stress_overlay import _stress_features
from research.projects.price_action_strategy_lab.narrow_falsification_stats import trade_diagnostics
from research.projects.price_action_strategy_lab.run_activator_suite import _read_config
from tests.research.test_price_action_strategy_lab_external_stress_diagnostics import _panel


CONFIG = Path("research/projects/price_action_strategy_lab/config/advance_decline_stress_overlay_hypothesis.yaml")


def test_only_pre_registered_stress_signals_are_used() -> None:
    config = _config(_read_config(CONFIG))

    assert {hyp.signal for hyp in config.hypotheses} == {
        "advance_decline_ratio_lag1_low",
        "nifty_return_5d_lag1_low",
        "advance_decline_ratio_5d_lag1_low",
        "composite_ad1d_low_and_nifty5d_low",
        "composite_ad1d_low_or_nifty5d_low",
        "breadth_risk_off_lag1_high",
    }


def test_reduce_only_never_increases_exposure() -> None:
    config = _config(_read_config(CONFIG))
    reduce_hyp = next(hyp for hyp in config.hypotheses if hyp.variant == "reduce_only")

    assert all(float(row["up"]) <= 1.0 for row in reduce_hyp.multipliers)
    assert all(float(row["down"]) <= 1.0 for row in reduce_hyp.multipliers)


def test_multiplier_reduces_only_in_stress_state() -> None:
    intensity = pd.Series([0.1, 0.9])

    mult = _multiplier(intensity, 0.5, {"down": 0.5, "up": 1.0})

    assert mult.tolist() == [1.0, 0.5]


def test_stress_features_are_lagged_and_no_event_labels() -> None:
    features = _stress_features(_panel())

    assert "event_label" not in features
    assert pd.isna(features["advance_decline_ratio_lag1_low"].iloc[0])
    assert "composite_ad1d_low_and_nifty5d_low" in features


def test_no_missing_external_sources_are_used() -> None:
    config = _config(_read_config(CONFIG))

    assert all("vix" not in hyp.signal for hyp in config.hypotheses)
    assert all("fpi" not in hyp.signal for hyp in config.hypotheses)
    assert all("usdinr" not in hyp.signal for hyp in config.hypotheses)
    assert all("crude" not in hyp.signal for hyp in config.hypotheses)


def test_fast_trade_diagnostics_reconciles_with_reference() -> None:
    index = pd.date_range("2025-01-01", periods=3)
    positions = pd.DataFrame({"A": [1.0, -1.0, 0.0], "B": [0.5, 1.0, -1.0]}, index=index)
    future = pd.DataFrame({"A": [0.03, -0.02, 0.01], "B": [-0.01, 0.04, -0.02]}, index=index)
    multiplier = pd.Series([1.0, 0.5, 1.25], index=index)

    expected = trade_diagnostics(positions, future, multiplier, 10)
    actual = _fast_trade_diagnostics(positions, future, multiplier, 10)

    assert actual == expected
