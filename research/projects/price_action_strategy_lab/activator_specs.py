from __future__ import annotations

import numpy as np
import pandas as pd

from project.alpha_math.gap_regimes import opening_gap_regime
from project.alpha_math.market_breadth import market_breadth_metrics
from project.alpha_math.ohlcv import relative_strength_index
from project.alpha_math.ohlcv import stochastic_oscillator
from project.alpha_math.regime_filters import higher_timeframe_regime_filters
from project.alpha_math.regime_filters import volatility_regime_filters
from project.alpha_math.trend_indicators import williams_r
from project.alpha_math.trend_regimes import choppiness_index
from project.alpha_math.trend_regimes import supertrend
from project.alpha_math.volume_profile import volume_profile_regime
from project.alpha_math.relative_strength import multi_horizon_relative_strength_rank
from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.projects.price_action_strategy_lab.activator_registry import ActivatorRegistry
from research.projects.price_action_strategy_lab.activator_registry import ActivatorSpec
from research.projects.price_action_strategy_lab.activator_registry import activator_spec
from research.projects.price_action_strategy_lab.activator_registry import build_activator_registry


ALPHA_FAMILY_ACTIVATORS: dict[str, tuple[str, ...]] = {
    "breakout_continuation": (
        "breakout_environment",
        "trend_alignment",
        "volatility_expansion",
        "breadth_thrust",
        "relative_strength_leader",
        "volume_acceptance",
    ),
    "gap_reaction": (
        "gap_continuation",
        "gap_fade",
        "mean_reversion_environment",
    ),
    "reversal_exhaustion": (
        "mean_reversion_environment",
        "oscillator_extreme",
        "gap_fade",
        "volatility_compression",
        "breadth_risk_off",
    ),
    "structure_levels": (
        "volume_acceptance",
        "trend_alignment",
        "relative_strength_leader",
    ),
    "trend_following": (
        "trend_alignment",
        "volatility_expansion",
        "breadth_thrust",
        "relative_strength_leader",
        "volume_acceptance",
    ),
    "volume_confirmation": (
        "volume_acceptance",
        "breadth_thrust",
        "trend_alignment",
        "relative_strength_leader",
    ),
}


def _trend_alignment_mask(panel: Alpha101Panel) -> pd.DataFrame:
    higher = higher_timeframe_regime_filters(panel.close, _higher_close(panel.close))
    trend = volatility_regime_filters(panel.high, panel.low, panel.close)
    supertrend_mask = supertrend(panel.high, panel.low, panel.close).bullish
    return _and(supertrend_mask, higher.bullish_regime, trend.trending)


def _volatility_expansion_mask(panel: Alpha101Panel) -> pd.DataFrame:
    regime = volatility_regime_filters(panel.high, panel.low, panel.close)
    return _and(regime.expanding_volatility, regime.high_volatility)


def _volatility_compression_mask(panel: Alpha101Panel) -> pd.DataFrame:
    regime = volatility_regime_filters(panel.high, panel.low, panel.close)
    return _and(regime.compressing_volatility, regime.low_volatility)


def _breadth_thrust_mask(panel: Alpha101Panel) -> pd.DataFrame:
    breadth = market_breadth_metrics(panel.close)
    regime = volatility_regime_filters(panel.high, panel.low, panel.close)
    return _and(_broadcast_date_mask(breadth.bullish, panel.close), regime.expanding_volatility)


def _breadth_risk_off_mask(panel: Alpha101Panel) -> pd.DataFrame:
    breadth = market_breadth_metrics(panel.close)
    regime = volatility_regime_filters(panel.high, panel.low, panel.close)
    return _and(_broadcast_date_mask(breadth.bearish, panel.close), regime.high_volatility)


def _gap_continuation_mask(panel: Alpha101Panel) -> pd.DataFrame:
    regime = opening_gap_regime(panel.open, panel.high, panel.low, panel.close)
    return regime.gap_continuation.fillna(False)


def _gap_fade_mask(panel: Alpha101Panel) -> pd.DataFrame:
    regime = opening_gap_regime(panel.open, panel.high, panel.low, panel.close)
    return regime.gap_faded.fillna(False)


def _volume_acceptance_mask(panel: Alpha101Panel) -> pd.DataFrame:
    regime = volume_profile_regime(panel.close, panel.volume)
    return _or(regime.accepted, regime.above_value_area)


def _relative_strength_leader_mask(panel: Alpha101Panel) -> pd.DataFrame:
    ranking = multi_horizon_relative_strength_rank(panel.close)
    return ranking.leader.fillna(False)


