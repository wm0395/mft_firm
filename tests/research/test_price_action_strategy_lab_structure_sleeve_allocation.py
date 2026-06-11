from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.projects.price_action_strategy_lab.run_activator_suite import _read_config
from research.projects.price_action_strategy_lab.structure_sleeve_allocation import _blend_series
from research.projects.price_action_strategy_lab.structure_sleeve_allocation import _config
from research.projects.price_action_strategy_lab.structure_sleeve_allocation import _event_split
from research.projects.price_action_strategy_lab.structure_sleeve_allocation import _variant_specs


def test_structure_sleeve_config_contains_pre_registered_candidates() -> None:
    raw = _read_config(Path("research/projects/price_action_strategy_lab/config/breadth_risk_off_structure_sleeve_hypothesis.yaml"))
    config = _config(raw)

    assert config.structure == (
        "support_trendline_position_20",
        "support_resistance_position_20",
        "failed_breakout_score_20",
        "failed_reversal_score",
        "inside_outside_bar_score",
    )
    assert config.core == (
        "support_trendline_position_20",
        "support_resistance_position_20",
        "failed_reversal_score",
    )
    assert config.core_weights == (0.05, 0.10, 0.15, 0.20)
    assert config.full_structure_weights == (0.10, 0.20)


def test_variant_specs_are_frozen_and_weighted() -> None:
    raw = _read_config(Path("research/projects/price_action_strategy_lab/config/breadth_risk_off_structure_sleeve_hypothesis.yaml"))
    config = _config(raw)
    specs = _variant_specs(config)

    variant_ids = {spec.variant_id for spec in specs}
    assert variant_ids == {
        "full_baseline",
        "full_baseline_without_structure",
        "core_structure_baseline_sleeve",
        "core_structure_overlay_sleeve",
        "full_structure_baseline_sleeve",
        "full_structure_overlay_sleeve",
        "full_baseline_plus_5pct_core_overlay_sleeve",
        "full_baseline_plus_10pct_core_overlay_sleeve",
        "full_baseline_plus_15pct_core_overlay_sleeve",
        "full_baseline_plus_20pct_core_overlay_sleeve",
        "full_baseline_plus_10pct_full_structure_overlay_sleeve",
        "full_baseline_plus_20pct_full_structure_overlay_sleeve",
    }
    target = next(spec for spec in specs if spec.variant_id == "full_baseline_plus_5pct_core_overlay_sleeve")
    assert target.sleeve_group == "core_structure"
    assert target.weight == 0.05


def test_blend_series_leaves_baseline_unchanged_at_zero_weight() -> None:
    base = pd.Series([1.0, 2.0], index=pd.Index([0, 1]))
    delta = pd.Series([0.4, -0.2], index=pd.Index([0, 1]))

    blended = _blend_series(base, delta, 0.0)

    assert blended.equals(base)
    assert _blend_series(base, delta, 0.10).equals(base.add(delta * 0.10))


def test_event_labels_are_reporting_only(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    pd.DataFrame({"fold": [1, 2], "event_label": ["stress", "stress"]}).to_csv(source / "weak_fold_event_attribution.csv", index=False)
    folds = pd.DataFrame(
        [
            {"variant": "full_baseline", "cost_bps": 10.0, "fold": 1, "delta_return_pct": 0.2, "average_exposure": 0.5},
            {"variant": "full_baseline", "cost_bps": 10.0, "fold": 2, "delta_return_pct": -0.1, "average_exposure": 0.5},
        ]
    )

    result = _event_split(folds, source)

    assert set(result["split"]) == {"known_stress", "unmatched", "all"}
    assert "event_label" not in result.columns
