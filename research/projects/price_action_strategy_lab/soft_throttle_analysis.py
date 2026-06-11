from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.notebooks.alpha_001.research.alpha101_engine import forward_return
from research.projects.price_action_strategy_lab.activator_registry import ActivatorRegistry
from research.projects.price_action_strategy_lab.activator_suite import build_activator_masks
from research.projects.price_action_strategy_lab.alpha_registry import AlphaRegistry
from research.projects.price_action_strategy_lab.alpha_runner import load_signal_bundles
from research.projects.price_action_strategy_lab.backtest_modes import BacktestConfig
from research.projects.price_action_strategy_lab.backtest_modes import run_backtest
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.costs import turnover_cost


@dataclass(frozen=True)
class SoftThrottleConfig:
    alpha_names: tuple[str, ...]
    cache_dir: Path
    mode: str = "ranked_long_only"
    horizon: int = 10
    cost_bps: float = 10.0
    lookback_days: int = 504
    rolling_window_days: int = 21
    top_quantile: float = 0.8
    bottom_quantile: float = 0.2
    threshold: float = 0.0
    min_names: int = 20
    max_workers: int = 1
    gpu: GpuConfig = field(default_factory=GpuConfig)


@dataclass(frozen=True)
class SoftThrottleResult:
    metrics: pd.DataFrame
    aggregate: pd.DataFrame
    monthly: pd.DataFrame
    exposure: pd.DataFrame


def run_soft_throttle_analysis(
    panel: Alpha101Panel,
    alpha_registry: AlphaRegistry,
    activator_registry: ActivatorRegistry,
    recommendations: pd.DataFrame,
    config: SoftThrottleConfig,
    activator_masks: dict[str, pd.DataFrame] | None = None,
) -> SoftThrottleResult:
    bundles = load_signal_bundles(panel, alpha_registry, config.alpha_names, config.cache_dir, config.gpu, config.max_workers)
    masks = activator_masks if activator_masks is not None else build_activator_masks(panel, activator_registry, config.max_workers)
    intensities = _indicator_intensities(masks, config.lookback_days)
    future = forward_return(panel.close, config.horizon)
    by_variant: dict[str, list[pd.Series]] = {name: [] for name in _variant_names()}
    metric_rows: list[dict[str, object]] = []
    exposure_rows: list[dict[str, object]] = []
    for bundle_rows, bundle_exposure, bundle_series in _run_bundle_jobs(panel, future, bundles, intensities, recommendations, config):
        metric_rows.extend(bundle_rows)
        exposure_rows.extend(bundle_exposure)
        for variant, returns in bundle_series.items():
            by_variant[variant].append(returns)
    aggregate = _aggregate_metrics(by_variant, config.rolling_window_days)
    monthly = _monthly_metrics(by_variant)
    return SoftThrottleResult(pd.DataFrame(metric_rows), aggregate, monthly, pd.DataFrame(exposure_rows))


def _run_bundle_jobs(panel, future, bundles, intensities, recommendations, config):
    jobs = [(panel, future, bundle, intensities, recommendations, config) for bundle in bundles]
    workers = max(1, int(config.max_workers))
    if workers == 1 or len(jobs) == 1:
        return [_run_bundle_job(job) for job in jobs]
    with ProcessPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(_run_bundle_job, jobs))


def _run_bundle_job(job):
    panel, future, bundle, intensities, recommendations, config = job
    baseline, turnover = _baseline_stream(panel, future, bundle.signal, bundle.rank_pct, config)
    rec = _recommendation(recommendations, bundle.alpha)
    multipliers = _variant_multipliers(_intensity(rec, intensities, baseline.index), rec)
    metric_rows: list[dict[str, object]] = []
    exposure_rows: list[dict[str, object]] = []
    series: dict[str, pd.Series] = {}
    for variant, multiplier in multipliers.items():
        returns = baseline.mul(multiplier, fill_value=0.0)
        scaled_turnover = turnover.mul(multiplier.abs(), fill_value=0.0)
        metric_rows.append(_metric_row(bundle.alpha, variant, returns, config.rolling_window_days))
        exposure_rows.append(_exposure_row(bundle.alpha, variant, baseline, returns, scaled_turnover, multiplier, config))
        series[variant] = returns.rename(bundle.alpha)
    return metric_rows, exposure_rows, series


