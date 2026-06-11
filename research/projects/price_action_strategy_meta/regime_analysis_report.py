from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from project.alpha_math.gap_regimes import opening_gap_metrics
from project.alpha_math.market_breadth import market_breadth_metrics
from research.notebooks.alpha_001.research.alpha101_engine import (
    Alpha101Panel,
    fast_rank_ic_by_date,
    forward_return,
    load_panel,
)
from research.projects.price_action_strategy_meta.regime_analysis_strategies import (
    extra_strategy_specs,
)
from research.projects.price_action_strategy_meta.regime_panel_utils import (
    subset_high_vol_panel,
)
from research.projects.price_action_strategy_meta.screening_report import (
    markdown_table as render_table,
    strategy_specs,
)
from research.projects.price_action_strategy_meta.strategy_spec import StrategySpec

REPORT_DIR = Path(__file__).resolve().parent / "reports"
STRATEGY_CSV = REPORT_DIR / "regime_strategy_summary.csv"
SECTOR_CSV = REPORT_DIR / "regime_sector_summary.csv"
LIQUIDITY_CSV = REPORT_DIR / "regime_liquidity_summary.csv"
CORR_CSV = REPORT_DIR / "regime_correlations.csv"
MD_PATH = REPORT_DIR / "regime_analysis.md"
HORIZONS = (1, 5)
MIN_NAMES = 25
TARGET_COST_BPS = 10
CORE_STRATEGY_NAMES = (
    "breakout_20",
    "keltner_breakout_20",
    "failed_breakout_score_20",
    "macd_histogram_12_26_9",
    "vortex_spread_14",
    "trix_histogram_15_9",
    "stochastic_mean_reversion_14",
    "williams_r_mean_reversion_14",
    "bollinger_percent_b_mean_reversion_20",
    "failed_reversal_score",
    "gap_continuation_score",
    "gap_fade_score",
    "pivot_relative_position",
    "chaikin_money_flow_20",
    "force_index_13",
    "price_volume_trend_20",
    "trend_volume_composite",
    "mfi_mean_reversion_14",
)


def base_strategy_specs() -> list[StrategySpec]:
    selected = set(CORE_STRATEGY_NAMES)
    lookup = {spec.name: spec for spec in strategy_specs()}
    missing = sorted(selected - lookup.keys())
    if missing:
        raise ValueError(f"Missing strategies: {', '.join(missing)}")
    return [lookup[name] for name in CORE_STRATEGY_NAMES]


def all_strategy_specs() -> list[StrategySpec]:
    return base_strategy_specs() + extra_strategy_specs()


def benchmark_close(panel: Alpha101Panel) -> pd.Series:
    benchmark_returns = panel.close.pct_change(fill_method=None).mean(axis=1)
    return (1.0 + benchmark_returns.fillna(0.0)).cumprod().mul(100.0)


def quantile_bucket(series: pd.Series, labels: tuple[str, str, str]) -> pd.Series:
    return rolling_quantile_bucket(series, labels)


def rolling_quantile_bucket(
    series: pd.Series,
    labels: tuple[str, str, str],
    lookback: int = 504,
    min_periods: int = 126,
) -> pd.Series:
    history = series.shift(1)
    low = history.rolling(lookback, min_periods=min_periods).quantile(1.0 / 3.0)
    high = history.rolling(lookback, min_periods=min_periods).quantile(2.0 / 3.0)
    out = pd.Series(labels[1], index=series.index, dtype="object")
    valid = series.notna() & low.notna() & high.notna()
    out[~valid] = "unknown"
    out[valid & series.le(low)] = labels[0]
    out[valid & series.ge(high)] = labels[2]
    return out


def rolling_upper_quantile(
    series: pd.Series,
    quantile: float = 0.75,
    lookback: int = 504,
    min_periods: int = 126,
) -> pd.Series:
    return series.shift(1).rolling(lookback, min_periods=min_periods).quantile(quantile)


