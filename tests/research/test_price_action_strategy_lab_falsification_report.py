from __future__ import annotations

import pandas as pd

from research.projects.price_action_strategy_lab.falsification_report import falsification_results


def test_falsification_results_passes_strict_candidate() -> None:
    results = falsification_results(pd.DataFrame([_row("alpha_a", 0.98, 0.2, 0.01, 0.8)]))

    assert results.iloc[0]["falsification_status"] == "passes_initial_falsification"
    assert results.iloc[0]["failure_reasons"] == ""


def test_falsification_results_fails_right_tail_first() -> None:
    results = falsification_results(pd.DataFrame([_row("alpha_b", 0.89, 0.2, 0.01, 0.8)]))

    assert results.iloc[0]["falsification_status"] == "falsified_right_tail_loss"
    assert "right_tail<95%" in results.iloc[0]["failure_reasons"]


def test_falsification_results_flags_insignificant_unstable_lead() -> None:
    results = falsification_results(pd.DataFrame([_row("alpha_c", 0.96, -0.1, 0.2, 0.2)]))

    assert results.iloc[0]["falsification_status"] == "not_significant"
    assert "ci_low<=0" in results.iloc[0]["failure_reasons"]
    assert "top_indicator_rate<50%" in results.iloc[0]["failure_reasons"]


def _row(alpha: str, right_tail: float, ci_low: float, pvalue: float, stability: float) -> dict[str, object]:
    return {
        "alpha": alpha,
        "variant": "soft_aggressive",
        "indicator": "gap_fade",
        "side": "low",
        "hypothesis_score": 1.0,
        "mean_delta_vs_baseline_pct": 0.2,
        "delta_ci_low_pct": ci_low,
        "paired_p_value": pvalue,
        "left_tail_delta_pct": 1.0,
        "right_tail_retention": right_tail,
        "max_drawdown_delta_pct": 0.5,
        "top_indicator_rate": stability,
        "selection_count": 5,
        "left_tail_count": 2,
        "right_tail_count": 2,
    }
