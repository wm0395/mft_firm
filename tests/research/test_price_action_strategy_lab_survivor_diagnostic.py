from __future__ import annotations

import pandas as pd

from research.projects.price_action_strategy_lab.survivor_diagnostic import SurvivorDiagnosticResult
from research.projects.price_action_strategy_lab.survivor_diagnostic import _cost_stress
from research.projects.price_action_strategy_lab.survivor_diagnostic import perturbed_quantiles
from research.projects.price_action_strategy_lab.survivor_diagnostic import write_survivor_diagnostic_reports
from research.projects.price_action_strategy_lab.survivor_features import SurvivorFeatureFrames
from research.projects.price_action_strategy_lab.survivor_features import blocker_value_row
from research.projects.price_action_strategy_lab.survivor_features import saved_loser_lost_winner_summary
from research.projects.price_action_strategy_lab.survivor_features import trade_feature_rows


def test_trade_diagnostic_counts_reconcile_with_evaluated_trades() -> None:
    rows = trade_feature_rows(_positions(), _future(), pd.Series([0.5, 1.25], index=_dates()), _features(), 10)

    counts = rows["classification"].value_counts()
    classified = int(counts.drop(labels=["other"], errors="ignore").sum())

    assert len(rows) == 4
    assert classified == 4
    assert set(rows["classification"]) == {"reduced_winner", "reduced_loser", "increased_winner", "increased_loser"}


def test_net_blocker_value_arithmetic_is_correct() -> None:
    rows = pd.DataFrame(
        {
            "baseline_trade_return": [0.10, -0.10, 0.10, -0.10],
            "throttle_trade_return": [0.05, -0.05, 0.125, -0.125],
            "classification": ["reduced_winner", "reduced_loser", "increased_winner", "increased_loser"],
        }
    )

    result = blocker_value_row(rows)

    assert round(float(result["net_blocker_value"]), 6) == 0.0
    assert result["reduced_winner"] == 1
    assert result["increased_loser"] == 1


def test_threshold_perturbation_is_selected_quantile_only() -> None:
    assert perturbed_quantiles(0.60) == (0.5, 0.55, 0.6, 0.65, 0.7)
    assert perturbed_quantiles(0.95) == (0.85, 0.9, 0.95, 0.99, 0.99)


def test_cost_stress_keeps_separate_outputs(tmp_path) -> None:
    result = SurvivorDiagnosticResult(
        report_dir=tmp_path,
        trade_diagnostics=pd.DataFrame(),
        blocker_value=pd.DataFrame(),
        saved_loser_vs_lost_winner=pd.DataFrame(),
        fold_anatomy=_fold_frame(),
        threshold_sensitivity=pd.DataFrame(),
        cost_stress=_cost_stress(_fold_frame()),
    )

    paths = write_survivor_diagnostic_reports(result)

    assert set(result.cost_stress["cost_bps"]) == {10.0, 25.0}
    assert paths["cost"].exists()
    assert paths["threshold"].exists()


def test_event_labels_are_reporting_only_not_features() -> None:
    rows = trade_feature_rows(_positions(), _future(), pd.Series([0.5, 1.25], index=_dates()), _features(), 10)
    summary = saved_loser_lost_winner_summary(rows)

    assert "event_label" not in rows.columns
    assert "event_label" not in summary.columns
    assert set(summary["group"]) == {"saved_loser", "lost_winner"}


def _dates() -> pd.DatetimeIndex:
    return pd.date_range("2026-01-01", periods=2, freq="D")


def _positions() -> pd.DataFrame:
    return pd.DataFrame([[0.5, 0.5], [0.5, 0.5]], index=_dates(), columns=["A", "B"])


def _future() -> pd.DataFrame:
    return pd.DataFrame([[0.2, -0.2], [0.2, -0.2]], index=_dates(), columns=["A", "B"])


def _features() -> SurvivorFeatureFrames:
    matrix = pd.DataFrame(1.0, index=_dates(), columns=["A", "B"])
    table = matrix.stack(future_stack=True).rename("support_trendline_alpha_score").to_frame()
    return SurvivorFeatureFrames(
        volatility_expansion_value=pd.Series([0.4, 0.7], index=_dates()),
        support_trendline_alpha_score=matrix,
        stock_vol20=matrix,
        stock_vol60=matrix,
        market_breadth=pd.Series([0.5, 0.5], index=_dates()),
        gap_size=matrix,
        volume_shock=matrix,
        relative_strength=matrix,
        sector=pd.Series({"A": "x", "B": "y"}),
        feature_table=table.assign(stock_vol20=1.0, stock_vol60=1.0, gap_size=1.0, volume_shock=1.0, relative_strength=1.0),
    )


def _fold_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _fold_row(1, 10.0, -1.0, -0.5),
            _fold_row(2, 10.0, 2.0, 1.9),
            _fold_row(1, 25.0, -1.0, -0.7),
            _fold_row(2, 25.0, 2.0, 1.8),
        ]
    )


def _fold_row(fold: int, cost: float, baseline: float, throttle: float) -> dict[str, object]:
    return {
        "fold": fold,
        "cost_bps": cost,
        "baseline_return_pct": baseline,
        "throttle_return_pct": throttle,
        "delta_vs_baseline_pct": throttle - baseline,
        "net_blocker_value": throttle - baseline,
        "helped_hurt_neutral": "helped" if throttle > baseline else "hurt",
    }