def regime_frame(panel: Alpha101Panel) -> pd.DataFrame:
    bench = benchmark_close(panel)
    bench_ret = bench.pct_change(fill_method=None)
    drawdown = bench.div(bench.cummax()).sub(1.0)
    vol20 = bench_ret.rolling(20, min_periods=20).std().mul(np.sqrt(252.0))
    ma50 = bench.rolling(50, min_periods=50).mean()
    ma200 = bench.rolling(200, min_periods=200).mean()
    breadth = market_breadth_metrics(panel.close).breadth_score
    gap = opening_gap_metrics(panel.open, panel.high, panel.low, panel.close)
    gap_atr = gap.gap_atr.mean(axis=1)
    gap_dir = gap.gap.mean(axis=1)
    dollar_volume = panel.close.mul(panel.volume).mean(axis=1)
    vol_state = rolling_quantile_bucket(vol20, ("low_vol", "normal_vol", "high_vol"))
    breadth_state = pd.Series("neutral", index=bench.index, dtype="object")
    breadth_state[breadth.ge(0.25)] = "bullish"
    breadth_state[breadth.le(-0.25)] = "bearish"
    trend_state = pd.Series("sideways", index=bench.index, dtype="object")
    bull = bench.gt(ma50) & ma50.gt(ma200) & bench_ret.rolling(20, min_periods=20).mean().gt(0.0)
    bear = bench.lt(ma50) & ma50.lt(ma200) & bench_ret.rolling(20, min_periods=20).mean().lt(0.0)
    trend_state[bull] = "bull"
    trend_state[bear] = "bear"
    gap_state = pd.Series("unknown", index=bench.index, dtype="object")
    gap_threshold = rolling_upper_quantile(gap_atr)
    gap_valid = gap_atr.notna() & gap_threshold.notna()
    gap_state[gap_valid] = "calm"
    shock = gap_valid & gap_atr.ge(gap_threshold)
    gap_state[shock & gap_dir.gt(0.0)] = "up_gap_shock"
    gap_state[shock & gap_dir.lt(0.0)] = "down_gap_shock"
    liquidity_state = rolling_quantile_bucket(
        np.log(dollar_volume.replace(0.0, np.nan)),
        ("low_liquidity", "normal_liquidity", "high_liquidity"),
    )
    drawdown_state = rolling_quantile_bucket(
        drawdown,
        ("deep_drawdown", "normal_drawdown", "shallow_drawdown"),
    )
    risk_state = pd.Series("mixed", index=bench.index, dtype="object")
    risk_on = trend_state.eq("bull") & vol_state.ne("high_vol") & breadth_state.eq("bullish")
    risk_off = trend_state.eq("bear") & vol_state.eq("high_vol") & breadth_state.eq("bearish")
    risk_state[risk_on] = "risk_on"
    risk_state[risk_off] = "risk_off"
    frame = pd.DataFrame(
        {
            "bench_close": bench,
            "vol_score": vol20.rank(pct=True),
            "trend_score": bench.div(ma200).sub(1.0),
            "breadth_score": breadth,
            "gap_score": gap_atr.mul(np.sign(gap_dir)),
            "liquidity_score": np.log(dollar_volume.replace(0.0, np.nan)),
            "drawdown_score": drawdown,
            "vol_state": vol_state,
            "trend_state": trend_state,
            "breadth_state": breadth_state,
            "gap_state": gap_state,
            "liquidity_state": liquidity_state,
            "drawdown_state": drawdown_state,
            "risk_state": risk_state,
        }
    )
    return frame.fillna({
        "vol_state": "unknown",
        "trend_state": "unknown",
        "breadth_state": "unknown",
        "gap_state": "unknown",
        "liquidity_state": "unknown",
        "drawdown_state": "unknown",
        "risk_state": "unknown",
    })


