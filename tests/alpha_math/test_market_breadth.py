from __future__ import annotations

from collections.abc import Mapping

import pandas as pd
import pytest

from project.alpha_math.market_breadth import (
    BreadthThrustComposite,
    BreadthDispersionMetrics,
    BreadthVolatilityRegime,
    breadth_thrust_composite,
    breadth_thrust_metrics,
    breadth_dispersion_metrics,
    breadth_thrust_volatility_regime,
    nested_universe_breadth_metrics,
    NestedUniverseBreadthMetrics,
    market_breadth_metrics,
    relative_rotation_metrics,
)


def test_market_breadth_metrics_capture_bullish_breadth() -> None:
    close = pd.DataFrame(
        {
            "a": [10.0, 11.0, 12.0, 13.0],
            "b": [9.0, 10.0, 11.0, 12.0],
            "c": [8.0, 9.0, 10.0, 11.0],
        }
    )

    breadth = market_breadth_metrics(
        close,
        moving_average_window=2,
        high_low_window=3,
    )

    assert breadth.advance_decline_line.iloc[-1] > 0.0
    assert breadth.breadth_score.iloc[-1] > 0.0
    assert breadth.bullish.iloc[-1]


def test_relative_rotation_metrics_label_quadrants() -> None:
    close = pd.DataFrame(
        {
            "leader": [100.0, 102.0, 104.0, 106.0, 108.0, 110.0],
            "laggard": [100.0, 99.0, 98.0, 97.0, 96.0, 95.0],
        }
    )
    benchmark = pd.Series([100.0] * 6)

    rotation = relative_rotation_metrics(close, benchmark, momentum_window=2)

    assert rotation.leading["leader"].iloc[-1]
    assert rotation.lagging["laggard"].iloc[-1]
    assert rotation.score["leader"].iloc[-1] > rotation.score["laggard"].iloc[-1]


def test_breadth_thrust_metrics_trigger_after_washout() -> None:
    close = pd.DataFrame(
        {
            "a": [10.0, 9.0, 8.0, 7.0, 6.0, 7.0, 8.0, 9.0],
            "b": [10.0, 9.0, 8.0, 7.0, 6.0, 7.0, 8.0, 9.0],
            "c": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0],
        }
    )

    metrics = breadth_thrust_metrics(
        close,
        thrust_window=2,
        washout_window=4,
    )

    assert metrics.washout.iloc[-1]
    assert metrics.thrust.iloc[-1]
    assert metrics.signal.iloc[-1]
    assert metrics.score.iloc[-1] > 0.0


def test_breadth_thrust_composite_supports_multiple_universes() -> None:
    universes = _breadth_universes()

    composite = breadth_thrust_composite(
        universes,
        thrust_window=2,
        washout_window=4,
    )

    assert isinstance(composite, BreadthThrustComposite)
    assert composite.universe_signal["sector"].iloc[-1]
    assert composite.universe_signal["asset"].iloc[-1]
    assert composite.composite_score.iloc[-1] > 0.0
    assert composite.bullish.iloc[-1]


def test_breadth_dispersion_metrics_capture_participation_decay() -> None:
    universes = _breadth_universes()

    dispersion = breadth_dispersion_metrics(
        universes,
        short_window=2,
        long_window=4,
    )

    assert isinstance(dispersion, BreadthDispersionMetrics)
    assert dispersion.participation_decay.iloc[-1] < 0.0
    assert dispersion.universe_breadth_score["sector"].iloc[-1] > dispersion.universe_breadth_score["asset"].iloc[-1]


def test_breadth_thrust_volatility_regime_combines_squeeze_and_thrust() -> None:
    universes = _breadth_universes()
    benchmark_close = pd.Series([100.0] * 8)

    regime = breadth_thrust_volatility_regime(
        benchmark_close,
        universes,
        thrust_window=2,
        washout_window=4,
        squeeze_window=2,
        squeeze_lookback=2,
    )

    assert isinstance(regime, BreadthVolatilityRegime)
    assert regime.bullish.iloc[-1]
    assert regime.squeeze.iloc[-1]


def test_nested_universe_breadth_metrics_normalize_by_universe_size() -> None:
    universes = {
        "large": pd.DataFrame(
            {
                "a": [10.0, 9.0, 8.0, 7.0, 6.0, 7.0, 8.0, 9.0],
                "b": [10.0, 9.0, 8.0, 7.0, 6.0, 7.0, 8.0, 9.0],
                "c": [10.0, 9.0, 8.0, 7.0, 6.0, 7.0, 8.0, 9.0],
                "d": [10.0, 9.0, 8.0, 7.0, 6.0, 7.0, 8.0, 9.0],
            }
        ),
        "small": pd.DataFrame(
            {
                "e": [20.0, 19.0, 18.0, 17.0, 16.0, 17.0, 18.0, 19.0],
                "f": [20.0, 19.0, 18.0, 17.0, 16.0, 17.0, 18.0, 17.0],
            }
        ),
    }

    metrics = nested_universe_breadth_metrics(universes)

    assert isinstance(metrics, NestedUniverseBreadthMetrics)
    assert metrics.universe_member_count["large"] == pytest.approx(4.0)
    assert metrics.coverage_weight["large"] == pytest.approx(1.0)
    assert metrics.coverage_weight["small"] < metrics.coverage_weight["large"]
    assert metrics.normalized_breadth_score["small"].iloc[-1] > metrics.universe_breadth_score["small"].iloc[-1]
    assert metrics.normalized_composite_score.iloc[-1] > metrics.raw_composite_score.iloc[-1]
    assert metrics.expansion_factor.iloc[-1] == pytest.approx((2.0 / 4.0) ** 0.5)


def _breadth_universes() -> Mapping[str, pd.DataFrame]:
    sector = pd.DataFrame(
        {
            "x": [10.0, 9.0, 8.0, 7.0, 6.0, 7.0, 8.0, 9.0],
            "y": [10.0, 9.0, 8.0, 7.0, 6.0, 7.0, 8.0, 9.0],
            "z": [10.0, 9.0, 8.0, 7.0, 6.0, 7.0, 8.0, 9.0],
        }
    )
    asset = pd.DataFrame(
        {
            "u": [20.0, 19.0, 18.0, 17.0, 16.0, 17.0, 18.0, 19.0],
            "v": [20.0, 19.0, 18.0, 17.0, 16.0, 17.0, 18.0, 19.0],
            "w": [20.0, 19.0, 18.0, 17.0, 16.0, 17.0, 18.0, 17.0],
        }
    )
    return {"sector": sector, "asset": asset}
