from __future__ import annotations

import pandas as pd
import pytest

from project.alpha_math.volume_profile import (
    volume_profile_levels,
    volume_profile_regime,
)


def test_volume_profile_levels_follow_rolling_value_area() -> None:
    close = pd.Series([10.0, 11.0, 12.0, 13.0])
    volume = pd.Series([1.0, 1.0, 1.0, 10.0])

    levels = volume_profile_levels(close, volume, window=3, bins=3)
    regime = volume_profile_regime(close, volume, window=3, bins=3)

    assert levels.point_of_control.iloc[2] == pytest.approx(10.3333333333)
    assert levels.value_area_low.iloc[2] == pytest.approx(10.3333333333)
    assert levels.value_area_high.iloc[2] == pytest.approx(11.6666666667)
    assert levels.concentration.iloc[2] == pytest.approx(1.0 / 3.0)
    assert levels.position.iloc[2] == pytest.approx(1.0)

    assert levels.point_of_control.iloc[3] == pytest.approx(12.6666666667)
    assert levels.value_area_low.iloc[3] == pytest.approx(12.6666666667)
    assert levels.value_area_high.iloc[3] == pytest.approx(12.6666666667)
    assert levels.concentration.iloc[3] == pytest.approx(10.0 / 12.0)
    assert levels.position.iloc[3] == pytest.approx(0.5)

    assert bool(regime.above_value_area.iloc[3])
    assert not bool(regime.inside_value_area.iloc[3])
    assert not bool(regime.accepted.iloc[3])


def test_volume_profile_levels_support_frames_and_constant_windows() -> None:
    close = pd.DataFrame({"asset": [10.0, 10.0, 10.0]})
    volume = pd.DataFrame({"asset": [1.0, 2.0, 3.0]})

    levels = volume_profile_levels(close, volume, window=3, bins=3)
    regime = volume_profile_regime(close, volume, window=3, bins=3)

    assert isinstance(levels.point_of_control, pd.DataFrame)
    assert levels.point_of_control.iloc[-1, 0] == pytest.approx(10.0)
    assert levels.value_area_low.iloc[-1, 0] == pytest.approx(10.0)
    assert levels.value_area_high.iloc[-1, 0] == pytest.approx(10.0)
    assert levels.concentration.iloc[-1, 0] == pytest.approx(0.5)
    assert levels.position.iloc[-1, 0] == pytest.approx(0.5)
    assert bool(regime.inside_value_area.iloc[-1, 0])
    assert bool(regime.accepted.iloc[-1, 0])