def strategy_daily_frame(
    panel: Alpha101Panel,
    spec: StrategySpec,
    horizon: int,
    compute_rank_ic: bool = True,
    future: pd.DataFrame | None = None,
    base_mask: pd.DataFrame | None = None,
) -> pd.DataFrame:
    mask = base_mask if base_mask is not None else panel.high_vol_mask & panel.active_mask
    future = future if future is not None else forward_return(panel.close, horizon)
    signal = spec.builder(panel).reindex_like(panel.close).astype(float)
    valid = mask & signal.notna() & future.notna()
    counts = valid.sum(axis=1)
    rank_pct = signal.where(valid).rank(axis=1, pct=True, method="average")
    long_mask = rank_pct.ge(0.8) & valid
    short_mask = rank_pct.le(0.2) & valid
    long_count = long_mask.sum(axis=1).replace(0, np.nan)
    short_count = short_mask.sum(axis=1).replace(0, np.nan)
    weights = long_mask.astype(float).div(long_count, axis=0).fillna(0.0) - short_mask.astype(float).div(short_count, axis=0).fillna(0.0)
    gross = (weights * future.where(valid, 0.0)).sum(axis=1)
    turnover = (weights.diff().abs().sum(axis=1) * 0.5).fillna(0.0)
    eligible = counts.ge(MIN_NAMES) & long_count.gt(0.0) & short_count.gt(0.0)
    gross = gross.where(eligible)
    turnover = turnover.where(eligible)
    net = gross - turnover * (2.0 * TARGET_COST_BPS / 10_000.0)
    rank_ic = (
        fast_rank_ic_by_date(signal.where(valid), future.where(valid), min_names=MIN_NAMES)
        if compute_rank_ic
        else pd.Series(np.nan, index=panel.close.index)
    )
    return pd.DataFrame(
        {
            "gross_return": gross,
            "net_return": net,
            "turnover": turnover,
            "rank_ic": rank_ic,
        }
    )


def sector_members(panel: Alpha101Panel) -> dict[str, list[str]]:
    mapping = panel.industry.astype(str)
    sectors = {}
    for sector in sorted(mapping.unique()):
        cols = mapping.index[mapping.eq(sector)].tolist()
        if len(cols) >= 5:
            sectors[sector] = cols
    return sectors


def liquidity_classes(panel: Alpha101Panel) -> dict[str, list[str]]:
    adv20 = panel.close.mul(panel.volume).rolling(20, min_periods=20).median().median(axis=0)
    bands = pd.qcut(
        adv20.rank(method="first", pct=True),
        5,
        labels=["very_low", "low", "mid", "high", "very_high"],
        duplicates="drop",
    )
    out: dict[str, list[str]] = {}
    for label in bands.astype(str).unique():
        cols = bands.index[bands.astype(str).eq(label)].tolist()
        if len(cols) >= 5:
            out[label] = cols
    return out


