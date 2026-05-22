from __future__ import annotations

import numpy as np
import pandas as pd


def demean_by_group(values: pd.Series, groups: pd.Series) -> pd.Series:
    aligned_values, aligned_groups = values.align(groups, join="left")
    group_labels = _normalize_groups(aligned_groups)
    means = aligned_values.groupby(group_labels).transform("mean")
    return aligned_values - means


def zscore_by_group(values: pd.Series, groups: pd.Series) -> pd.Series:
    aligned_values, aligned_groups = values.align(groups, join="left")
    group_labels = _normalize_groups(aligned_groups)
    grouped = aligned_values.groupby(group_labels)
    means = grouped.transform("mean")
    std = grouped.transform("std").replace(0, np.nan)
    return ((aligned_values - means) / std).fillna(0.0)


def neutralize_by_exposure(values: pd.Series, exposures: pd.Series | pd.DataFrame) -> pd.Series:
    frame = _exposure_frame(values, exposures)
    if frame is None:
        return values - values.mean()
    y = frame.pop("_value").to_numpy(dtype=float)
    x = frame.to_numpy(dtype=float)
    beta = np.linalg.lstsq(_add_intercept(x), y, rcond=None)[0]
    fitted = _add_intercept(x) @ beta
    residuals = pd.Series(y - fitted, index=frame.index, dtype=float)
    result = values.astype(float).copy()
    result.loc[residuals.index] = residuals
    return result


def residualize_against_factors(values: pd.Series, factors: pd.Series | pd.DataFrame) -> pd.Series:
    return neutralize_by_exposure(values, factors)


def _normalize_groups(groups: pd.Series) -> pd.Series:
    return groups.fillna("__ungrouped__").astype(str)


def _exposure_frame(
    values: pd.Series,
    exposures: pd.Series | pd.DataFrame,
) -> pd.DataFrame | None:
    if isinstance(exposures, pd.Series):
        frame = pd.DataFrame({"_exposure_0": exposures})
    else:
        frame = exposures.copy()
    frame["_value"] = values
    frame = frame.dropna(axis=0, how="any")
    if frame.empty:
        return None
    return frame


def _add_intercept(matrix: np.ndarray) -> np.ndarray:
    intercept = np.ones((matrix.shape[0], 1), dtype=float)
    return np.hstack([intercept, matrix]) if matrix.size else intercept