def write_soft_throttle_reports(result: SoftThrottleResult, report_dir: Path) -> tuple[Path, Path, Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = report_dir / "soft_throttle_2yr_metrics.csv"
    aggregate_path = report_dir / "soft_throttle_2yr_aggregate.csv"
    monthly_path = report_dir / "soft_throttle_2yr_monthly.csv"
    exposure_path = report_dir / "soft_throttle_exposure_diagnostics.csv"
    result.metrics.to_csv(metrics_path, index=False)
    result.aggregate.to_csv(aggregate_path, index=False)
    result.monthly.to_csv(monthly_path, index=False)
    result.exposure.to_csv(exposure_path, index=False)
    return metrics_path, aggregate_path, monthly_path, exposure_path


def _variant_names() -> tuple[str, ...]:
    return ("baseline", "hard_gate", "soft_conservative", "soft_aggressive", "drawdown_only_throttle")


def _indicator_intensities(masks: dict[str, pd.DataFrame], lookback_days: int) -> dict[str, pd.Series]:
    return {name: mask.mean(axis=1).fillna(0.0).tail(lookback_days) for name, mask in masks.items()}


def _baseline_stream(
    panel: Alpha101Panel,
    future: pd.DataFrame,
    signal: pd.DataFrame,
    rank_pct: pd.DataFrame | None,
    config: SoftThrottleConfig,
) -> tuple[pd.Series, pd.Series]:
    bt_config = BacktestConfig(
        name=f"{config.mode}:{config.horizon}d:{config.cost_bps:g}bps",
        mode=config.mode,
        horizon=config.horizon,
        cost_model=turnover_cost(config.cost_bps),
        top_quantile=config.top_quantile,
        bottom_quantile=config.bottom_quantile,
        threshold=config.threshold,
        min_names=config.min_names,
    )
    result = run_backtest(signal, future, bt_config, panel.active_mask, rank_pct)
    return _daily(result.net_return, config), _daily(result.turnover, config)


def _daily(series: pd.Series, config: SoftThrottleConfig) -> pd.Series:
    return series.fillna(0.0).div(float(config.horizon)).tail(config.lookback_days)


def _combine_series(series_list: list[pd.Series]) -> pd.Series:
    if not series_list:
        return pd.Series(dtype=float)
    return pd.concat(series_list, axis=1).mean(axis=1).fillna(0.0)


def _recommendation(recommendations: pd.DataFrame, alpha: str) -> pd.Series | None:
    if recommendations.empty:
        return None
    active = recommendations.loc[recommendations["alpha"].eq(alpha) & recommendations["decision"].eq("activate")]
    return active.iloc[0] if not active.empty else None


def _intensity(
    recommendation: pd.Series | None,
    intensities: dict[str, pd.Series],
    index: pd.Index,
) -> pd.Series:
    if recommendation is None:
        return pd.Series(0.0, index=index)
    return intensities[str(recommendation["indicator"])].reindex(index).fillna(0.0)


def _variant_multipliers(intensity: pd.Series, recommendation: pd.Series | None) -> dict[str, pd.Series]:
    one = pd.Series(1.0, index=intensity.index)
    if recommendation is None:
        return {name: one.copy() for name in _variant_names()}
    good = _good_gate(intensity, recommendation)
    adverse = _adverse_gate(intensity, recommendation)
    return {
        "baseline": one,
        "hard_gate": good.astype(float),
        "soft_conservative": pd.Series(np.where(good, 1.0, 0.5), index=intensity.index),
        "soft_aggressive": pd.Series(np.select([good, adverse], [1.25, 0.25], 1.0), index=intensity.index),
        "drawdown_only_throttle": pd.Series(np.where(adverse, 0.5, 1.0), index=intensity.index),
    }


def _good_gate(intensity: pd.Series, recommendation: pd.Series) -> pd.Series:
    threshold = float(recommendation["threshold"])
    if str(recommendation["side"]) == "high":
        return intensity.ge(threshold)
    return intensity.le(threshold)


def _adverse_gate(intensity: pd.Series, recommendation: pd.Series) -> pd.Series:
    quantile = float(recommendation["quantile"])
    if str(recommendation["side"]) == "high":
        return intensity.le(float(intensity.quantile(1.0 - quantile)))
    return intensity.ge(float(intensity.quantile(quantile)))


def _aggregate_metrics(by_variant: dict[str, list[pd.Series]], rolling_window_days: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for variant, series_list in by_variant.items():
        if not series_list:
            continue
        returns = pd.concat(series_list, axis=1).mean(axis=1).fillna(0.0)
        rows.append(_metric_row("aggregate_equal_weight", variant, returns, rolling_window_days))
    return pd.DataFrame(rows)


def _monthly_metrics(by_variant: dict[str, list[pd.Series]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for variant, series_list in by_variant.items():
        returns = pd.concat(series_list, axis=1).mean(axis=1).fillna(0.0)
        for month, month_returns in returns.groupby(pd.Grouper(freq="ME")):
            rows.append(_monthly_row(variant, month, month_returns))
    return pd.DataFrame(rows)


def _metric_row(alpha: str, variant: str, returns: pd.Series, rolling_window_days: int) -> dict[str, object]:
    clean = returns.dropna()
    rolling = _rolling_sharpe(clean, rolling_window_days)
    return {
        "alpha": alpha,
        "variant": variant,
        "obs": int(clean.shape[0]),
        "return_pct": _total_return_pct(clean),
        "cagr_pct": _cagr_pct(clean),
        "ann_vol_pct": _annual_vol_pct(clean),
        "ann_sharpe": _annual_sharpe(clean),
        "latest_1m_rolling_sharpe": _latest(rolling),
        "negative_1m_sharpe_windows": int(rolling.lt(0.0).sum()),
        "negative_1m_sharpe_rate": float(rolling.lt(0.0).mean()) if not rolling.empty else 0.0,
        "mean_negative_1m_sharpe": _mean_negative(rolling),
        "worst_1m_sharpe": float(rolling.min()) if not rolling.empty else float("nan"),
        "max_drawdown_pct": _max_drawdown_pct(clean),
    }


def _exposure_row(
    alpha: str,
    variant: str,
    baseline: pd.Series,
    returns: pd.Series,
    turnover: pd.Series,
    multiplier: pd.Series,
    config: SoftThrottleConfig,
) -> dict[str, object]:
    reduced = multiplier.lt(1.0)
    active = multiplier.gt(0.0)
    baseline_rolling = _rolling_sharpe(baseline, config.rolling_window_days)
    return {
        "alpha": alpha,
        "variant": variant,
        "active_day_pct": float(active.mean() * 100.0),
        "avg_exposure_multiplier": float(multiplier.mean()),
        "return_per_active_day_bps": _active_mean_bps(returns, active),
        "sharpe_while_active": _annual_sharpe(returns.loc[active]),
        "baseline_return_reduced_days_pct": _total_return_pct(baseline.loc[reduced]),
        "positive_windows_reduced": int((baseline_rolling.gt(0.0) & reduced.reindex(baseline_rolling.index)).sum()),
        "negative_windows_reduced": int((baseline_rolling.lt(0.0) & reduced.reindex(baseline_rolling.index)).sum()),
        "scaled_turnover_est": float(turnover.mean()),
    }


def _monthly_row(variant: str, month: pd.Timestamp, returns: pd.Series) -> dict[str, object]:
    return {
        "variant": variant,
        "month": month.strftime("%Y-%m"),
        "return_pct": _total_return_pct(returns),
        "ann_vol_pct": _annual_vol_pct(returns),
        "ann_sharpe": _annual_sharpe(returns),
        "obs": int(returns.dropna().shape[0]),
    }


def _rolling_sharpe(returns: pd.Series, window: int) -> pd.Series:
    mean = returns.rolling(window).mean()
    std = returns.rolling(window).std(ddof=1)
    return mean.div(std).mul(np.sqrt(252.0)).replace([np.inf, -np.inf], np.nan).dropna()


def _total_return_pct(returns: pd.Series) -> float:
    return float(((1.0 + returns.dropna()).prod() - 1.0) * 100.0)


def _cagr_pct(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return float("nan")
    return float(((1.0 + _total_return_pct(clean) / 100.0) ** (252.0 / clean.shape[0]) - 1.0) * 100.0)


def _annual_vol_pct(returns: pd.Series) -> float:
    clean = returns.dropna()
    return float(clean.std(ddof=1) * np.sqrt(252.0) * 100.0) if clean.shape[0] > 1 else float("nan")


def _annual_sharpe(returns: pd.Series) -> float:
    clean = returns.dropna()
    std = float(clean.std(ddof=1)) if clean.shape[0] > 1 else 0.0
    return float(clean.mean() / std * np.sqrt(252.0)) if std > 0.0 else float("nan")


def _max_drawdown_pct(returns: pd.Series) -> float:
    if returns.empty:
        return float("nan")
    equity = (1.0 + returns.fillna(0.0)).cumprod()
    return float((equity / equity.cummax() - 1.0).min() * 100.0)


def _latest(series: pd.Series) -> float:
    return float(series.iloc[-1]) if not series.empty else float("nan")


def _mean_negative(series: pd.Series) -> float:
    negative = series.loc[series.lt(0.0)]
    return float(negative.mean()) if not negative.empty else 0.0


def _active_mean_bps(returns: pd.Series, active: pd.Series) -> float:
    active_returns = returns.loc[active]
    return float(active_returns.mean() * 10_000.0) if not active_returns.empty else 0.0
