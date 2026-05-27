from __future__ import annotations

import pandas as pd
import pytest

from project.alpha_math.oscillator_regimes import (
    OscillatorClusterPersistence,
    OscillatorRegimeAnalysis,
    oscillator_cluster_persistence,
    oscillator_regime_analysis,
    oscillator_regime_clusters,
    orthogonalize_oscillators,
)


def test_oscillator_regime_clusters_group_correlated_series() -> None:
    oscillators = pd.DataFrame(
        {
            "fast": [1.0, 2.0, 3.0, 4.0, 5.0],
            "slow": [2.0, 4.0, 6.0, 8.0, 10.0],
            "reverse": [5.0, 1.0, 4.0, 2.0, 3.0],
        }
    )

    clusters = oscillator_regime_clusters(oscillators, threshold=0.9)

    assert ("fast", "slow") in clusters
    assert ("reverse",) in clusters


def test_orthogonalize_oscillators_removes_linear_dependence() -> None:
    oscillators = pd.DataFrame(
        {
            "fast": [1.0, 2.0, 3.0, 4.0, 5.0],
            "slow": [2.0, 4.0, 6.0, 8.0, 10.0],
            "reverse": [5.0, 1.0, 4.0, 2.0, 3.0],
        }
    )

    orthogonalized = orthogonalize_oscillators(oscillators)

    assert orthogonalized.shape == oscillators.shape
    assert orthogonalized["fast"].dot(orthogonalized["slow"]) == pytest.approx(0.0)


def test_oscillator_regime_analysis_returns_clusters_and_matrix() -> None:
    oscillators = pd.DataFrame(
        {
            "fast": [1.0, 2.0, 3.0, 4.0, 5.0],
            "slow": [2.0, 4.0, 6.0, 8.0, 10.0],
            "reverse": [5.0, 1.0, 4.0, 2.0, 3.0],
        }
    )

    analysis = oscillator_regime_analysis(oscillators, threshold=0.9)

    assert isinstance(analysis, OscillatorRegimeAnalysis)
    assert analysis.correlation_matrix.shape == (3, 3)
    assert analysis.orthogonalized.shape == oscillators.shape


def test_oscillator_cluster_persistence_tracks_timeframe_similarity() -> None:
    oscillators_by_timeframe = {
        "short": pd.DataFrame(
            {
                "fast": [1.0, 2.0, 3.0, 4.0, 5.0],
                "slow": [1.0, 2.0, 3.0, 4.0, 5.0],
                "noise": [1.0, 0.0, 1.0, 0.0, 1.0],
            }
        ),
        "medium": pd.DataFrame(
            {
                "fast": [1.0, 2.0, 3.0, 4.0, 5.0],
                "slow": [1.0, 2.0, 3.0, 4.0, 5.0],
                "noise": [1.0, 0.0, 1.0, 0.0, 1.0],
            }
        ),
        "long": pd.DataFrame(
            {
                "fast": [1.0, 2.0, 3.0, 4.0, 5.0],
                "slow": [1.0, 2.0, 3.0, 4.0, 5.0],
                "noise": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        ),
    }

    persistence = oscillator_cluster_persistence(oscillators_by_timeframe, threshold=0.99)

    assert isinstance(persistence, OscillatorClusterPersistence)
    assert persistence.timeframes == ("short", "medium", "long")
    assert persistence.transition_persistence.iloc[1] == pytest.approx(1.0)
    assert persistence.transition_persistence.iloc[2] == pytest.approx(1.0 / 3.0)
    assert persistence.persistent_pairs == (("fast", "slow"),)
