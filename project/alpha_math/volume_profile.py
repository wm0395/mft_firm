from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from project.alpha_math.ohlcv import SeriesOrFrame


@dataclass(frozen=True)
class VolumeProfileLevels:
    point_of_control: SeriesOrFrame
    value_area_low: SeriesOrFrame
    value_area_high: SeriesOrFrame
    concentration: SeriesOrFrame
    position: SeriesOrFrame


@dataclass(frozen=True)
class VolumeProfileRegime:
    above_value_area: SeriesOrFrame
    below_value_area: SeriesOrFrame
    inside_value_area: SeriesOrFrame
    accepted: SeriesOrFrame


def volume_profile_levels(
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    window: int = 20,
    bins: int = 20,
    value_area_pct: float = 0.7,
) -> VolumeProfileLevels:
    if isinstance(close, pd.Series):
        return _series_volume_profile_levels(
            close,
            volume,
            window,
            bins,
            value_area_pct,
        )
    if isinstance(close, pd.DataFrame):
        return _frame_volume_profile_levels(
            close,
            volume,
            window,
            bins,
            value_area_pct,
        )
    raise TypeError("close must be a pandas Series or DataFrame")


def volume_profile_regime(
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    window: int = 20,
    bins: int = 20,
    value_area_pct: float = 0.7,
) -> VolumeProfileRegime:
    levels = volume_profile_levels(close, volume, window, bins, value_area_pct)
    above = close.gt(levels.value_area_high)
    below = close.lt(levels.value_area_low)
    inside = ~(above | below)
    accepted = inside & close.ge(levels.point_of_control)
    return VolumeProfileRegime(
        above_value_area=above,
        below_value_area=below,
        inside_value_area=inside,
        accepted=accepted,
    )


def _series_volume_profile_levels(
    close: pd.Series,
    volume: pd.Series,
    window: int,
    bins: int,
    value_area_pct: float,
) -> VolumeProfileLevels:
    length = len(close)
    poc = np.full(length, np.nan, dtype=float)
    val = np.full(length, np.nan, dtype=float)
    vah = np.full(length, np.nan, dtype=float)
    concentration = np.full(length, np.nan, dtype=float)
    position = np.full(length, np.nan, dtype=float)
    close_values = close.to_numpy(dtype=float)
    volume_values = volume.to_numpy(dtype=float)
    for end in range(window - 1, length):
        snapshot = _profile_snapshot(
            close_values[end - window + 1 : end + 1],
            volume_values[end - window + 1 : end + 1],
            bins,
            value_area_pct,
        )
        poc[end], val[end], vah[end], concentration[end], position[end] = snapshot
    return VolumeProfileLevels(
        point_of_control=pd.Series(poc, index=close.index, name=close.name),
        value_area_low=pd.Series(val, index=close.index, name=close.name),
        value_area_high=pd.Series(vah, index=close.index, name=close.name),
        concentration=pd.Series(concentration, index=close.index, name=close.name),
        position=pd.Series(position, index=close.index, name=close.name),
    )


def _frame_volume_profile_levels(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    window: int,
    bins: int,
    value_area_pct: float,
) -> VolumeProfileLevels:
    if not close.columns.equals(volume.columns):
        raise ValueError("close and volume must have matching columns")
    summaries = {
        column: _series_volume_profile_levels(
            close[column],
            volume[column],
            window,
            bins,
            value_area_pct,
        )
        for column in close.columns
    }
    return VolumeProfileLevels(
        point_of_control=pd.DataFrame(
            {column: summary.point_of_control for column, summary in summaries.items()}
        ),
        value_area_low=pd.DataFrame(
            {column: summary.value_area_low for column, summary in summaries.items()}
        ),
        value_area_high=pd.DataFrame(
            {column: summary.value_area_high for column, summary in summaries.items()}
        ),
        concentration=pd.DataFrame(
            {column: summary.concentration for column, summary in summaries.items()}
        ),
        position=pd.DataFrame(
            {column: summary.position for column, summary in summaries.items()}
        ),
    )


def _profile_snapshot(
    close: np.ndarray,
    volume: np.ndarray,
    bins: int,
    value_area_pct: float,
) -> tuple[float, float, float, float, float]:
    valid = ~np.isnan(close) & ~np.isnan(volume)
    if valid.sum() < 1:
        return _empty_snapshot()
    prices = close[valid]
    weights = volume[valid]
    price_min = float(np.min(prices))
    price_max = float(np.max(prices))
    if price_min == price_max:
        return _constant_snapshot(price_min, weights)
    return _histogram_snapshot(prices, weights, bins, value_area_pct)


def _empty_snapshot() -> tuple[float, float, float, float, float]:
    return (float("nan"),) * 5


def _constant_snapshot(
    price: float,
    weights: np.ndarray,
) -> tuple[float, float, float, float, float]:
    total = float(np.sum(weights))
    concentration = float(np.max(weights) / total) if total > 0.0 else float("nan")
    return price, price, price, concentration, 0.5


def _histogram_snapshot(
    prices: np.ndarray,
    weights: np.ndarray,
    bins: int,
    value_area_pct: float,
) -> tuple[float, float, float, float, float]:
    edges = np.linspace(float(np.min(prices)), float(np.max(prices)), bins + 1)
    profile, edges = np.histogram(prices, bins=edges, weights=weights)
    total = float(np.sum(profile))
    if total <= 0.0:
        return _empty_snapshot()
    centers = (edges[:-1] + edges[1:]) / 2.0
    poc_index = int(np.argmax(profile))
    selected = _value_area_bins(profile, poc_index, total * value_area_pct)
    value_low = float(np.min(centers[selected]))
    value_high = float(np.max(centers[selected]))
    concentration = float(profile[poc_index] / total)
    position = _profile_position(prices[-1], value_low, value_high)
    return float(centers[poc_index]), value_low, value_high, concentration, position


def _profile_position(close: float, value_low: float, value_high: float) -> float:
    if value_high == value_low:
        return 0.5
    position = (close - value_low) / (value_high - value_low)
    return float(np.clip(position, 0.0, 1.0))


def _value_area_bins(profile: np.ndarray, poc_index: int, target: float) -> np.ndarray:
    selected = [poc_index]
    included = float(profile[poc_index])
    left = poc_index - 1
    right = poc_index + 1
    while included < target and (left >= 0 or right < len(profile)):
        left_weight = profile[left] if left >= 0 else -1.0
        right_weight = profile[right] if right < len(profile) else -1.0
        if right_weight >= left_weight:
            selected.append(right)
            included += float(profile[right])
            right += 1
        else:
            selected.append(left)
            included += float(profile[left])
            left -= 1
    return np.array(selected, dtype=int)
