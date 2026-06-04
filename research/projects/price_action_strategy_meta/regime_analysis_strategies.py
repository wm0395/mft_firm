from __future__ import annotations

import numpy as np
import pandas as pd

from project.alpha_math.cycle_indicators import fisher_transform
from project.alpha_math.cycle_indicators import inverse_fisher_transform
from project.alpha_math.cycle_indicators import mass_index
from project.alpha_math.gap_regimes import opening_gap_regime
from project.alpha_math.market_structure import support_resistance_trendlines
from project.alpha_math.ohlcv import breakout_above, breakout_below, relative_volume
from project.alpha_math.price_action import bollinger_squeeze, chandelier_exit, parabolic_sar
from project.alpha_math.trend_regimes import supertrend
from project.alpha_math.trend_regimes import choppiness_index
from project.alpha_math.trend_indicators import aroon
from project.alpha_math.trend_indicators import ichimoku_cloud
from project.alpha_math.trend_indicators import elder_ray, ultimate_oscillator
from project.alpha_math.trend_indicators import know_sure_thing
from project.alpha_math.ohlcv import relative_strength_index
from project.alpha_math.volume_flow import ease_of_movement
from project.alpha_math.volume_profile import volume_profile_levels
from research.projects.price_action_strategy_meta.strategy_spec import StrategySpec


def extra_strategy_specs() -> list[StrategySpec]:
    return [
        StrategySpec("squeeze_breakout_20", "breakout_continuation", "breakout after Bollinger squeeze", squeeze_breakout_score),
        StrategySpec("relative_volume_breakout_20", "breakout_continuation", "breakout score scaled by relative volume", relative_volume_breakout_score),
        StrategySpec("chandelier_trend", "trend_following", "chandelier exit trend", chandelier_score),
        StrategySpec("elder_ray_trend", "trend_following", "elder ray power spread", elder_ray_score),
        StrategySpec("supertrend_direction_10", "trend_following", "supertrend direction", supertrend_score),
        StrategySpec("parabolic_sar_trend", "trend_following", "parabolic SAR trend", parabolic_sar_score),
        StrategySpec("aroon_oscillator_25", "trend_following", "Aroon oscillator", aroon_score),
        StrategySpec("ichimoku_kijun_spread_26", "trend_following", "Ichimoku tenkan-kijun spread", ichimoku_score),
        StrategySpec("kst_momentum_9", "trend_following", "KST minus signal", kst_momentum_score),
        StrategySpec("ultimate_oscillator_reversal", "reversal_exhaustion", "ultimate oscillator mean reversion", ultimate_oscillator_score),
        StrategySpec("fisher_transform_reversal_10", "reversal_exhaustion", "fisher transform reversal", fisher_reversal_score),
        StrategySpec("inverse_fisher_rsi_reversal_10", "reversal_exhaustion", "inverse Fisher RSI reversal", inverse_fisher_rsi_score),
        StrategySpec("mass_index_reversal_25", "reversal_exhaustion", "mass index reversal bulge", mass_index_reversal_score),
        StrategySpec("opening_gap_regime_score", "gap_reaction", "gap continuation minus fade", opening_gap_regime_score),
        StrategySpec("ease_of_movement_14", "volume_confirmation", "ease of movement", ease_of_movement_score),
        StrategySpec("support_trendline_position_20", "structure_levels", "support trendline position", support_trendline_position_score),
        StrategySpec("volume_profile_position_20", "structure_levels", "volume profile position", volume_profile_position_score),
        StrategySpec("choppiness_inverse_14", "trend_following", "inverse choppiness index", choppiness_inverse_score),
    ]


def squeeze_breakout_score(panel) -> pd.DataFrame:
    squeeze = bollinger_squeeze(panel.close)
    score = breakout_above(panel.close, 20).astype(float) - breakout_below(panel.close, 20).astype(float)
    return score.where(squeeze, 0.0)


def relative_volume_breakout_score(panel) -> pd.DataFrame:
    breakout = breakout_above(panel.close, 20).astype(float) - breakout_below(panel.close, 20).astype(float)
    participation = relative_volume(panel.volume, 20).fillna(1.0)
    return breakout * participation


def chandelier_score(panel) -> pd.DataFrame:
    stops = chandelier_exit(panel.high, panel.low, panel.close)
    long_side = panel.close.gt(stops.long_stop).astype(float)
    short_side = panel.close.lt(stops.short_stop).astype(float)
    return long_side - short_side


def elder_ray_score(panel) -> pd.DataFrame:
    result = elder_ray(panel.high, panel.low, panel.close)
    return result.bull_power.sub(result.bear_power)


def supertrend_score(panel) -> pd.DataFrame:
    trend = supertrend(panel.high, panel.low, panel.close).trend_up
    return trend.astype(float).mul(2.0).sub(1.0)


def parabolic_sar_score(panel) -> pd.DataFrame:
    return parabolic_sar(panel.high, panel.low, panel.close).trend


def aroon_score(panel) -> pd.DataFrame:
    return aroon(panel.high, panel.low).oscillator


def ichimoku_score(panel) -> pd.DataFrame:
    cloud = ichimoku_cloud(panel.high, panel.low, panel.close)
    return cloud.tenkan_sen.sub(cloud.kijun_sen)


def kst_momentum_score(panel) -> pd.DataFrame:
    kst = know_sure_thing(panel.close)
    return kst.kst.sub(kst.signal)


def fisher_reversal_score(panel) -> pd.DataFrame:
    return -fisher_transform(panel.high, panel.low, panel.close).fisher


def ultimate_oscillator_score(panel) -> pd.DataFrame:
    return ultimate_oscillator(panel.high, panel.low, panel.close).oscillator - 50.0


def opening_gap_regime_score(panel) -> pd.DataFrame:
    regime = opening_gap_regime(panel.open, panel.high, panel.low, panel.close)
    return regime.gap_continuation.astype(float) - regime.gap_faded.astype(float)


def inverse_fisher_rsi_score(panel) -> pd.DataFrame:
    rsi = relative_strength_index(panel.close)
    return inverse_fisher_transform(50.0 - rsi, scale=0.05).transform


def mass_index_reversal_score(panel) -> pd.DataFrame:
    result = mass_index(panel.high, panel.low)
    return result.reversal_bulge.astype(float) - result.bulge.astype(float)


def support_trendline_position_score(panel) -> pd.DataFrame:
    trendlines = support_resistance_trendlines(panel.high, panel.low, lookback=20)
    spread = (trendlines.resistance - trendlines.support).replace(0.0, np.nan)
    return panel.close.sub(trendlines.support).div(spread).sub(0.5)


def volume_profile_position_score(panel) -> pd.DataFrame:
    levels = volume_profile_levels(panel.close, panel.volume, window=20, bins=20, value_area_pct=0.7)
    return levels.position.sub(0.5)


def choppiness_inverse_score(panel) -> pd.DataFrame:
    return 50.0 - choppiness_index(panel.high, panel.low, panel.close).index


def ease_of_movement_score(panel) -> pd.DataFrame:
    return ease_of_movement(panel.high, panel.low, panel.volume).smoothed_eom