def _relative_strength_laggard_mask(panel: Alpha101Panel) -> pd.DataFrame:
    ranking = multi_horizon_relative_strength_rank(panel.close)
    return ranking.laggard.fillna(False)


def _oscillator_extreme_mask(panel: Alpha101Panel) -> pd.DataFrame:
    rsi = relative_strength_index(panel.close, period=14)
    stochastic = stochastic_oscillator(panel.high, panel.low, panel.close, period=14).percent_k
    williams = williams_r(panel.high, panel.low, panel.close, period=14).percent_r
    mask = (
        rsi.le(30.0)
        | rsi.ge(70.0)
        | stochastic.le(20.0)
        | stochastic.ge(80.0)
        | williams.le(-80.0)
        | williams.ge(-20.0)
    )
    return mask.fillna(False)


def _mean_reversion_environment_mask(panel: Alpha101Panel) -> pd.DataFrame:
    regime = volatility_regime_filters(panel.high, panel.low, panel.close)
    chop = choppiness_index(panel.high, panel.low, panel.close)
    breadth = _breadth_risk_off_mask(panel)
    return _and(regime.mean_reverting, chop.choppy, breadth)


def _breakout_environment_mask(panel: Alpha101Panel) -> pd.DataFrame:
    return _and(
        _trend_alignment_mask(panel),
        _volatility_expansion_mask(panel),
        _breadth_thrust_mask(panel),
        _relative_strength_leader_mask(panel),
    )


@activator_spec(
    name="trend_alignment",
    family="trend",
    description="Higher-timeframe trend aligned with supertrend and trend filters.",
    tags=("trend", "higher_timeframe", "supertrend"),
)
def trend_alignment(panel: Alpha101Panel) -> pd.DataFrame:
    return _trend_alignment_mask(panel)


@activator_spec(
    name="breakout_environment",
    family="trend",
    description="Trend alignment plus breadth, expansion, and relative-strength support.",
    tags=("breakout", "trend", "breadth", "relative_strength"),
)
def breakout_environment(panel: Alpha101Panel) -> pd.DataFrame:
    return _breakout_environment_mask(panel)


@activator_spec(
    name="mean_reversion_environment",
    family="reversal",
    description="Choppy mean-reverting regime with weak breadth and exhaustion signals.",
    tags=("reversal", "mean_reversion", "choppy"),
)
def mean_reversion_environment(panel: Alpha101Panel) -> pd.DataFrame:
    return _mean_reversion_environment_mask(panel)


@activator_spec(
    name="volatility_expansion",
    family="volatility",
    description="Expansion after compression with high realized volatility.",
    tags=("volatility", "expansion"),
)
def volatility_expansion(panel: Alpha101Panel) -> pd.DataFrame:
    return _volatility_expansion_mask(panel)


@activator_spec(
    name="volatility_compression",
    family="volatility",
    description="Low-volatility compression regime.",
    tags=("volatility", "compression"),
)
def volatility_compression(panel: Alpha101Panel) -> pd.DataFrame:
    return _volatility_compression_mask(panel)


@activator_spec(
    name="breadth_thrust",
    family="breadth",
    description="Positive market breadth with expansion bias.",
    tags=("breadth", "thrust"),
)
def breadth_thrust(panel: Alpha101Panel) -> pd.DataFrame:
    return _breadth_thrust_mask(panel)


@activator_spec(
    name="breadth_risk_off",
    family="breadth",
    description="Bearish breadth with elevated volatility.",
    tags=("breadth", "risk_off"),
)
def breadth_risk_off(panel: Alpha101Panel) -> pd.DataFrame:
    return _breadth_risk_off_mask(panel)


@activator_spec(
    name="gap_continuation",
    family="gap",
    description="Opening-gap continuation regime.",
    tags=("gap", "continuation"),
)
def gap_continuation(panel: Alpha101Panel) -> pd.DataFrame:
    return _gap_continuation_mask(panel)


@activator_spec(
    name="gap_fade",
    family="gap",
    description="Opening-gap fade regime.",
    tags=("gap", "fade"),
)
def gap_fade(panel: Alpha101Panel) -> pd.DataFrame:
    return _gap_fade_mask(panel)


@activator_spec(
    name="volume_acceptance",
    family="volume",
    description="Volume profile acceptance and value-area participation.",
    tags=("volume", "acceptance", "value_area"),
)
def volume_acceptance(panel: Alpha101Panel) -> pd.DataFrame:
    return _volume_acceptance_mask(panel)


