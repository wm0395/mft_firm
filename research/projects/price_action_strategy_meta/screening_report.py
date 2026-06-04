from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from project.alpha_math.gap_regimes import opening_gap_metrics
from project.alpha_math.market_structure import (
    multi_timeframe_confirmation,
    support_resistance_levels,
)
from project.alpha_math.ohlcv import (
    breakout_above,
    breakout_below,
    directional_movement_index,
    money_flow_index,
    on_balance_volume,
    relative_strength_index,
    stochastic_oscillator,
    macd,
)
from project.alpha_math.price_action import bollinger_percent_b
from project.alpha_math.trade_profiles import (
    failed_breakout_score,
    failed_reversal_score,
    hybrid_trend_volume_scores,
    trend_volume_composite,
)
from project.alpha_math.trend_indicators import (
    commodity_channel_index,
    chande_momentum_oscillator,
    vortex_indicator,
    williams_r,
)
from project.alpha_math.trend_regimes import trix
from project.alpha_math.trend_regimes import keltner_channels
from project.alpha_math.cycle_indicators import detrended_price_oscillator
from project.alpha_math.volume_flow import (
    chaikin_money_flow,
    chaikin_oscillator,
    force_index,
    price_volume_trend,
)
from research.projects.price_action_strategy_meta.strategy_spec import StrategySpec
from research.notebooks.alpha_001.research.alpha101_engine import (
    Alpha101Panel,
    fast_rank_ic_by_date,
    forward_return,
    load_panel,
)

REPORT_DIR = Path(__file__).resolve().parent / "reports"
CSV_PATH = REPORT_DIR / "screening_results.csv"
MD_PATH = REPORT_DIR / "screening_results.md"
HORIZONS = (1, 5)
COST_GRID_BPS = (0, 5, 10, 25)
MIN_NAMES = 25

