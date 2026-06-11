from __future__ import annotations

import pandas as pd

from research.projects.price_action_strategy_lab.evidence_metrics_report import write_evidence_metrics


def test_write_evidence_metrics_creates_core_outputs(tmp_path) -> None:
    _write_inputs(tmp_path)

    paths = write_evidence_metrics(tmp_path)

    assert paths.alpha_deltas.exists()
    assert paths.top_candidates.exists()
    assert paths.summary.exists()
    top = pd.read_csv(paths.top_candidates)
    assert bool(top.loc[top["alpha"].eq("alpha_a"), "passes_all_in_sample_gates"].iloc[0])


def _write_inputs(path) -> None:
    pd.DataFrame(
        [
            _metric("alpha_a", "baseline", 10.0, 1.0, -5.0),
            _metric("alpha_a", "soft_aggressive", 12.0, 1.2, -4.0),
            _metric("alpha_a", "hard_gate", 8.0, 1.5, -2.0),
        ]
    ).to_csv(path / "soft_throttle_2yr_metrics.csv", index=False)
    pd.DataFrame([_exposure("alpha_a", item) for item in ["baseline", "soft_aggressive", "hard_gate"]]).to_csv(
        path / "soft_throttle_exposure_diagnostics.csv",
        index=False,
    )
    pd.DataFrame([_gate("alpha_a")]).to_csv(path / "indicator_alpha_tuned_gates.csv", index=False)
    pd.DataFrame([_correlation("alpha_a")]).to_csv(path / "indicator_alpha_correlations.csv", index=False)
    pd.DataFrame([_gate("alpha_a", fold=1)]).to_csv(path / "soft_throttle_walk_forward_selected_gates.csv", index=False)
    pd.DataFrame([{"alpha": "alpha_a", "fold_count": 1, "top_indicator": "vol", "top_indicator_rate": 1.0}]).to_csv(
        path / "soft_throttle_walk_forward_gate_stability.csv",
        index=False,
    )
    pd.DataFrame([{"variant": "baseline", "return_pct": 1.0}, {"variant": "soft_aggressive", "return_pct": 1.2}]).to_csv(
        path / "soft_throttle_2yr_aggregate.csv",
        index=False,
    )


def _metric(alpha: str, variant: str, ret: float, sharpe: float, drawdown: float) -> dict[str, object]:
    return {
        "alpha": alpha,
        "variant": variant,
        "obs": 10,
        "return_pct": ret,
        "cagr_pct": ret,
        "ann_vol_pct": 1.0,
        "ann_sharpe": sharpe,
        "latest_1m_rolling_sharpe": sharpe,
        "negative_1m_sharpe_rate": 0.0,
        "max_drawdown_pct": drawdown,
    }


def _exposure(alpha: str, variant: str) -> dict[str, object]:
    return {
        "alpha": alpha,
        "variant": variant,
        "active_day_pct": 100.0,
        "avg_exposure_multiplier": 1.0,
        "scaled_turnover_est": 0.1,
        "positive_windows_reduced": 1,
        "negative_windows_reduced": 2,
    }


def _gate(alpha: str, fold: int | None = None) -> dict[str, object]:
    row: dict[str, object] = {
        "alpha": alpha,
        "family": "test",
        "indicator": "vol",
        "side": "high",
        "coverage": 0.5,
        "score": 1.0,
        "lift_bps": 2.0,
        "on_return_bps": 3.0,
        "off_return_bps": 1.0,
        "decision": "activate",
        "test_start": "2026-01-01",
        "test_end": "2026-01-31",
    }
    if fold is not None:
        row["fold"] = fold
    return row


def _correlation(alpha: str) -> dict[str, object]:
    return {
        "alpha": alpha,
        "indicator": "vol",
        "return_spearman": 0.2,
        "underperform_corr": -0.1,
        "overperform_corr": 0.3,
    }
