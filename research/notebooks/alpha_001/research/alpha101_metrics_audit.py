from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path
import sys
from typing import cast

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if __package__:
    from .alpha101_engine import (  # type: ignore[import-not-found]  # noqa: E402
        ANNUALIZATION,
        Alpha101Panel,
        backtest_weights,
        causal_orient,
        forward_return,
        load_panel,
        next_session_return,
        performance_metrics,
    )
    from .alpha101_factory import (  # type: ignore[import-not-found]  # noqa: E402
        PRIMARY_HORIZON,
        advanced_transform_signal,
        build_portfolio_weights,
        panel_masks,
    )
    from . import alpha101_formulas as formula_module  # type: ignore[import-not-found]  # noqa: E402
else:  # pragma: no cover
    from alpha101_engine import (  # type: ignore[import-not-found]  # noqa: E402
        ANNUALIZATION,
        Alpha101Panel,
        backtest_weights,
        causal_orient,
        forward_return,
        load_panel,
        next_session_return,
        performance_metrics,
    )
    from alpha101_factory import (  # type: ignore[import-not-found]  # noqa: E402
        PRIMARY_HORIZON,
        advanced_transform_signal,
        build_portfolio_weights,
        panel_masks,
    )
    import alpha101_formulas as formula_module  # type: ignore[import-not-found]  # noqa: E402
from project.data.db import DuckDBAccess  # noqa: E402
from project.data.repository import DataRepository  # noqa: E402

DEFAULT_BENCHMARK_PATH = REPO_ROOT / "project_mft.duckdb"
BENCHMARK_SYMBOL = "NIFTY"
ROLLING_WINDOWS = (21, 63, 252)
POSITION_EPSILON = 1e-12
AUDIT_LOOKBACK_DAYS = 252


def load_benchmark_returns(path: Path = DEFAULT_BENCHMARK_PATH) -> pd.Series:
    if not path.exists():
        raise FileNotFoundError(f"Missing cached NIFTY benchmark series at {path}")
    if path.suffix == ".duckdb":
        return _load_benchmark_returns_from_repository(path)
    frame = pd.read_csv(path)
    if "timestamp" in frame.columns:
        timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    else:
        timestamps = pd.to_datetime(frame.index, utc=True, errors="coerce")
    index = _benchmark_date_index(timestamps)
    price_col = "adj_close" if "adj_close" in frame.columns else "close"
    if price_col not in frame.columns:
        raise ValueError(f"Benchmark file {path} is missing a close column")
    prices = pd.to_numeric(frame[price_col], errors="coerce")
    series = pd.Series(prices.to_numpy(dtype=float), index=index, name="nifty50_close")
    series = series.dropna().sort_index()
    return series.pct_change(fill_method=None).dropna().rename("nifty50")


def rolling_return_metrics(returns: pd.Series, windows: tuple[int, ...] = ROLLING_WINDOWS) -> pd.DataFrame:
    series = returns.astype(float).sort_index()
    frame = pd.DataFrame(index=series.index)
    for window in windows:
        rolling = series.rolling(window, min_periods=window)
        vol = rolling.std(ddof=0) * math.sqrt(ANNUALIZATION)
        sharpe = rolling.mean().div(rolling.std(ddof=0).replace(0.0, np.nan)) * math.sqrt(ANNUALIZATION)
        frame[f"rolling_vol_{window}"] = vol
        frame[f"rolling_sharpe_{window}"] = sharpe
    return frame


def rolling_relative_metrics(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    windows: tuple[int, ...] = ROLLING_WINDOWS,
) -> pd.DataFrame:
    pair = pd.concat(
        [strategy_returns.rename("strategy"), benchmark_returns.rename("benchmark")],
        axis=1,
    ).dropna()
    frame = pd.DataFrame(index=pair.index)
    for window in windows:
        strategy_roll = pair["strategy"].rolling(window, min_periods=window)
        benchmark_roll = pair["benchmark"].rolling(window, min_periods=window)
        corr = strategy_roll.corr(pair["benchmark"])
        beta = strategy_roll.cov(pair["benchmark"], ddof=0).div(benchmark_roll.var(ddof=0).replace(0.0, np.nan))
        frame[f"rolling_corr_{window}"] = corr
        frame[f"rolling_beta_{window}"] = beta
    return frame


def average_holding_period(weights: pd.DataFrame) -> float:
    positions = _position_state_frame(weights)
    runs: list[int] = []
    for column in positions.columns:
        runs.extend(_non_zero_run_lengths(positions[column]))
    return float(np.mean(runs)) if runs else float("nan")


def trade_count(weights: pd.DataFrame) -> int:
    positions = _position_state_frame(weights)
    if positions.empty:
        return 0
    changes = positions.diff().fillna(positions.iloc[0]).ne(0.0)
    return int(changes.to_numpy(dtype=bool).sum())


