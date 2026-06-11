from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.projects.price_action_strategy_lab.breadth_only_diagnostic import concentration_diagnostics
from research.projects.price_action_strategy_lab.breadth_only_diagnostic import fold_concentration_row
from research.projects.price_action_strategy_lab.breadth_only_diagnostic import threshold_stability
from research.projects.price_action_strategy_lab.run_activator_suite import _read_config
from research.projects.price_action_strategy_lab.run_stress_confirmation import _config


def test_only_breadth_candidate_is_registered() -> None:
    raw = _read_config(Path("research/projects/price_action_strategy_lab/config/support_trendline_breadth_only_diagnostic.yaml"))
    config = _config(raw)

    assert tuple(variant.variant_id for variant in config.variants) == ("baseline", "breadth_risk_off_high")
    assert config.variants[1].indicators == ("breadth_risk_off",)


def test_event_labels_are_not_model_inputs() -> None:
    raw = _read_config(Path("research/projects/price_action_strategy_lab/config/support_trendline_breadth_only_diagnostic.yaml"))
    config = _config(raw)

    assert all("event_label" not in variant.indicators for variant in config.variants)


def test_fold_concentration_metrics_are_correct() -> None:
    frame = pd.DataFrame({"fold": [1, 2, 3, 4], "delta_return_pct": [3.0, 2.0, -1.0, 0.5]})

    row = fold_concentration_row("breadth_risk_off_high", 25.0, frame)

    assert row["helped_folds"] == 3
    assert row["hurt_folds"] == 1
    assert row["top_1_fold_contribution"] == 3.0 / 4.5
    assert row["excluding_best_fold_delta"] == 1.5


def test_threshold_stability_excludes_baseline() -> None:
    result = threshold_stability(_fold_frame())

    assert result["variant"].tolist() == ["breadth_risk_off_high"]
    assert result.iloc[0]["fold_count"] == 2


def test_cost_outputs_are_separated() -> None:
    result = concentration_diagnostics(pd.concat([_fold_frame(), _fold_frame().assign(cost_bps=50.0)]))

    assert set(result["cost_bps"]) == {25.0, 50.0}


def _fold_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _row("baseline", 1, 0.0, 1.0),
            _row("baseline", 2, 0.0, 1.0),
            _row("breadth_risk_off_high", 1, 0.5, 0.8),
            _row("breadth_risk_off_high", 2, -0.2, 1.1),
        ]
    )


def _row(variant: str, fold: int, delta: float, exposure: float) -> dict[str, object]:
    return {
        "variant": variant,
        "fold": fold,
        "cost_bps": 25.0,
        "delta_return_pct": delta,
        "selected_threshold": 0.5,
        "selected_quantile": 0.6,
        "avg_exposure": exposure,
    }
