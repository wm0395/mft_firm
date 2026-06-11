from __future__ import annotations

import pandas as pd

from research.projects.price_action_strategy_lab.alpha_regime_hypothesis_book import alpha_regime_hypotheses


def test_alpha_regime_hypotheses_ranks_tail_preserving_lead() -> None:
    result = alpha_regime_hypotheses(_alpha_tail(), _gates(), _folds(), _stability())
    top = result.iloc[0]

    assert top["alpha"] == "alpha_a"
    assert top["indicator"] == "gap_fade"
    assert top["side"] == "low"
    assert top["hypothesis_status"] == "research_only_needs_significance"
    assert top["left_tail_count"] == 1


def test_alpha_regime_hypotheses_rejects_right_tail_loss() -> None:
    result = alpha_regime_hypotheses(_alpha_tail(), _gates(), _folds(), _stability())
    rejected = result.loc[result["alpha"].eq("alpha_b")].iloc[0]

    assert rejected["hypothesis_status"] == "reject_right_tail_loss"


def _alpha_tail() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _tail("alpha_a", "soft_aggressive", 0.2, -0.1, 1.5, 0.94, 0.5),
            _tail("alpha_b", "soft_aggressive", 0.4, -0.1, 2.0, 0.80, 0.7),
            _tail("alpha_c", "hard_gate", 0.5, 0.2, 3.0, 0.30, 0.9),
        ]
    )


def _tail(alpha: str, variant: str, delta: float, ci: float, left: float, right: float, drawdown: float) -> dict[str, object]:
    return {
        "alpha": alpha,
        "variant": variant,
        "mean_delta_vs_baseline_pct": delta,
        "delta_ci_low_pct": ci,
        "paired_p_value": 0.2,
        "left_tail_delta_pct": left,
        "right_tail_retention": right,
        "max_drawdown_delta_pct": drawdown,
    }


def _gates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _gate(1, "alpha_a", "gap_fade", "low"),
            _gate(2, "alpha_a", "volatility_expansion", "high"),
            _gate(1, "alpha_b", "gap_fade", "low"),
            _gate(2, "alpha_b", "gap_fade", "low"),
        ]
    )


def _gate(fold: int, alpha: str, indicator: str, side: str) -> dict[str, object]:
    return {
        "fold": fold,
        "alpha": alpha,
        "indicator": indicator,
        "side": side,
        "score": 2.0,
        "lift_bps": 3.0,
    }


def _folds() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"fold": 1, "variant": "baseline", "return_pct": -4.0},
            {"fold": 2, "variant": "baseline", "return_pct": 6.0},
            {"fold": 3, "variant": "baseline", "return_pct": 1.0},
        ]
    )


def _stability() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"alpha": "alpha_a", "top_indicator_rate": 0.6, "unique_indicators": 2, "activate_rate": 1.0},
            {"alpha": "alpha_b", "top_indicator_rate": 0.9, "unique_indicators": 1, "activate_rate": 1.0},
        ]
    )
