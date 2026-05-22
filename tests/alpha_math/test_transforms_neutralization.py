from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from project.alpha_math.neutralization import (
    demean_by_group,
    neutralize_by_exposure,
    residualize_against_factors,
    zscore_by_group,
)
from project.alpha_math.transforms import (
    decay_linear,
    rank_cross_sectional,
    robust_zscore,
    rolling_rank,
    rolling_zscore,
    signed_power,
    winsorize,
    zscore_cross_sectional,
)


def test_cross_sectional_transforms_handle_constant_rows_and_nans() -> None:
    frame = pd.DataFrame(
        {
            "a": [1.0, 1.0, np.nan],
            "b": [1.0, 2.0, 2.0],
            "c": [1.0, 3.0, 4.0],
        }
    )

    ranked = rank_cross_sectional(frame)
    zscored = zscore_cross_sectional(frame)

    assert ranked.iloc[0].nunique() == 1
    assert ranked.iloc[0]["a"] == pytest.approx(2.0 / 3.0)
    assert zscored.iloc[0].tolist() == [0.0, 0.0, 0.0]
    assert zscored.iloc[1]["c"] > zscored.iloc[1]["b"] > zscored.iloc[1]["a"]
    assert pd.isna(ranked.iloc[2]["a"])


def test_robust_zscore_and_winsorize_dampen_outliers() -> None:
    values = pd.Series([1.0, 2.0, 3.0, 100.0], index=list("abcd"))

    robust = robust_zscore(values)
    clipped = winsorize(values, lower=0.25, upper=0.75)

    assert robust["d"] > 40.0
    assert clipped.max() < 100.0
    assert clipped.min() > 1.0


def test_decay_and_rolling_transforms_preserve_warmup_nans() -> None:
    values = pd.Series([1.0, 2.0, 3.0, 4.0], index=pd.RangeIndex(4))

    decayed = decay_linear(values, window=3)
    ranked = rolling_rank(values, window=3)
    zscored = rolling_zscore(values, window=3)

    assert decayed.iloc[:2].isna().all()
    assert decayed.iloc[2] == pytest.approx(14.0 / 6.0)
    assert ranked.iloc[:2].isna().all()
    assert ranked.iloc[2] == pytest.approx(1.0)
    assert zscored.iloc[:2].isna().all()
    assert zscored.iloc[2] == pytest.approx(1.22474487139, rel=1e-6)


def test_signed_power_is_signed_and_elementwise() -> None:
    values = pd.Series([-4.0, -1.0, 0.0, 9.0])

    powered = signed_power(values, 0.5)

    assert powered.tolist() == pytest.approx([-2.0, -1.0, 0.0, 3.0])


def test_group_neutralization_handles_missing_groups() -> None:
    values = pd.Series([1.0, 3.0, 10.0, 7.0], index=["a", "b", "c", "d"])
    groups = pd.Series(["tech", "tech", "finance", None], index=values.index)

    demeaned = demean_by_group(values, groups)
    zscored = zscore_by_group(values, groups)

    assert demeaned["a"] == pytest.approx(-1.0)
    assert demeaned["b"] == pytest.approx(1.0)
    assert demeaned["c"] == pytest.approx(0.0)
    assert demeaned["d"] == pytest.approx(0.0)
    assert zscored["d"] == pytest.approx(0.0)


def test_exposure_neutralization_residualizes_linear_beta() -> None:
    exposure = pd.Series([0.0, 1.0, 2.0, 3.0], index=list("abcd"))
    values = 1.0 + 2.0 * exposure

    neutralized = neutralize_by_exposure(values, exposure)
    residualized = residualize_against_factors(values, exposure)

    assert neutralized.abs().max() < 1e-10
    assert residualized.abs().max() < 1e-10
