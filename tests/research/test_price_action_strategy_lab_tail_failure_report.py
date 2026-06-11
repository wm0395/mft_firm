from __future__ import annotations

import pandas as pd

from research.projects.price_action_strategy_lab.tail_failure_report import tail_alpha_variant_diagnostics
from research.projects.price_action_strategy_lab.tail_failure_report import tail_variant_diagnostics
from research.projects.price_action_strategy_lab.tail_failure_report import write_tail_failure_report


def test_tail_variant_diagnostics_measures_tail_and_right_retention() -> None:
    folds = pd.DataFrame(
        [
            _fold(1, "baseline", -4.0, -10.0, -2.0),
            _fold(2, "baseline", 2.0, 3.0, -0.5),
            _fold(3, "baseline", 4.0, 5.0, -0.2),
            _fold(4, "baseline", 6.0, 7.0, -0.1),
            _fold(1, "drawdown_only_throttle", -2.0, -4.0, -1.0),
            _fold(2, "drawdown_only_throttle", 1.9, 3.2, -0.4),
            _fold(3, "drawdown_only_throttle", 3.9, 5.3, -0.2),
            _fold(4, "drawdown_only_throttle", 5.9, 7.3, -0.1),
        ]
    )

    result = tail_variant_diagnostics(folds)
    throttle = result.loc[result["variant"].eq("drawdown_only_throttle")].iloc[0]

    assert throttle["left_tail_delta_pct"] > 0.0
    assert throttle["right_tail_retention"] > 0.95
    assert throttle["sharpe_delta"] > 0.0


def test_tail_alpha_variant_diagnostics_keeps_alpha_dimension() -> None:
    folds = pd.DataFrame(
        [
            dict(_fold(1, "baseline", -4.0, -10.0, -2.0), alpha="alpha_a"),
            dict(_fold(2, "baseline", 4.0, 6.0, -0.2), alpha="alpha_a"),
            dict(_fold(1, "soft_aggressive", -2.0, -5.0, -1.0), alpha="alpha_a"),
            dict(_fold(2, "soft_aggressive", 3.9, 6.4, -0.2), alpha="alpha_a"),
            dict(_fold(1, "baseline", -3.0, -8.0, -2.0), alpha="alpha_b"),
            dict(_fold(2, "baseline", 3.0, 5.0, -0.2), alpha="alpha_b"),
        ]
    )

    result = tail_alpha_variant_diagnostics(folds)

    assert set(result["alpha"]) == {"alpha_a", "alpha_b"}
    assert "soft_aggressive" in set(result.loc[result["alpha"].eq("alpha_a"), "variant"])


def test_write_tail_failure_report_creates_outputs(tmp_path) -> None:
    pd.DataFrame(
        [
            _fold(1, "baseline", -4.0, -10.0, -2.0),
            _fold(2, "baseline", 4.0, 6.0, -0.2),
            _fold(1, "soft_aggressive", -3.0, -8.0, -1.0),
            _fold(2, "soft_aggressive", 3.8, 6.5, -0.2),
        ]
    ).to_csv(tmp_path / "soft_throttle_walk_forward_fold_metrics.csv", index=False)
    pd.DataFrame([_gate(1), _gate(2)]).to_csv(
        tmp_path / "soft_throttle_walk_forward_selected_gates.csv",
        index=False,
    )

    paths = write_tail_failure_report(tmp_path)

    assert paths.variant_diagnostics.exists()
    assert paths.gate_diagnostics.exists()
    assert "Tail Failure Report" in paths.markdown.read_text(encoding="utf-8")


def _fold(fold: int, variant: str, ret: float, sharpe: float, drawdown: float) -> dict[str, object]:
    return {
        "fold": fold,
        "variant": variant,
        "return_pct": ret,
        "ann_sharpe": sharpe,
        "max_drawdown_pct": drawdown,
    }


def _gate(fold: int) -> dict[str, object]:
    return {
        "fold": fold,
        "alpha": "alpha_a",
        "decision": "activate",
        "indicator": "volatility_expansion",
        "side": "high",
        "score": 2.0,
        "lift_bps": 3.0,
        "on_return_bps": 4.0,
        "off_return_bps": 1.0,
    }
