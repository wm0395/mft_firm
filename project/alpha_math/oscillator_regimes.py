from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

import numpy as np
import pandas as pd

from project.alpha_math.diagnostics import cluster_alphas
from project.alpha_math.ohlcv import SeriesOrFrame


@dataclass(frozen=True)
class OscillatorRegimeAnalysis:
    correlation_matrix: pd.DataFrame
    clusters: tuple[tuple[str, ...], ...]
    orthogonalized: pd.DataFrame


@dataclass(frozen=True)
class OscillatorClusterPersistence:
    timeframes: tuple[str, ...]
    clusters_by_timeframe: tuple[tuple[tuple[str, ...], ...], ...]
    pairwise_similarity: pd.DataFrame
    transition_persistence: pd.Series
    persistent_pairs: tuple[tuple[str, str], ...]


def oscillator_regime_clusters(
    oscillators: pd.DataFrame,
    threshold: float = 0.8,
) -> tuple[tuple[str, ...], ...]:
    return cluster_alphas(oscillators, threshold)


def oscillator_cluster_persistence(
    oscillators_by_timeframe: Mapping[str, pd.DataFrame],
    threshold: float = 0.8,
) -> OscillatorClusterPersistence:
    items = tuple(oscillators_by_timeframe.items())
    if not items:
        raise ValueError("oscillators_by_timeframe must not be empty")
    timeframes = tuple(name for name, _ in items)
    clusters_by_timeframe = tuple(
        oscillator_regime_clusters(frame, threshold) for _, frame in items
    )
    pair_sets = tuple(_cluster_pairs(clusters) for clusters in clusters_by_timeframe)
    pairwise_similarity = pd.DataFrame(index=timeframes, columns=timeframes, dtype=float)
    for left_index, left_name in enumerate(timeframes):
        for right_index, right_name in enumerate(timeframes):
            pairwise_similarity.loc[left_name, right_name] = _jaccard_similarity(
                pair_sets[left_index],
                pair_sets[right_index],
            )
    transition = pd.Series(index=timeframes, dtype=float)
    transition.iloc[0] = 1.0
    for index in range(1, len(timeframes)):
        transition.iloc[index] = _jaccard_similarity(pair_sets[index - 1], pair_sets[index])
    persistent_pairs = _persistent_pairs(pair_sets)
    return OscillatorClusterPersistence(
        timeframes=timeframes,
        clusters_by_timeframe=clusters_by_timeframe,
        pairwise_similarity=pairwise_similarity,
        transition_persistence=transition,
        persistent_pairs=persistent_pairs,
    )


def orthogonalize_oscillators(
    oscillators: SeriesOrFrame,
) -> pd.DataFrame:
    frame = _frame_like(oscillators).astype(float).fillna(0.0)
    centered = frame.sub(frame.mean(axis=0), axis=1)
    orthogonalized = pd.DataFrame(index=centered.index)
    basis: list[np.ndarray] = []
    for column in centered.columns:
        vector = centered[column].to_numpy(dtype=float)
        for prior in basis:
            denominator = float(np.dot(prior, prior))
            if denominator == 0.0:
                continue
            projection = float(np.dot(vector, prior) / denominator)
            vector = vector - (projection * prior)
        basis.append(vector)
        orthogonalized[column] = vector
    return orthogonalized


def oscillator_regime_analysis(
    oscillators: SeriesOrFrame,
    threshold: float = 0.8,
) -> OscillatorRegimeAnalysis:
    frame = _frame_like(oscillators)
    return OscillatorRegimeAnalysis(
        correlation_matrix=frame.corr().fillna(0.0),
        clusters=oscillator_regime_clusters(frame, threshold),
        orthogonalized=orthogonalize_oscillators(frame),
    )


def _frame_like(values: SeriesOrFrame) -> pd.DataFrame:
    if isinstance(values, pd.DataFrame):
        return values
    return values.to_frame()


def _cluster_pairs(clusters: tuple[tuple[str, ...], ...]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for cluster in clusters:
        if len(cluster) < 2:
            continue
        for index, left in enumerate(cluster[:-1]):
            for right in cluster[index + 1 :]:
                pairs.add((left, right))
    return pairs


def _jaccard_similarity(
    left: set[tuple[str, str]],
    right: set[tuple[str, str]],
) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _persistent_pairs(pair_sets: tuple[set[tuple[str, str]], ...]) -> tuple[tuple[str, str], ...]:
    if not pair_sets:
        return tuple()
    persistent = set(pair_sets[0]).intersection(*pair_sets[1:])
    return tuple(sorted(persistent))