def strategy_specs() -> list[StrategySpec]:
    return [
        StrategySpec("breakout_20", "breakout_continuation", "20-day close breakout", lambda panel: breakout_score(panel.close, 20)),
        StrategySpec("keltner_breakout_20", "breakout_continuation", "20-day Keltner channel breakout", lambda panel: keltner_score(panel, 20, 10, 2.0)),
        StrategySpec("failed_breakout_score_20", "breakout_continuation", "failed breakout score", lambda panel: failed_breakout_score(panel.high, panel.low, panel.close, panel.volume).score),
        StrategySpec("macd_histogram_12_26_9", "trend_following", "MACD histogram", lambda panel: macd(panel.close).histogram),
        StrategySpec("directional_spread_14", "trend_following", "DMI directional spread", directional_spread),
        StrategySpec("adx_directional_14", "trend_following", "ADX signed by DMI direction", adx_directional_score),
        StrategySpec("vortex_spread_14", "trend_following", "Vortex positive-minus-negative spread", lambda panel: vortex_indicator(panel.high, panel.low, panel.close).spread),
        StrategySpec("multi_timeframe_confirmation", "trend_following", "multi-timeframe confirmation score", lambda panel: multi_timeframe_confirmation(panel.close).score),
        StrategySpec("trix_histogram_15_9", "trend_following", "TRIX histogram", lambda panel: trix(panel.close).histogram),
        StrategySpec("rsi_mean_reversion_14", "reversal_exhaustion", "RSI mean reversion", lambda panel: 50.0 - relative_strength_index(panel.close)),
        StrategySpec("stochastic_mean_reversion_14", "reversal_exhaustion", "stochastic %K mean reversion", lambda panel: 50.0 - stochastic_oscillator(panel.high, panel.low, panel.close).percent_k),
        StrategySpec("williams_r_mean_reversion_14", "reversal_exhaustion", "Williams %R mean reversion", lambda panel: -williams_r(panel.high, panel.low, panel.close).percent_r),
        StrategySpec("cci_mean_reversion_20", "reversal_exhaustion", "CCI mean reversion", lambda panel: -commodity_channel_index(panel.high, panel.low, panel.close)),
        StrategySpec("cmo_mean_reversion_14", "reversal_exhaustion", "Chande momentum mean reversion", lambda panel: -chande_momentum_oscillator(panel.close)),
        StrategySpec("dpo_mean_reversion_20", "reversal_exhaustion", "detrended price oscillator mean reversion", lambda panel: -detrended_price_oscillator(panel.close).dpo),
        StrategySpec("bollinger_percent_b_mean_reversion_20", "reversal_exhaustion", "%B mean reversion", lambda panel: 0.5 - bollinger_percent_b(panel.close)),
        StrategySpec("failed_reversal_score", "reversal_exhaustion", "failed reversal score", lambda panel: failed_reversal_score(panel.open, panel.high, panel.low, panel.close, panel.volume).score),
        StrategySpec("gap_continuation_score", "gap_reaction", "opening gap continuation score", lambda panel: opening_gap_metrics(panel.open, panel.high, panel.low, panel.close).continuation_score),
        StrategySpec("gap_fade_score", "gap_reaction", "opening gap fade score", lambda panel: -opening_gap_metrics(panel.open, panel.high, panel.low, panel.close).continuation_score),
        StrategySpec("support_resistance_position_20", "structure_levels", "support/resistance position", lambda panel: support_resistance_levels(panel.high, panel.low, panel.close).position - 0.5),
        StrategySpec("pivot_relative_position", "structure_levels", "pivot-relative price position", lambda panel: pivot_relative_position(panel)),
        StrategySpec("chaikin_money_flow_20", "volume_confirmation", "Chaikin money flow", lambda panel: chaikin_money_flow(panel.high, panel.low, panel.close, panel.volume).cmf),
        StrategySpec("force_index_13", "volume_confirmation", "force index", lambda panel: force_index(panel.close, panel.volume).smoothed_force_index),
        StrategySpec("price_volume_trend_20", "volume_confirmation", "price-volume trend slope", lambda panel: price_volume_trend(panel.close, panel.volume).pvt.diff(20)),
        StrategySpec("chaikin_oscillator_3_10", "volume_confirmation", "Chaikin oscillator", lambda panel: chaikin_oscillator(panel.high, panel.low, panel.close, panel.volume).oscillator),
        StrategySpec("trend_volume_composite", "volume_confirmation", "trend-volume composite", lambda panel: trend_volume_composite(panel.high, panel.low, panel.close, panel.volume).score),
        StrategySpec("hybrid_confirmation", "volume_confirmation", "hybrid trend-volume confirmation", lambda panel: hybrid_trend_volume_scores(panel.high, panel.low, panel.close, panel.volume).confirmation_score),
        StrategySpec("obv_slope_20", "volume_confirmation", "on-balance-volume slope", lambda panel: on_balance_volume(panel.close, panel.volume).diff(20)),
        StrategySpec("mfi_mean_reversion_14", "volume_confirmation", "money flow index mean reversion", lambda panel: 50.0 - money_flow_index(panel.high, panel.low, panel.close, panel.volume)),
    ]


def breakout_score(close: pd.DataFrame, lookback: int) -> pd.DataFrame:
    return breakout_above(close, lookback).astype(float) - breakout_below(close, lookback).astype(float)


def keltner_score(panel: Alpha101Panel, ema_period: int, atr_period: int, multiplier: float) -> pd.DataFrame:
    channels = keltner_channels(panel.high, panel.low, panel.close, ema_period, atr_period, multiplier)
    return channels.breakout_above.astype(float) - channels.breakout_below.astype(float)


def directional_spread(panel: Alpha101Panel) -> pd.DataFrame:
    dmi = directional_movement_index(panel.high, panel.low, panel.close)
    return dmi.plus_di - dmi.minus_di


def adx_directional_score(panel: Alpha101Panel) -> pd.DataFrame:
    dmi = directional_movement_index(panel.high, panel.low, panel.close)
    return dmi.adx * np.sign(dmi.plus_di - dmi.minus_di)


def pivot_relative_position(panel: Alpha101Panel) -> pd.DataFrame:
    pivot = (panel.high.shift(1) + panel.low.shift(1) + panel.close.shift(1)) / 3.0
    return panel.close.div(pivot.replace(0.0, np.nan)).sub(1.0)


