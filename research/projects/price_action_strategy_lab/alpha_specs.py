from __future__ import annotations

import pandas as pd

from project.alpha_math.cycle_indicators import fisher_transform
from project.alpha_math.cycle_indicators import inverse_fisher_transform
from project.alpha_math.ohlcv import relative_strength_index
from project.alpha_math.ohlcv import stochastic_oscillator
from project.alpha_math.price_action import bollinger_percent_b
from project.alpha_math.trade_profiles import failed_breakout_score as build_failed_breakout_score
from project.alpha_math.trade_profiles import failed_reversal_score as build_failed_reversal_score
from project.alpha_math.trade_profiles import hybrid_trend_volume_scores as build_hybrid_confirmation_scores
from project.alpha_math.trade_profiles import trend_volume_composite as build_trend_volume_composite
from project.alpha_math.trend_indicators import williams_r
from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.projects.price_action_strategy_lab.alpha_registry import AlphaRegistry
from research.projects.price_action_strategy_lab.alpha_registry import AlphaSpec
from research.projects.price_action_strategy_lab.alpha_registry import alpha_spec
from research.projects.price_action_strategy_lab.alpha_registry import build_alpha_registry
from research.projects.price_action_strategy_lab.price_action_pattern_specs import (
    BROAD_PRICE_ACTION_ALPHA_SPECS,
)


REVERSAL_MODES = (
    "cross_sectional_quintile",
    "time_series_threshold",
    "ranked_long_only",
)
REVERSAL_TAGS = ("reversal", "exhaustion", "price_action")
BREAKOUT_TAGS = ("breakout", "failure", "price_action")
CANDLESTICK_TAGS = ("candlestick", "reversal", "price_action")
VOLUME_TAGS = ("trend", "volume", "confirmation", "price_action")
HYBRID_TAGS = ("hybrid", "trend", "volume", "confirmation", "price_action")


@alpha_spec(
    name="bollinger_percent_b_mean_reversion_20",
    family="reversal_exhaustion",
    description="Bollinger percent-b mean reversion score.",
    inputs=("close",),
    horizons=(5,),
    expression_modes=REVERSAL_MODES,
    tags=REVERSAL_TAGS,
)
def bollinger_percent_b_mean_reversion_20(panel: Alpha101Panel) -> pd.DataFrame:
    return 0.5 - bollinger_percent_b(panel.close, period=20)


@alpha_spec(
    name="stochastic_mean_reversion_14",
    family="reversal_exhaustion",
    description="Stochastic percent-k mean reversion score.",
    inputs=("high", "low", "close"),
    horizons=(5,),
    expression_modes=REVERSAL_MODES,
    tags=REVERSAL_TAGS,
)
def stochastic_mean_reversion_14(panel: Alpha101Panel) -> pd.DataFrame:
    oscillator = stochastic_oscillator(panel.high, panel.low, panel.close, period=14)
    return 50.0 - oscillator.percent_k


@alpha_spec(
    name="williams_r_mean_reversion_14",
    family="reversal_exhaustion",
    description="Williams R mean reversion score.",
    inputs=("high", "low", "close"),
    horizons=(5,),
    expression_modes=REVERSAL_MODES,
    tags=REVERSAL_TAGS,
)
def williams_r_mean_reversion_14(panel: Alpha101Panel) -> pd.DataFrame:
    return -williams_r(panel.high, panel.low, panel.close, period=14).percent_r


@alpha_spec(
    name="fisher_transform_reversal_10",
    family="reversal_exhaustion",
    description="Fisher transform reversal score.",
    inputs=("high", "low", "close"),
    horizons=(5,),
    expression_modes=REVERSAL_MODES,
    tags=REVERSAL_TAGS,
)
def fisher_transform_reversal_10(panel: Alpha101Panel) -> pd.DataFrame:
    return -fisher_transform(panel.high, panel.low, panel.close, period=10).fisher


@alpha_spec(
    name="inverse_fisher_rsi_reversal_10",
    family="reversal_exhaustion",
    description="Inverse Fisher RSI reversal score.",
    inputs=("close",),
    horizons=(5,),
    expression_modes=REVERSAL_MODES,
    tags=REVERSAL_TAGS,
)
def inverse_fisher_rsi_reversal_10(panel: Alpha101Panel) -> pd.DataFrame:
    rsi = relative_strength_index(panel.close, period=10)
    return inverse_fisher_transform(50.0 - rsi, scale=0.05).transform


@alpha_spec(
    name="failed_breakout_score_20",
    family="breakout_continuation",
    description="Failed breakout pattern score.",
    inputs=("high", "low", "close", "volume"),
    horizons=(5,),
    expression_modes=REVERSAL_MODES,
    tags=BREAKOUT_TAGS,
)
def failed_breakout_score_20(panel: Alpha101Panel) -> pd.DataFrame:
    return build_failed_breakout_score(
        panel.high,
        panel.low,
        panel.close,
        panel.volume,
    ).score


@alpha_spec(
    name="failed_reversal_score",
    family="reversal_exhaustion",
    description="Failed reversal candlestick pattern score.",
    inputs=("open", "high", "low", "close", "volume"),
    horizons=(5,),
    expression_modes=REVERSAL_MODES,
    tags=CANDLESTICK_TAGS,
)
def failed_reversal_score(panel: Alpha101Panel) -> pd.DataFrame:
    return build_failed_reversal_score(
        panel.open,
        panel.high,
        panel.low,
        panel.close,
        panel.volume,
    ).score


@alpha_spec(
    name="trend_volume_composite",
    family="volume_confirmation",
    description="Trend and volume composite score.",
    inputs=("high", "low", "close", "volume"),
    horizons=(5,),
    expression_modes=REVERSAL_MODES,
    tags=VOLUME_TAGS,
)
def trend_volume_composite(panel: Alpha101Panel) -> pd.DataFrame:
    return build_trend_volume_composite(
        panel.high,
        panel.low,
        panel.close,
        panel.volume,
    ).score


@alpha_spec(
    name="hybrid_confirmation",
    family="volume_confirmation",
    description="Hybrid trend-volume confirmation score.",
    inputs=("high", "low", "close", "volume"),
    horizons=(5,),
    expression_modes=REVERSAL_MODES,
    tags=HYBRID_TAGS,
)
def hybrid_confirmation(panel: Alpha101Panel) -> pd.DataFrame:
    return build_hybrid_confirmation_scores(
        panel.high,
        panel.low,
        panel.close,
        panel.volume,
    ).confirmation_score


CORE_ALPHA_SPECS: tuple[AlphaSpec, ...] = (
    bollinger_percent_b_mean_reversion_20,
    stochastic_mean_reversion_14,
    williams_r_mean_reversion_14,
    fisher_transform_reversal_10,
    inverse_fisher_rsi_reversal_10,
    failed_breakout_score_20,
    failed_reversal_score,
    trend_volume_composite,
    hybrid_confirmation,
)


DEFAULT_ALPHA_SPECS: tuple[AlphaSpec, ...] = (
    *CORE_ALPHA_SPECS,
    *BROAD_PRICE_ACTION_ALPHA_SPECS,
)


def default_alpha_registry() -> AlphaRegistry:
    return build_alpha_registry(DEFAULT_ALPHA_SPECS)
