from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.projects.price_action_strategy_lab.external_stress_diagnostics import _baseline_folds
from research.projects.price_action_strategy_lab.external_stress_diagnostics import _config
from research.projects.price_action_strategy_lab.external_stress_diagnostics import _fold_feature_values
from research.projects.price_action_strategy_lab.external_stress_diagnostics import _lagged_feature_panel
from research.projects.price_action_strategy_lab.external_stress_diagnostics import _raw_features
from research.projects.price_action_strategy_lab.external_stress_diagnostics import _shortlist
from research.projects.price_action_strategy_lab.run_activator_suite import _read_config


CONFIG = Path("research/projects/price_action_strategy_lab/config/external_stress_feature_registry.yaml")


def test_external_stress_registry_is_lagged_and_versioned() -> None:
    raw = _read_config(CONFIG)
    config = _config(raw)

    assert raw["version"] == 1
    assert all(item.lag_days >= 1 for item in config.features)
    assert "event_label" not in {item.name for item in config.features}


def test_lagged_feature_panel_has_no_event_labels() -> None:
    panel = _panel()
    raw = _raw_features(panel)
    config = _config(_read_config(CONFIG))

    features = _lagged_feature_panel(raw, config.features, 1)

    assert "event_label" not in features.columns
    assert "breadth_risk_off_lag1" in features.columns
    assert pd.isna(features.loc[0, "breadth_risk_off_lag1"])


def test_baseline_weak_folds_are_derived_from_baseline_only(tmp_path: Path) -> None:
    path = tmp_path / "folds.csv"
    pd.DataFrame(
        [
            {"fold": 1, "variant": "baseline", "test_start": "2024-01-01", "test_end": "2024-01-31", "return_pct": -2.0},
            {"fold": 1, "variant": "gate", "test_start": "2024-01-01", "test_end": "2024-01-31", "return_pct": 9.0},
            {"fold": 2, "variant": "baseline", "test_start": "2024-02-01", "test_end": "2024-02-29", "return_pct": 4.0},
        ]
    ).to_csv(path, index=False)
    raw = _read_config(CONFIG)
    raw["compute"]["baseline_fold_metrics_path"] = str(path)
    raw["compute"]["max_folds"] = 2

    folds = _baseline_folds(_config(raw))

    assert set(folds["variant"]) == {"baseline"}
    assert folds.loc[folds["fold"].eq(1), "bottom_quartile_baseline_fold"].item()


def test_fold_feature_values_do_not_include_event_labels() -> None:
    features = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=4), "x_lag1": [1.0, 2.0, 3.0, 4.0]})
    folds = pd.DataFrame(
        [{"fold": 1, "test_start": "2024-01-02", "test_end": "2024-01-03", "return_pct": -1.0, "bottom_quartile_baseline_fold": True, "bottom_decile_baseline_fold": True}]
    )

    result = _fold_feature_values(features, folds)

    assert result.loc[0, "x_lag1"] == 2.5
    assert "event_label" not in result.columns


def test_shortlist_filters_missing_sources() -> None:
    separation = pd.DataFrame(
        [
            {"feature": "a_lag1", "abs_standardized_difference": 1.0, "auc": 0.8, "oriented_auc": 0.8},
            {"feature": "b_lag1", "abs_standardized_difference": 1.0, "auc": 0.8, "oriented_auc": 0.8},
        ]
    )
    coverage = pd.DataFrame(
        [
            {"feature": "a_lag1", "missing_pct": 0.1, "status": "available"},
            {"feature": "b_lag1", "missing_pct": 1.0, "status": "missing_source"},
        ]
    )
    correlation = pd.DataFrame({"feature": ["a_lag1"], "breadth_risk_off_lag1": [0.2]})

    result = _shortlist(separation, coverage, correlation)

    assert result["feature"].tolist() == ["a_lag1"]


def _panel() -> Alpha101Panel:
    dates = pd.date_range("2024-01-01", periods=8)
    columns = ["A", "B", "C"]
    close = pd.DataFrame(
        [[10 + i, 20 - i, 30 + (i % 2)] for i in range(8)],
        index=dates,
        columns=columns,
        dtype=float,
    )
    volume = pd.DataFrame(100.0, index=dates, columns=columns)
    active = close.notna()
    constituents = pd.DataFrame({"symbol": columns})
    industry = pd.Series("test", index=columns)
    return Alpha101Panel(
        name="test",
        open=close,
        high=close + 1,
        low=close - 1,
        close=close,
        adj_close=close,
        volume=volume,
        vwap=close,
        returns=close.pct_change(fill_method=None),
        active_mask=active,
        high_vol_mask=active,
        constituents=constituents,
        industry=industry,
        pit_risk="research",
    )
