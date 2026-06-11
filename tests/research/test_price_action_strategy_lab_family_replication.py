from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.projects.price_action_strategy_lab.family_replication import _alpha_improve_rate
from research.projects.price_action_strategy_lab.family_replication import _cost_stress
from research.projects.price_action_strategy_lab.family_replication import _groups
from research.projects.price_action_strategy_lab.run_activator_suite import _read_config
from research.projects.price_action_strategy_lab.run_stress_confirmation import _config
from research.projects.price_action_strategy_lab.stress_confirmation import _tail


def test_only_pre_registered_alphas_are_evaluated() -> None:
    raw = _read_config(Path("research/projects/price_action_strategy_lab/config/breadth_risk_off_family_replication_hypothesis.yaml"))
    groups = _groups(raw)

    assert len(groups["structure_level"]) == 5
    assert len(groups["reversal_exhaustion"]) == 7
    assert "support_trendline_position_20" in groups["structure_level"]


def test_only_breadth_risk_off_indicator_is_used() -> None:
    raw = _read_config(Path("research/projects/price_action_strategy_lab/config/breadth_risk_off_family_replication_hypothesis.yaml"))
    config = _config(raw)

    assert {variant.hypothesis.indicator for variant in config.variants} == {"breadth_risk_off"}
    assert all("volatility_expansion" not in variant.indicators for variant in config.variants)


def test_drawdown_variant_keeps_drawdown_throttle() -> None:
    raw = _read_config(Path("research/projects/price_action_strategy_lab/config/breadth_risk_off_family_replication_hypothesis.yaml"))
    config = _config(raw)
    variants = {variant.variant_id: variant.hypothesis.throttle_variant for variant in config.variants}

    assert variants["breadth_drawdown_only"] == "drawdown_only_throttle"


def test_group_alpha_improve_rate_is_correct() -> None:
    frame = pd.DataFrame(
        {
            "group": ["g", "g", "g", "g"],
            "alpha": ["a", "a", "b", "b"],
            "variant": ["v", "v", "v", "v"],
            "cost_bps": [10.0, 10.0, 10.0, 10.0],
            "delta_return_pct": [1.0, 1.0, -1.0, -1.0],
        }
    )

    assert _alpha_improve_rate(frame, "g", "v", 10.0) == 0.5


def test_cost_outputs_are_separated() -> None:
    tail = pd.DataFrame(
        {
            "group": ["g", "g"],
            "alpha": ["a", "a"],
            "variant": ["v", "v"],
            "cost_bps": [10.0, 25.0],
            "mean_delta_vs_baseline": [1.0, 2.0],
            "left_tail_delta": [1.0, 2.0],
            "right_tail_retention": [1.0, 1.0],
            "ci_low": [0.0, 0.0],
        }
    )

    assert set(_cost_stress(tail)["cost_bps"]) == {10.0, 25.0}


def test_tail_bootstrap_is_deterministic() -> None:
    first = _tail(_fold_frame())
    second = _tail(_fold_frame())

    assert first["ci_low"].tolist() == second["ci_low"].tolist()


def _fold_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "variant": ["v", "v", "v", "v"],
            "cost_bps": [10.0, 10.0, 10.0, 10.0],
            "baseline_return_pct": [-1.0, 1.0, 2.0, 3.0],
            "variant_return_pct": [-0.5, 1.2, 1.8, 3.1],
            "delta_return_pct": [0.5, 0.2, -0.2, 0.1],
        }
    )
