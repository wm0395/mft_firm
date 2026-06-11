from __future__ import annotations

import pandas as pd

from research.projects.price_action_strategy_lab.indicator_alpha_diagnostics import tune_indicator_gates


def test_tune_indicator_gates_selects_best_positive_lift_gate() -> None:
    grid = pd.DataFrame(
        [
            _row("alpha_a", "trend_alignment", "high", 0.7, 0.4, 12.0, True),
            _row("alpha_a", "breadth_thrust", "low", 0.7, 0.3, -4.0, True),
            _row("alpha_b", "oscillator_extreme", "low", 0.8, 0.2, 5.0, True),
        ]
    )
    tuned = tune_indicator_gates(grid)
    alpha_a = tuned.loc[tuned["alpha"].eq("alpha_a")].iloc[0]
    alpha_b = tuned.loc[tuned["alpha"].eq("alpha_b")].iloc[0]
    assert alpha_a["indicator"] == "trend_alignment"
    assert alpha_a["decision"] == "activate"
    assert alpha_b["indicator"] == "oscillator_extreme"
    assert alpha_b["decision"] == "activate"


def test_tune_indicator_gates_abstains_when_no_eligible_rows_exist() -> None:
    grid = pd.DataFrame([_row("alpha_a", "trend_alignment", "high", 0.9, 0.01, 20.0, False)])
    tuned = tune_indicator_gates(grid)
    assert tuned.empty


def _row(
    alpha: str,
    indicator: str,
    side: str,
    quantile: float,
    coverage: float,
    lift_bps: float,
    eligible: bool,
) -> dict[str, object]:
    bad_rate_on = 0.10 if lift_bps > 0.0 else 0.30
    return {
        "alpha": alpha,
        "family": "test",
        "indicator": indicator,
        "side": side,
        "quantile": quantile,
        "threshold": 0.5,
        "eligible": eligible,
        "score": lift_bps + 1.0,
        "coverage": coverage,
        "lift_bps": lift_bps,
        "on_return_bps": lift_bps + 2.0,
        "off_return_bps": 2.0,
        "bad_rate_on": bad_rate_on,
        "bad_rate_off": 0.20,
        "good_rate_on": 0.30,
        "good_rate_off": 0.20,
    }
