from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.projects.price_action_strategy_lab.run_activator_suite import _read_config
from research.projects.price_action_strategy_lab.run_stress_confirmation import _config
from research.projects.price_action_strategy_lab.stress_confirmation import _bh
from research.projects.price_action_strategy_lab.stress_confirmation import _tail
from research.projects.price_action_strategy_lab.stress_confirmation import and_intensity
from research.projects.price_action_strategy_lab.stress_confirmation import stress_variant_ids


def test_only_pre_registered_variants_are_evaluated() -> None:
    raw = _read_config(Path("research/projects/price_action_strategy_lab/config/support_trendline_stress_confirmation_hypothesis.yaml"))
    config = _config(raw)

    assert stress_variant_ids(config) == (
        "baseline",
        "volatility_expansion_high",
        "breadth_risk_off_high",
        "vol_and_breadth",
    )


def test_and_condition_logic_is_boolean_intersection() -> None:
    left = pd.DataFrame([[True, False], [True, True]])
    right = pd.DataFrame([[True, True], [False, True]])

    result = and_intensity(left, right)

    assert result.tolist() == [0.5, 0.5]


def test_event_labels_are_not_variant_features() -> None:
    raw = _read_config(Path("research/projects/price_action_strategy_lab/config/support_trendline_stress_confirmation_hypothesis.yaml"))
    config = _config(raw)

    for variant in config.variants:
        assert "event_label" not in variant.indicators
        assert "weak_fold" not in variant.indicators


def test_cost_outputs_are_separated_in_tail_diagnostics() -> None:
    tail = _tail(_fold_frame())

    assert set(tail["cost_bps"]) == {10.0, 25.0}
    assert set(tail["variant"]) == {"baseline", "vol_and_breadth"}


def test_deterministic_bh_adjustment() -> None:
    values = pd.Series([0.03, 0.01, 0.20])

    assert _bh(values).tolist() == _bh(values).tolist()


def _fold_frame() -> pd.DataFrame:
    rows = []
    for cost in (10.0, 25.0):
        for variant in ("baseline", "vol_and_breadth"):
            for fold, base, delta in ((1, -2.0, 1.0), (2, 1.0, 0.1), (3, 2.0, -0.1), (4, 3.0, 0.2)):
                rows.append(_row(fold, cost, variant, base, delta if variant != "baseline" else 0.0))
    return pd.DataFrame(rows)


def _row(fold: int, cost: float, variant: str, base: float, delta: float) -> dict[str, object]:
    return {
        "fold": fold,
        "variant": variant,
        "cost_bps": cost,
        "baseline_return_pct": base,
        "variant_return_pct": base + delta,
        "delta_return_pct": delta,
        "event_label": "unmatched",
        "avg_exposure": 1.0,
    }
