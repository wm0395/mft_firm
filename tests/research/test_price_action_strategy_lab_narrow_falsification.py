from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.projects.price_action_strategy_lab.narrow_falsification import NarrowFalsificationConfig
from research.projects.price_action_strategy_lab.narrow_falsification import NarrowHypothesis
from research.projects.price_action_strategy_lab.narrow_falsification import _folds
from research.projects.price_action_strategy_lab.narrow_falsification_stats import aggregate_metrics
from research.projects.price_action_strategy_lab.narrow_falsification_stats import tail_diagnostics
from research.projects.price_action_strategy_lab.narrow_falsification_stats import trade_diagnostics
from research.projects.price_action_strategy_lab.run_narrow_falsification import _config
from research.projects.price_action_strategy_lab.run_narrow_falsification import _read_config


def test_pre_registered_config_contains_only_fixed_candidates() -> None:
    raw = _read_config(Path("research/projects/price_action_strategy_lab/config/pre_registered_blocker_hypotheses.yaml"))
    config = _config(raw)

    assert len(config.hypotheses) == 5
    assert {item.hypothesis_id for item in config.hypotheses} == {
        "doji_gap_fade_low_soft_aggressive",
        "doji_gap_fade_low_drawdown_only",
        "inside_outside_vol_expansion_high_drawdown_only",
        "oscillator_family_gap_fade_low_soft_aggressive",
        "support_trendline_vol_expansion_high_soft_aggressive",
    }


def test_purged_folds_leave_lookahead_gap() -> None:
    index = pd.date_range("2025-01-01", periods=60, freq="D")
    config = _small_config(max_folds=1)
    fold = _folds(index, config)[0]

    assert len(fold.train_index) == config.train_size_days - config.lookahead_days
    assert fold.train_index[-1] < fold.test_index[0]


def test_trade_diagnostics_counts_reconcile() -> None:
    positions = pd.DataFrame([[0.5, 0.5], [0.5, 0.0]])
    future = pd.DataFrame([[0.1, -0.1], [-0.2, 0.0]])
    multiplier = pd.Series([0.0, 0.5])
    result = trade_diagnostics(positions, future, multiplier, horizon=10)

    total = sum(int(result[key]) for key in _count_keys())
    assert total == 3
    assert result["blocked_winner"] == 1
    assert result["blocked_loser"] == 1
    assert result["reduced_loser"] == 1


def test_tail_diagnostics_are_deterministic() -> None:
    folds = _fold_frame()
    first = tail_diagnostics(folds)
    second = tail_diagnostics(folds)

    assert first["delta_ci_low_pct"].tolist() == second["delta_ci_low_pct"].tolist()
    assert "bh_p_value" in first.columns


def test_cost_sensitivity_keeps_separate_groups() -> None:
    result = aggregate_metrics(_fold_frame())

    assert set(result["cost_bps"]) == {10.0, 25.0}


def _small_config(max_folds: int) -> NarrowFalsificationConfig:
    return NarrowFalsificationConfig(
        hypotheses=(NarrowHypothesis("h1", ("alpha_a",), "gap_fade", "low", "soft_aggressive", (0.5,), ({"down": 0.5, "up": 1.1},)),),
        cache_dir=Path(".cache"),
        report_root=Path(".reports"),
        source_report_dir=Path(".reports/source"),
        train_size_days=20,
        test_size_days=5,
        step_size_days=5,
        lookahead_days=5,
        max_folds=max_folds,
    )


def _fold_frame() -> pd.DataFrame:
    rows = []
    for cost in (10.0, 25.0):
        for fold, base, var in [(1, -2.0, -1.0), (2, 1.0, 1.2), (3, 2.0, 2.2), (4, 3.0, 3.1)]:
            rows.append(
                {
                    "hypothesis_id": "h1",
                    "cost_bps": cost,
                    "fold": fold,
                    "baseline_return_pct": base,
                    "variant_return_pct": var,
                    "delta_return_pct": var - base,
                    "variant_ann_sharpe": float(var),
                    "avg_exposure_multiplier": 1.0,
                }
            )
    return pd.DataFrame(rows)


def _count_keys() -> tuple[str, ...]:
    return (
        "accepted_winner",
        "accepted_loser",
        "blocked_winner",
        "blocked_loser",
        "reduced_winner",
        "reduced_loser",
        "increased_winner",
        "increased_loser",
    )