def build_selection_audit(selection: pd.Series, benchmark_returns: pd.Series, cost_bps: float = 20.0) -> dict[str, object]:
    panel, raw = _candidate_raw_windowed(str(selection["panel"]), str(selection["alpha_id"]), benchmark_returns)
    mask_name = _selection_choice(selection, "selected_mask", "best_mask")
    transform = _selection_choice(selection, "selected_signal_transform", "best_signal_transform")
    strategy = _selection_choice(selection, "selected_strategy", "best_strategy")
    masks = panel_masks(panel)
    if mask_name not in masks:
        raise ValueError(f"Unknown mask {mask_name!r} for {selection['panel']} {selection['alpha_id']}")
    mask = masks[mask_name] & panel.active_mask
    future = forward_return(panel.close, PRIMARY_HORIZON)
    signal = advanced_transform_signal(raw, transform, mask, panel)
    oriented, _direction = causal_orient(signal, future, PRIMARY_HORIZON)
    weights = build_portfolio_weights(oriented.where(mask), mask, strategy)
    backtest = backtest_weights(weights, next_session_return(panel.close), cost_bps)
    strategy_returns = backtest["returns"].rename("strategy")
    paired = pd.concat(
        [strategy_returns.rename("strategy"), benchmark_returns.rename("benchmark")],
        axis=1,
    ).dropna()
    benchmark_aligned = paired["benchmark"].rename("nifty50")
    active_returns = (paired["strategy"] - paired["benchmark"]).rename("active")
    strategy_metrics = performance_metrics(strategy_returns, backtest["turnover"])
    benchmark_metrics = performance_metrics(benchmark_aligned)
    active_metrics = performance_metrics(active_returns)
    rolling_strategy = rolling_return_metrics(strategy_returns)
    rolling_relative = rolling_relative_metrics(paired["strategy"], paired["benchmark"])
    summary = dict(selection)
    summary.update(
        {
            "strategy_cagr": strategy_metrics["cagr"],
            "strategy_sharpe": strategy_metrics["sharpe"],
            "strategy_sortino": strategy_metrics["sortino"],
            "strategy_max_drawdown": strategy_metrics["max_drawdown"],
            "strategy_hit_rate": strategy_metrics["hit_rate"],
            "strategy_avg_daily_turnover": strategy_metrics["avg_daily_turnover"],
            "benchmark_cagr": benchmark_metrics["cagr"],
            "benchmark_sharpe": benchmark_metrics["sharpe"],
            "benchmark_sortino": benchmark_metrics["sortino"],
            "benchmark_max_drawdown": benchmark_metrics["max_drawdown"],
            "benchmark_hit_rate": benchmark_metrics["hit_rate"],
            "active_cagr": active_metrics["cagr"],
            "active_sharpe": active_metrics["sharpe"],
            "active_sortino": active_metrics["sortino"],
            "active_max_drawdown": active_metrics["max_drawdown"],
            "information_ratio": active_metrics["sharpe"],
            "beta_to_nifty50": _beta_to_benchmark(paired["strategy"], paired["benchmark"]),
            "correlation_to_nifty50": paired["strategy"].corr(paired["benchmark"]),
            "average_holding_period": average_holding_period(weights),
            "trade_count": trade_count(weights),
            "strategy_observations": strategy_metrics["observations"],
            "benchmark_observations": benchmark_metrics["observations"],
            "overlap_observations": int(len(paired)),
            "overlap_start": paired.index.min() if not paired.empty else pd.NaT,
            "overlap_end": paired.index.max() if not paired.empty else pd.NaT,
        }
    )
    summary.update(_latest_rolling_values(rolling_strategy))
    summary.update(_latest_rolling_values(rolling_relative))
    return {
        "summary": summary,
        "weights": weights,
        "strategy_returns": strategy_returns,
        "benchmark_returns": benchmark_aligned,
        "active_returns": active_returns,
        "rolling_strategy": rolling_strategy,
        "rolling_relative": rolling_relative,
    }


