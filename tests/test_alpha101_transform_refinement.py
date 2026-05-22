from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
import sys

import pandas as pd  # type: ignore[import-untyped]


NOTEBOOK_ROOT = Path(__file__).resolve().parents[1] / "research/notebooks/alpha_001"
if str(NOTEBOOK_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_ROOT))

MODULE_PATH = NOTEBOOK_ROOT / "research/alpha101_factory.py"
SPEC = spec_from_file_location("alpha101_factory_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE: Any = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_family_transforms_include_smoothed_threshold_variants() -> None:
    transforms = MODULE.family_transforms("price_reversal")
    assert "ewm3_threshold_top_bottom" in transforms
    assert "ewm5_threshold_top_bottom" in transforms
    assert "ewm10_threshold_top_bottom" in transforms
    volume = MODULE.family_transforms("volume_liquidity")
    volatility = MODULE.family_transforms("volatility_range")
    residual = MODULE.family_transforms("correlation_relative_value")
    assert "ewm3_threshold_top_bottom" in volume
    assert "ewm5_threshold_top_bottom" in volatility
    assert "ewm10_threshold_top_bottom" in residual


def test_portfolio_signal_transforms_include_smoothed_threshold_variants() -> None:
    volume = MODULE.portfolio_signal_transforms("volume_liquidity")
    vol = MODULE.portfolio_signal_transforms("volatility_range")
    price = MODULE.portfolio_signal_transforms("price_reversal")
    assert "ewm3_threshold_top_bottom" in volume
    assert "ewm5_threshold_top_bottom" in vol
    assert "ewm10_threshold_top_bottom" in price
    residual = MODULE.portfolio_signal_transforms("correlation_relative_value")
    assert "ewm3_threshold_top_bottom" in residual
    assert "ewm5_threshold_top_bottom" in residual
    assert "ewm10_threshold_top_bottom" in residual


def test_smoothed_threshold_top_bottom_keeps_extremes() -> None:
    frame = pd.DataFrame({"A": [1.0, 2.0, 3.0, 4.0], "B": [4.0, 3.0, 2.0, 1.0], "C": [2.0, 2.0, 2.0, 2.0]})
    result = MODULE.smoothed_threshold_top_bottom(frame, 3, 2)
    assert result.iloc[-1].dropna().index.tolist() == ["A"]
    assert result.iloc[-1].isna().sum() == 2
