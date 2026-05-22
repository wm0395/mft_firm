from __future__ import annotations

import pandas as pd
import pytest

from project.alpha_math.capacity import (
    capacity_estimate,
    liquidity_score,
    participation_rate_limit,
    transaction_cost_stress,
    turnover_penalty,
)
from project.alpha_math.diagnostics import (
    alpha_correlation_matrix,
    alpha_decay_report,
    cluster_alphas,
    duplicate_alpha_detection,
    failure_window_report,
)
from project.alpha_math.ensembles import (
    equal_weight_ensemble,
    inverse_correlation_weighting,
    orthogonalized_ensemble,
    rank_average_ensemble,
)
from project.alpha_math.validation import (
    embargo_time_split,
    ic_decay,
    purged_time_split,
    rank_ic,
    rolling_ic,
    stability_by_regime,
    stability_by_universe,
    walk_forward_split,
)


def test_ic_functions_return_perfect_signal_for_perfect_relationship() -> None:
    signal = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0],
            "b": [2.0, 4.0, 6.0],
            "c": [3.0, 6.0, 9.0],
        },
        index=pd.date_range("2024-01-01", periods=3),
    )
    forward = signal * 2.0

    ic = rolling_ic(signal, forward)
    rank = rank_ic(signal, forward)
    decay = ic_decay(signal, {"1d": forward, "5d": forward})

    assert ic.dropna().tolist() == pytest.approx([1.0, 1.0, 1.0])
    assert rank.dropna().tolist() == pytest.approx([1.0, 1.0, 1.0])
    assert list(decay.index) == ["1d", "5d"]
    assert decay.tolist() == pytest.approx([1.0, 1.0])


def test_walk_forward_and_purged_splits_are_deterministic() -> None:
    index = pd.RangeIndex(10)

    walk = list(walk_forward_split(index, train_size=4, test_size=2, step_size=2))
    purged = list(purged_time_split(index, train_size=4, test_size=2, lookahead=1, step_size=2))
    embargoed = list(embargo_time_split(index, train_size=4, test_size=2, embargo=1, step_size=2))

    assert len(walk) == 3
    assert walk[0][0].tolist() == [0, 1, 2, 3]
    assert walk[0][1].tolist() == [4, 5]
    assert purged[0][0].tolist() == [0, 1, 2]
    assert purged[0][1].tolist() == [4, 5]
    assert embargoed[0][0].tolist() == [0, 1, 2, 3]
    assert embargoed[0][1].tolist() == [5, 6]


def test_stability_by_regime_and_universe_group_metrics() -> None:
    metric = pd.Series([0.1, 0.2, -0.1, 0.3], index=list("abcd"))
    regimes = pd.Series(["risk_on", "risk_on", "risk_off", "risk_off"], index=metric.index)
    universes = pd.Series(["cash", "cash", "etf", "etf"], index=metric.index)

    regime_report = stability_by_regime(metric, regimes)
    universe_report = stability_by_universe(metric, universes)

    assert regime_report.loc["risk_on", "count"] == 2
    assert universe_report.loc["cash", "mean"] == pytest.approx(0.15)


def test_capacity_helpers_are_explicit_and_deterministic() -> None:
    volume = pd.Series([100.0, 200.0])
    turnover = pd.Series([0.1, 0.2])

    score = liquidity_score(volume, turnover=turnover)
    capacity = capacity_estimate(10.0, volume, 0.1, turnover=turnover)
    penalty = turnover_penalty(turnover, target_turnover=0.2)
    stressed = transaction_cost_stress(pd.Series([0.05, 0.03]), turnover, cost_bps=10.0)
    limit = participation_rate_limit(volume, 0.1)

    assert score.iloc[1] > score.iloc[0]
    assert capacity.iloc[1] > capacity.iloc[0]
    assert penalty.iloc[0] > penalty.iloc[1]
    assert stressed.iloc[0] < 0.05
    assert limit.tolist() == pytest.approx([10.0, 20.0])


def test_ensemble_helpers_combine_signals_consistently() -> None:
    signals = pd.DataFrame(
        {
            "alpha_a": [1.0, 2.0, 3.0],
            "alpha_b": [1.1, 1.9, 3.1],
            "alpha_c": [10.0, 10.0, 10.0],
        },
        index=pd.RangeIndex(3),
    )

    equal = equal_weight_ensemble(signals)
    ranked = rank_average_ensemble(signals)
    inverse = inverse_correlation_weighting(signals)
    orthogonal = orthogonalized_ensemble(signals)

    assert equal.tolist() == pytest.approx([4.0333333333, 4.6333333333, 5.3666666667])
    assert ranked.between(0.0, 1.0).all()
    assert inverse.index.equals(signals.index)
    assert orthogonal.index.equals(signals.index)


def test_diagnostics_find_clusters_and_failure_windows() -> None:
    alphas = pd.DataFrame(
        {
            "alpha_a": [1.0, 2.0, 3.0, 4.0],
            "alpha_b": [1.0, 2.0, 3.0, 4.0],
            "alpha_c": [1.0, 4.0, 2.0, 3.0],
        }
    )
    returns = pd.Series([0.1, -0.2, -0.1, 0.05, 0.01])
    signal = pd.DataFrame(
        {
            "alpha_a": [1.0, 2.0, 3.0],
            "alpha_b": [1.0, 2.0, 3.0],
        }
    )

    corr = alpha_correlation_matrix(alphas)
    clusters = cluster_alphas(alphas, threshold=0.99)
    duplicates = duplicate_alpha_detection(alphas, threshold=0.99)
    decay_report = alpha_decay_report(signal, {"1d": signal * 2.0, "5d": signal * 3.0})
    failures = failure_window_report(returns, window=3, threshold=-0.05)

    assert corr.loc["alpha_a", "alpha_b"] == pytest.approx(1.0)
    assert ("alpha_a", "alpha_b") in clusters
    assert duplicates == (("alpha_a", "alpha_b"),)
    assert list(decay_report["horizon"]) == ["1d", "5d"]
    assert not failures.empty