def audit_selection_frame(
    selection_frame: pd.DataFrame,
    benchmark_returns: pd.Series,
    cost_bps: float = 20.0,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, selection in selection_frame.iterrows():
        summary = cast(dict[str, object], build_selection_audit(selection, benchmark_returns, cost_bps)["summary"])
        rows.append(summary)
    return pd.DataFrame(rows)


def _load_benchmark_returns_from_repository(path: Path) -> pd.Series:
    repository = DataRepository(DuckDBAccess(path, read_only=True))
    try:
        rows = repository.get_market_data(BENCHMARK_SYMBOL, None, None)
    finally:
        repository.close()
    if not rows:
        raise ValueError(f"Cached benchmark {BENCHMARK_SYMBOL} has no rows in {path}")
    frame = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    index = _benchmark_date_index(timestamps)
    prices = pd.to_numeric(frame["close"], errors="coerce")
    series = pd.Series(prices.to_numpy(dtype=float), index=index, name="nifty50_close")
    series = series.dropna().sort_index()
    return series.pct_change(fill_method=None).dropna().rename("nifty50")


def _benchmark_date_index(timestamps: pd.Series | pd.DatetimeIndex) -> pd.DatetimeIndex:
    parsed = pd.DatetimeIndex(timestamps)
    if parsed.tz is None:
        parsed = parsed.tz_localize("UTC")
    local_dates = parsed.tz_convert("Asia/Kolkata").tz_localize(None)
    return local_dates.normalize()


def _selection_choice(selection: pd.Series, primary: str, fallback: str) -> str:
    for key in (primary, fallback):
        value = selection.get(key)
        if pd.notna(value):
            text = str(value).strip()
            if text and text.lower() != "nan":
                return text
    raise ValueError(f"Selection row is missing {primary!r} and {fallback!r}")


def _position_state_frame(weights: pd.DataFrame) -> pd.DataFrame:
    clipped = weights.fillna(0.0).where(weights.abs().ge(POSITION_EPSILON), 0.0)
    return clipped.apply(np.sign)


def _candidate_raw_windowed(
    panel_name: str,
    alpha_id: str,
    benchmark_returns: pd.Series,
    vwap_variant: str = "hlc3",
    neutralization: str = "snapshot",
) -> tuple[Alpha101Panel, pd.DataFrame]:
    panel = _load_windowed_panel(panel_name, benchmark_returns, vwap_variant)
    if neutralization == "identity":
        old = formula_module.indneutralize
        formula_module.indneutralize = lambda frame, groups: frame
        try:
            raw = formula_module.compute_alpha(panel, alpha_id)
        finally:
            formula_module.indneutralize = old
    elif neutralization == "snapshot":
        raw = formula_module.compute_alpha(panel, alpha_id)
    else:
        raise ValueError(f"Unknown neutralization mode: {neutralization}")
    cleaned = raw.reindex_like(panel.close).where(panel.active_mask)
    return panel, cleaned


def _load_windowed_panel(panel_name: str, benchmark_returns: pd.Series, vwap_variant: str) -> Alpha101Panel:
    panel = load_panel(panel_name)
    window_start = benchmark_returns.index.min() - pd.tseries.offsets.BDay(AUDIT_LOOKBACK_DAYS)
    window_end = benchmark_returns.index.max()
    panel = _slice_panel(panel, window_start, window_end)
    if vwap_variant == "close":
        return replace(panel, vwap=panel.close)
    if vwap_variant == "ohlc4":
        return replace(panel, vwap=(panel.open + panel.high + panel.low + panel.close) / 4.0)
    if vwap_variant == "hl2c4":
        return replace(panel, vwap=(panel.high + panel.low + 2.0 * panel.close) / 4.0)
    if vwap_variant == "hlc3":
        return panel
    raise ValueError(f"Unknown vwap variant: {vwap_variant}")


def _slice_panel(panel: Alpha101Panel, start: pd.Timestamp, end: pd.Timestamp) -> Alpha101Panel:
    return replace(
        panel,
        open=panel.open.loc[start:end],
        high=panel.high.loc[start:end],
        low=panel.low.loc[start:end],
        close=panel.close.loc[start:end],
        adj_close=panel.adj_close.loc[start:end],
        volume=panel.volume.loc[start:end],
        vwap=panel.vwap.loc[start:end],
        returns=panel.returns.loc[start:end],
        active_mask=panel.active_mask.loc[start:end],
        high_vol_mask=panel.high_vol_mask.loc[start:end],
    )


def _non_zero_run_lengths(series: pd.Series) -> list[int]:
    values = series.to_numpy(dtype=float, copy=False)
    if len(values) == 0:
        return []
    lengths: list[int] = []
    start = 0
    while start < len(values):
        current = values[start]
        end = start + 1
        while end < len(values) and values[end] == current:
            end += 1
        if current != 0.0:
            lengths.append(end - start)
        start = end
    return lengths


def _beta_to_benchmark(strategy_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    if strategy_returns.empty or benchmark_returns.empty:
        return float("nan")
    centered_strategy = strategy_returns.astype(float) - strategy_returns.astype(float).mean()
    centered_benchmark = benchmark_returns.astype(float) - benchmark_returns.astype(float).mean()
    variance = centered_benchmark.pow(2).mean()
    if variance == 0.0 or pd.isna(variance):
        return float("nan")
    covariance = centered_strategy.mul(centered_benchmark).mean()
    return float(covariance / variance)


def _latest_rolling_values(frame: pd.DataFrame) -> dict[str, float]:
    latest: dict[str, float] = {}
    for column in frame.columns:
        series = frame[column].dropna()
        latest[column] = float(series.iloc[-1]) if not series.empty else float("nan")
    return latest
