from __future__ import annotations

import numpy as np
import pandas as pd

from project.alpha_math.cycle_indicators import (
    DetrendedPriceOscillatorResult,
    FisherTransformResult,
    InverseFisherResult,
    MassIndexResult,
    detrended_price_oscillator,
    fisher_transform,
    inverse_fisher_transform,
    mass_index,
)


def test_fisher_transform_and_inverse_fisher_sharpen_trend_turns() -> None:
    base = pd.Series([float(value) for value in range(100, 140)])
    high = pd.DataFrame({"a": base + 1.0, "b": base + 2.0})
    low = high - 2.0
    close = high - 0.25

    fisher = fisher_transform(high, low, close, period=10)
    inverse = inverse_fisher_transform(fisher.fisher)

    assert isinstance(fisher, FisherTransformResult)
    assert isinstance(inverse, InverseFisherResult)
    assert fisher.bullish.iloc[-1].all()
    assert fisher.fisher.iloc[-1].gt(0.0).all()
    assert inverse.strong_bullish.iloc[-1].all()
    assert inverse.transform.iloc[-1].gt(0.0).all()


def test_dpo_and_mass_index_separate_cycles_from_bulges() -> None:
    cycle = pd.Series(100.0 + (5.0 * np.sin(np.linspace(0.0, 4.0 * np.pi, 80))))
    dpo = detrended_price_oscillator(cycle, period=20)

    base = pd.Series(np.arange(100.0, 180.0))
    ranges = pd.Series(np.linspace(1.0, 10.0, 80))
    high = base + (ranges / 2.0)
    low = base - (ranges / 2.0)
    bulge = mass_index(high, low)

    assert isinstance(dpo, DetrendedPriceOscillatorResult)
    assert isinstance(bulge, MassIndexResult)
    assert dpo.bullish.any()
    assert dpo.bearish.any()
    assert bulge.mass_index.max() > 27.0
    assert bulge.bulge.fillna(False).any()