def evaluate_strategy(panel: Alpha101Panel, spec: StrategySpec, horizon: int) -> dict[str, float | int | str]:
    mask = panel.high_vol_mask & panel.active_mask
    future = forward_return(panel.close, horizon)
    signal = spec.builder(panel).reindex_like(panel.close).astype(float)
    valid = mask & signal.notna() & future.notna()
    counts = valid.sum(axis=1)
    rank_pct = signal.where(valid).rank(axis=1, pct=True, method="average")
    long_mask = rank_pct.ge(0.8) & valid
    short_mask = rank_pct.le(0.2) & valid
    long_count = long_mask.sum(axis=1).replace(0, np.nan)
    short_count = short_mask.sum(axis=1).replace(0, np.nan)
    weights = (
        long_mask.astype(float).div(long_count, axis=0).fillna(0.0)
        - short_mask.astype(float).div(short_count, axis=0).fillna(0.0)
    )
    gross = (weights * future.where(valid, 0.0)).sum(axis=1)
    eligible = counts.ge(MIN_NAMES) & long_count.gt(0.0) & short_count.gt(0.0)
    gross = gross.where(eligible)
    turnover = (weights.diff().abs().sum(axis=1) * 0.5).fillna(0.0).where(eligible)
    rank_ic = fast_rank_ic_by_date(signal.where(valid), future.where(valid), min_names=MIN_NAMES)
    equity = (1.0 + gross.fillna(0.0)).cumprod()
    gross_std = float(gross.std(ddof=0))
    sharpe_like = float(gross.mean() / gross_std * np.sqrt(252.0)) if gross_std > 0.0 else float("nan")
    return {
        "universe": f"{panel.name}_high_vol_top100",
        "horizon": horizon,
        "family": spec.family,
        "strategy": spec.name,
        "description": spec.description,
        "trade_days": int(gross.notna().sum()),
        "coverage_pct": float(valid.sum().sum() / mask.sum().sum()),
        "avg_names": float(counts.where(eligible).mean()),
        "gross_mean_bps": float(gross.mean() * 10_000.0),
        "gross_median_bps": float(gross.median() * 10_000.0),
        "gross_win_rate": float((gross > 0.0).mean()),
        "turnover": float(turnover.mean()),
        "gross_sharpe_like": sharpe_like,
        "gross_max_drawdown_pct": float((equity / equity.cummax() - 1.0).min() * 100.0),
        "rank_ic_mean": float(rank_ic.mean()),
        "rank_ic_median": float(rank_ic.median()),
        "rank_ic_tstat": t_stat(rank_ic),
        "rank_ic_positive_rate": float((rank_ic > 0.0).mean()),
        "net_mean_bps_0": net_mean_bps(gross, turnover, 0),
        "net_mean_bps_5": net_mean_bps(gross, turnover, 5),
        "net_mean_bps_10": net_mean_bps(gross, turnover, 10),
        "net_mean_bps_25": net_mean_bps(gross, turnover, 25),
    }


def net_mean_bps(gross: pd.Series, turnover: pd.Series, cost_bps: int) -> float:
    cost = gross - turnover * (2.0 * cost_bps / 10_000.0)
    return float(cost.mean() * 10_000.0)


def t_stat(series: pd.Series) -> float:
    values = series.dropna()
    std = float(values.std(ddof=0))
    if values.empty or std == 0.0:
        return float("nan")
    return float(values.mean() / std * np.sqrt(len(values)))


def build_results() -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for universe in ("nifty500", "expanded"):
        panel = load_panel(universe)
        for horizon in HORIZONS:
            for spec in strategy_specs():
                print(f"screening {universe} horizon={horizon} strategy={spec.name}", flush=True)
                row = evaluate_strategy(panel, spec, horizon)
                rows.append(row)
    return pd.DataFrame(rows)


def family_summary(results: pd.DataFrame) -> pd.DataFrame:
    summary = results.groupby("family", as_index=False).agg(
        strategies=("strategy", "nunique"),
        mean_rank_ic=("rank_ic_mean", "mean"),
        mean_gross_bps=("gross_mean_bps", "mean"),
        mean_net_10_bps=("net_mean_bps_10", "mean"),
        positive_net_10_rate=("net_mean_bps_10", lambda s: float((s > 0.0).mean())),
        positive_ic_rate=("rank_ic_mean", lambda s: float((s > 0.0).mean())),
    )
    return summary.sort_values("mean_net_10_bps", ascending=False)