def daily_group_summary(values: pd.Series, state: pd.Series, min_obs: int = 20) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for key, chunk in values.groupby(state):
        clean = chunk.dropna()
        if len(clean) < min_obs:
            continue
        std = float(clean.std(ddof=0))
        rows.append(
            {
                "regime_state": str(key),
                "obs": int(len(clean)),
                "mean_net_bps": float(clean.mean() * 10_000.0),
                "median_net_bps": float(clean.median() * 10_000.0),
                "win_rate": float(clean.gt(0.0).mean()),
                "tstat": float(clean.mean() / std * np.sqrt(len(clean))) if std > 0.0 else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def strategy_regime_rows(panel: Alpha101Panel, regime: pd.DataFrame, universe: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    base_mask = panel.high_vol_mask & panel.active_mask
    for horizon in HORIZONS:
        future = forward_return(panel.close, horizon)
        for spec in all_strategy_specs():
            daily = strategy_daily_frame(
                panel,
                spec,
                horizon,
                compute_rank_ic=False,
                future=future,
                base_mask=base_mask,
            ).join(regime, how="left")
            for dimension in ("vol_state", "trend_state", "breadth_state", "gap_state", "liquidity_state", "risk_state"):
                summary = daily_group_summary(daily["net_return"], daily[dimension])
                if summary.empty:
                    continue
                for row in summary.to_dict(orient="records"):
                    row.update(
                        {
                            "universe": universe,
                            "horizon": horizon,
                            "family": spec.family,
                            "strategy": spec.name,
                            "regime_dimension": dimension,
                        }
                    )
                    rows.append(row)
    return rows


def correlation_rows(panel: Alpha101Panel, regime: pd.DataFrame, universe: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for horizon in HORIZONS:
        for spec in all_strategy_specs():
            daily = strategy_daily_frame(
                panel, spec, horizon, compute_rank_ic=False
            ).join(regime, how="left")
            factors = daily[["net_return", "vol_score", "trend_score", "breadth_score", "gap_score", "liquidity_score"]].dropna()
            if len(factors) < 20:
                continue
            row = {
                "universe": universe,
                "horizon": horizon,
                "family": spec.family,
                "strategy": spec.name,
            }
            for col in ("vol_score", "trend_score", "breadth_score", "gap_score", "liquidity_score"):
                row[f"corr_{col}"] = float(factors["net_return"].corr(factors[col]))
            rows.append(row)
    return rows


def class_rows(panel: Alpha101Panel, classes: dict[str, list[str]], class_type: str, regime: pd.DataFrame, universe: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for horizon in HORIZONS:
        future = forward_return(panel.close, horizon)
        for class_name, cols in classes.items():
            class_return = future[cols].where(panel.high_vol_mask[cols] & panel.active_mask[cols] & future[cols].notna()).mean(axis=1)
            joined = pd.DataFrame({"net_return": class_return}).join(regime, how="left")
            for dimension in ("vol_state", "trend_state", "breadth_state", "gap_state", "liquidity_state", "risk_state"):
                summary = daily_group_summary(joined["net_return"], joined[dimension])
                if summary.empty:
                    continue
                for row in summary.to_dict(orient="records"):
                    row.update(
                        {
                            "universe": universe,
                            "horizon": horizon,
                            class_type: class_name,
                            "regime_dimension": dimension,
                        }
                    )
                    rows.append(row)
    return rows


def aggregate_family_rows(rows: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    grouped = frame.groupby(["family", "strategy", "regime_dimension", "regime_state"], as_index=False).agg(
        mean_net_bps=("mean_net_bps", "mean"),
        median_net_bps=("median_net_bps", "mean"),
        win_rate=("win_rate", "mean"),
        tstat=("tstat", "mean"),
        obs=("obs", "sum"),
        universes=("universe", "nunique"),
        horizons=("horizon", "nunique"),
    )
    return grouped.sort_values("mean_net_bps", ascending=False)


def write_outputs(strategy_rows: list[dict[str, object]], sector_rows: list[dict[str, object]], liquidity_rows: list[dict[str, object]], corr_rows: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(strategy_rows).to_csv(STRATEGY_CSV, index=False)
    pd.DataFrame(sector_rows).to_csv(SECTOR_CSV, index=False)
    pd.DataFrame(liquidity_rows).to_csv(LIQUIDITY_CSV, index=False)
    pd.DataFrame(corr_rows).to_csv(CORR_CSV, index=False)


def build_report(strategy_rows: list[dict[str, object]], sector_rows: list[dict[str, object]], liquidity_rows: list[dict[str, object]], corr_rows: list[dict[str, object]]) -> str:
    strategies = pd.DataFrame(strategy_rows)
    sectors = pd.DataFrame(sector_rows)
    liquidity = pd.DataFrame(liquidity_rows)
    corr = pd.DataFrame(corr_rows)
    family = aggregate_family_rows(strategy_rows)
    family_gate = family[family["universes"].ge(2) & family["horizons"].ge(2)] if not family.empty else family
    corr_top = corr.assign(abs_gap_corr=corr["corr_gap_score"].abs()).sort_values("abs_gap_corr", ascending=False).head(10) if not corr.empty else corr
    sector_focus = sectors[sectors["horizon"].eq(5)] if not sectors.empty else sectors
    liquidity_focus = liquidity[liquidity["horizon"].eq(5)] if not liquidity.empty else liquidity
    lines = [
        "# Regime Analysis",
        "",
        "## Protocol",
        "",
        "- Strategy pool: a curated subset of fast, representative base-screen strategies plus breakout, trend, reversal, gap, structure, and participation extras.",
        "- Each universe is reduced to its top 100 high-vol names before the regime scan so the panel matches the first-pass screen and stays tractable.",
        "- Regime axes: volatility, trend, breadth, gap shock, liquidity, and combined risk state.",
        "- Volatility, gap, liquidity, and drawdown buckets are built from trailing windows only; no full-sample quantiles remain in the regime labels.",
        "- News effects are proxied by gap shocks because no local headline feed exists in the repository.",
        "- Cost stress uses `10bps` net returns for the regime summaries.",
        "",
        "## Strategy Correlations",
        "",
        render_table(corr_top.drop(columns=["abs_gap_corr"], errors="ignore")),
        "",
        "## High-Confidence Gate Candidates",
        "",
        render_table(family_gate.head(20)),
        "",
        "## Market State Highlights",
        "",
    ]
    market = strategies[strategies["regime_dimension"].eq("trend_state") & strategies["horizon"].eq(5)] if not strategies.empty else strategies
    if not market.empty:
        market = market.sort_values("mean_net_bps", ascending=False).groupby(["family", "strategy"], as_index=False).head(1)
        lines.extend([
            "Top family/state pairs on 5-day horizon:",
            "",
            render_table(market.head(20)[["family", "strategy", "regime_state", "mean_net_bps", "win_rate", "obs"]]),
            "",
        ])
    lines.extend([
        "## Sectors",
        "",
        render_table(sector_focus.sort_values("mean_net_bps", ascending=False).head(10)),
        "",
        "## Liquidity Classes",
        "",
        render_table(liquidity_focus.sort_values("mean_net_bps", ascending=False).head(10)),
        "",
        "## Takeaway",
        "",
        "- The report is designed to surface where signals align with the market state, not to promote every positive pocket as deployable.",
        "- The next step is a walk-forward selector that only activates the historically consistent regime-state combinations.",
    ])
    return "\n".join(lines)


def main() -> int:
    strategy_rows: list[dict[str, object]] = []
    sector_rows: list[dict[str, object]] = []
    liquidity_rows: list[dict[str, object]] = []
    corr_rows: list[dict[str, object]] = []
    for universe in ("nifty500", "expanded"):
        print(f"regime {universe}: loading high-vol subset", flush=True)
        panel = subset_high_vol_panel(load_panel(universe))
        regime = regime_frame(panel)
        print(f"regime {universe}: strategy rows", flush=True)
        strategy_rows.extend(strategy_regime_rows(panel, regime, universe))
        print(f"regime {universe}: sector rows", flush=True)
        sector_rows.extend(class_rows(panel, sector_members(panel), "sector", regime, universe))
        print(f"regime {universe}: liquidity rows", flush=True)
        liquidity_rows.extend(class_rows(panel, liquidity_classes(panel), "liquidity_class", regime, universe))
        print(f"regime {universe}: correlation rows", flush=True)
        corr_rows.extend(correlation_rows(panel, regime, universe))
    write_outputs(strategy_rows, sector_rows, liquidity_rows, corr_rows)
    MD_PATH.write_text(build_report(strategy_rows, sector_rows, liquidity_rows, corr_rows), encoding="utf-8")
    print(f"Wrote {MD_PATH}")
    print(f"Wrote {STRATEGY_CSV}")
    print(f"Wrote {SECTOR_CSV}")
    print(f"Wrote {LIQUIDITY_CSV}")
    print(f"Wrote {CORR_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
