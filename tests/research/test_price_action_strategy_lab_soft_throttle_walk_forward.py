from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.projects.price_action_strategy_lab.soft_throttle_walk_forward import WalkForwardThrottleConfig
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward import build_walk_forward_fold_specs


def test_build_walk_forward_fold_specs_purges_lookahead_window() -> None:
    index = pd.date_range("2025-01-01", periods=200, freq="D")
    config = WalkForwardThrottleConfig(
        alpha_names=("alpha_a",),
        cache_dir=Path("."),
        train_size_days=126,
        test_size_days=21,
        step_size_days=21,
        lookahead_days=10,
        max_folds=1,
    )

    fold = build_walk_forward_fold_specs(index, config)[0]

    assert len(fold.train_index) == 116
    assert len(fold.test_index) == 21
    assert fold.train_index.intersection(fold.test_index).empty
    assert fold.train_index[-1] == index[115]
    assert fold.test_index[0] == index[126]


def test_build_walk_forward_fold_specs_is_deterministic() -> None:
    index = pd.date_range("2025-01-01", periods=200, freq="D")
    config = WalkForwardThrottleConfig(
        alpha_names=("alpha_a",),
        cache_dir=Path("."),
        max_folds=3,
    )

    left = build_walk_forward_fold_specs(index, config)
    right = build_walk_forward_fold_specs(index, config)

    assert [(fold.fold, tuple(fold.train_index), tuple(fold.test_index)) for fold in left] == [
        (fold.fold, tuple(fold.train_index), tuple(fold.test_index)) for fold in right
    ]


def test_build_walk_forward_fold_specs_can_select_latest_folds() -> None:
    index = pd.date_range("2025-01-01", periods=220, freq="D")
    earliest_config = WalkForwardThrottleConfig(
        alpha_names=("alpha_a",),
        cache_dir=Path("."),
        max_folds=1,
    )
    latest_config = WalkForwardThrottleConfig(
        alpha_names=("alpha_a",),
        cache_dir=Path("."),
        max_folds=1,
        fold_selection="latest",
    )

    earliest = build_walk_forward_fold_specs(index, earliest_config)[0]
    latest = build_walk_forward_fold_specs(index, latest_config)[0]

    assert latest.fold > earliest.fold
    assert latest.test_index[-1] > earliest.test_index[-1]