@activator_spec(
    name="relative_strength_leader",
    family="relative_strength",
    description="Multi-horizon relative-strength leader mask.",
    tags=("relative_strength", "leader"),
)
def relative_strength_leader(panel: Alpha101Panel) -> pd.DataFrame:
    return _relative_strength_leader_mask(panel)


@activator_spec(
    name="relative_strength_laggard",
    family="relative_strength",
    description="Multi-horizon relative-strength laggard mask.",
    tags=("relative_strength", "laggard"),
)
def relative_strength_laggard(panel: Alpha101Panel) -> pd.DataFrame:
    return _relative_strength_laggard_mask(panel)


@activator_spec(
    name="oscillator_extreme",
    family="oscillator",
    description="Composite oscillator extreme mask from RSI, stochastic, and Williams %R.",
    tags=("oscillator", "extreme"),
)
def oscillator_extreme(panel: Alpha101Panel) -> pd.DataFrame:
    return _oscillator_extreme_mask(panel)


DEFAULT_ACTIVATOR_SPECS: tuple[ActivatorSpec, ...] = (
    trend_alignment,
    breakout_environment,
    mean_reversion_environment,
    volatility_expansion,
    volatility_compression,
    breadth_thrust,
    breadth_risk_off,
    gap_continuation,
    gap_fade,
    volume_acceptance,
    relative_strength_leader,
    relative_strength_laggard,
    oscillator_extreme,
)


def build_shared_activator_masks(panel: Alpha101Panel, names: tuple[str, ...]) -> dict[str, pd.DataFrame]:
    requested = set(names)
    cache: dict[str, pd.DataFrame] = {}
    builders = {
        "trend_alignment": lambda: _trend_alignment_mask(panel),
        "volatility_expansion": lambda: _volatility_expansion_mask(panel),
        "volatility_compression": lambda: _volatility_compression_mask(panel),
        "breadth_thrust": lambda: _breadth_thrust_mask(panel),
        "breadth_risk_off": lambda: _breadth_risk_off_mask(panel),
        "gap_continuation": lambda: _gap_continuation_mask(panel),
        "gap_fade": lambda: _gap_fade_mask(panel),
        "volume_acceptance": lambda: _volume_acceptance_mask(panel),
        "relative_strength_leader": lambda: _relative_strength_leader_mask(panel),
        "relative_strength_laggard": lambda: _relative_strength_laggard_mask(panel),
        "oscillator_extreme": lambda: _oscillator_extreme_mask(panel),
    }

    def mask(name: str) -> pd.DataFrame:
        if name in cache:
            return cache[name]
        if name == "breakout_environment":
            cache[name] = _and(
                mask("trend_alignment"),
                mask("volatility_expansion"),
                mask("breadth_thrust"),
                mask("relative_strength_leader"),
            )
        elif name == "mean_reversion_environment":
            cache[name] = _and(_volatility_regime_mean_reverting(panel), _choppy_mask(panel), mask("breadth_risk_off"))
        elif name in builders:
            cache[name] = builders[name]()
        return cache[name]

    supported = set(builders) | {"breakout_environment", "mean_reversion_environment"}
    return {name: mask(name) & panel.active_mask.fillna(False) for name in names if name in requested and name in supported}


def default_activator_registry() -> ActivatorRegistry:
    return build_activator_registry(DEFAULT_ACTIVATOR_SPECS)


def _volatility_regime_mean_reverting(panel: Alpha101Panel) -> pd.DataFrame:
    return volatility_regime_filters(panel.high, panel.low, panel.close).mean_reverting


def _choppy_mask(panel: Alpha101Panel) -> pd.DataFrame:
    return choppiness_index(panel.high, panel.low, panel.close).choppy


def _higher_close(close: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(close.index, pd.DatetimeIndex):
        return close
    weekly = close.resample("W-FRI").last()
    return weekly.reindex(close.index).ffill()


def _broadcast_date_mask(mask: pd.Series, like: pd.DataFrame) -> pd.DataFrame:
    values = np.broadcast_to(mask.fillna(False).to_numpy()[:, None], like.shape)
    return pd.DataFrame(values, index=like.index, columns=like.columns).astype(bool)


def _and(*masks: pd.DataFrame) -> pd.DataFrame:
    frame = masks[0].fillna(False).copy()
    for mask in masks[1:]:
        frame &= mask.fillna(False)
    return frame.astype(bool)


def _or(*masks: pd.DataFrame) -> pd.DataFrame:
    frame = masks[0].fillna(False).copy()
    for mask in masks[1:]:
        frame |= mask.fillna(False)
    return frame.astype(bool)