def stable_strategies(results: pd.DataFrame, positive: bool) -> pd.DataFrame:
    grouped = results.groupby("strategy", as_index=False).agg(
        family=("family", "first"),
        universes=("universe", "nunique"),
        horizons=("horizon", "nunique"),
        mean_rank_ic=("rank_ic_mean", "mean"),
        mean_net_10_bps=("net_mean_bps_10", "mean"),
        min_net_10_bps=("net_mean_bps_10", "min"),
        max_net_10_bps=("net_mean_bps_10", "max"),
    )
    if positive:
        mask = grouped["mean_rank_ic"].gt(0.0) & grouped["min_net_10_bps"].gt(0.0)
        return grouped.loc[mask].sort_values("mean_net_10_bps", ascending=False)
    mask = grouped["mean_rank_ic"].lt(0.0) & grouped["max_net_10_bps"].lt(0.0)
    return grouped.loc[mask].sort_values("mean_net_10_bps")


def panel_leaderboard(results: pd.DataFrame, universe: str, horizon: int, ascending: bool = False) -> pd.DataFrame:
    subset = results[(results["universe"].eq(universe)) & (results["horizon"].eq(horizon))]
    cols = [
        "family",
        "strategy",
        "rank_ic_mean",
        "gross_mean_bps",
        "net_mean_bps_10",
        "turnover",
        "gross_win_rate",
    ]
    return subset.sort_values("net_mean_bps_10", ascending=ascending)[cols].head(5)


def markdown_table(frame: pd.DataFrame, float_digits: int = 3) -> str:
    if frame.empty:
        return "_No rows._"
    formatted = frame.copy()
    for column in formatted.columns:
        formatted[column] = formatted[column].map(lambda value: format_value(value, float_digits))
    header = "| " + " | ".join(formatted.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(formatted.columns)) + " |"
    rows = ["| " + " | ".join(map(str, row)) + " |" for row in formatted.to_numpy()]
    return "\n".join([header, divider, *rows])


def format_value(value: object, float_digits: int) -> str:
    if isinstance(value, float):
        if np.isnan(value):
            return "nan"
        return f"{value:.{float_digits}f}"
    return str(value)


def build_report(results: pd.DataFrame) -> str:
    lines = [
        "# Price Action Screening Results",
        "",
        "## Protocol",
        "",
        "- Universe: `nifty500_high_vol_top100` and `expanded_high_vol_top100`.",
        "- Horizon: `1d` and `5d` forward returns.",
        "- Primary mask: repo-native `high_vol_mask` intersected with `active_mask`.",
        "- Long-short construction: top and bottom quintiles of each signal cross-section.",
        "- Cost stress: `0`, `5`, `10`, and `25` bps with turnover-based deductions.",
        "- Non-directional overlays, intraday-only helpers, and loop-heavy profile tools are listed separately and not forced into this pass.",
        "",
        "## Family Summary",
        "",
        markdown_table(family_summary(results).round(4)),
        "",
        "## Stable Winners",
        "",
        markdown_table(stable_strategies(results, positive=True).round(4)),
        "",
        "## Stable Losers",
        "",
        markdown_table(stable_strategies(results, positive=False).round(4)),
        "",
    ]
    for universe in ("nifty500_high_vol_top100", "expanded_high_vol_top100"):
        for horizon in HORIZONS:
            lines.extend([
                f"## {universe} / {horizon}d",
                "",
                "Top 5 by `net_mean_bps_10`:",
                "",
                markdown_table(panel_leaderboard(results, universe, horizon).round(4)),
                "",
                "Bottom 5 by `net_mean_bps_10`:",
                "",
                markdown_table(panel_leaderboard(results, universe, horizon, ascending=True).round(4)),
                "",
            ])
    lines.extend([
        "## Not Screened In This Pass",
        "",
        "- `opening_range_breakout`: session-dependent intraday data is not present in the daily panel.",
        "- `volume_profile_levels`, `support_resistance_trendlines`: structure/profile helpers that need a separate pass.",
        "- `supertrend`, `parabolic_sar`: directional helpers that are too slow for the pooled screen pass here.",
        "- `atr_position_size`, `pyramiding_ladder`: sizing overlays, not standalone directional strategies.",
        "- `bollinger_squeeze`, `choppiness_index`, `mass_index`, `volume_profile_regime`: gate-only helpers rather than standalone directional scores.",
        "",
    ])
    return "\n".join(lines)


def write_outputs(results: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    results.sort_values(["universe", "horizon", "family", "strategy"]).to_csv(CSV_PATH, index=False)
    MD_PATH.write_text(build_report(results), encoding="utf-8")


def main() -> int:
    results = build_results()
    write_outputs(results)
    print(f"Wrote {MD_PATH}")
    print(f"Wrote {CSV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
