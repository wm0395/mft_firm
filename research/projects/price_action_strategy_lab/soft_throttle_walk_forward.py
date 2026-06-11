from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import TypedDict

import pandas as pd

from project.alpha_math.validation import purged_time_split
from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel, forward_return
from research.projects.price_action_strategy_lab.activator_registry import ActivatorRegistry
from research.projects.price_action_strategy_lab.activator_suite import build_activator_masks
from research.projects.price_action_strategy_lab.alpha_registry import AlphaRegistry
from research.projects.price_action_strategy_lab.alpha_runner import load_signal_bundles
from research.projects.price_action_strategy_lab.backtest_modes import BacktestConfig
from research.projects.price_action_strategy_lab.backtest_modes import run_backtest
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.costs import turnover_cost
from research.projects.price_action_strategy_lab.indicator_alpha_diagnostics import IndicatorDiagnosticsConfig
from research.projects.price_action_strategy_lab.indicator_alpha_diagnostics import build_indicator_diagnostic_frame
from research.projects.price_action_strategy_lab.indicator_alpha_diagnostics import tune_indicator_gates_from_frame
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _indicator_intensities
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _variant_multipliers
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _combine_series
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import aggregate_rows
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import decision_frame
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import decision_markdown
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import fold_exposure_row
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import fold_metric_row
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import gate_row
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import gate_stability
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import variant_names

_PANDAS_REINDEX_LOCK = Lock()


@dataclass(frozen=True)
class WalkForwardThrottleConfig:
    alpha_names: tuple[str, ...]
    cache_dir: Path
    mode: str = "ranked_long_only"
    horizon: int = 10
    cost_bps: float = 10.0
    lookback_days: int = 504
    rolling_window_days: int = 21
    train_size_days: int = 126
    test_size_days: int = 21
    step_size_days: int = 21
    lookahead_days: int = 10
    max_folds: int = 0
    fold_selection: str = "earliest"
    top_quantile: float = 0.8
    bottom_quantile: float = 0.2
    threshold: float = 0.0
    min_names: int = 20
    max_workers: int = 1
    gpu: GpuConfig = field(default_factory=GpuConfig)


@dataclass(frozen=True)
class WalkForwardThrottleResult:
    folds: pd.DataFrame
    alpha_folds: pd.DataFrame
    aggregate: pd.DataFrame
    selected_gates: pd.DataFrame
    gate_stability: pd.DataFrame
    exposure: pd.DataFrame
    decision: pd.DataFrame


class FoldStreams(TypedDict):
    series: dict[str, list[pd.Series]]
    turnover: dict[str, list[pd.Series]]
    multiplier: dict[str, list[pd.Series]]
    gate_rows: list[dict[str, object]]


class FoldOutputs(TypedDict):
    fold_rows: list[dict[str, object]]
    alpha_fold_rows: list[dict[str, object]]
    gate_rows: list[dict[str, object]]
    exposure_rows: list[dict[str, object]]
    series: dict[str, pd.Series]
    turnover: dict[str, pd.Series]


def run_walk_forward_soft_throttle(
    panel: Alpha101Panel,
    alpha_registry: AlphaRegistry,
    activator_registry: ActivatorRegistry,
    config: WalkForwardThrottleConfig,
    diagnostic_frame: pd.DataFrame | None = None,
    activator_masks: dict[str, pd.DataFrame] | None = None,
) -> WalkForwardThrottleResult:
    bundles = load_signal_bundles(panel, alpha_registry, config.alpha_names, config.cache_dir, config.gpu, config.max_workers)
    masks = activator_masks if activator_masks is not None else build_activator_masks(panel, activator_registry, config.max_workers)
    intensities = _indicator_intensities(masks, len(panel.close.index))
    diagnostic_frame = diagnostic_frame if diagnostic_frame is not None else build_indicator_diagnostic_frame(
        panel, alpha_registry, activator_registry, _diagnostics_config(config)
    )
    folds = build_walk_forward_fold_specs(panel.close.index, config)
    if not folds:
        empty = pd.DataFrame()
        return WalkForwardThrottleResult(empty, empty, empty, empty, empty, empty, empty)
    future_returns = forward_return(panel.close, config.horizon)
    fold_rows: list[dict[str, object]] = []
    alpha_fold_rows: list[dict[str, object]] = []
    gate_rows: list[dict[str, object]] = []
    exposure_rows: list[dict[str, object]] = []
    aggregate_series: dict[str, list[pd.Series]] = {name: [] for name in variant_names()}
    aggregate_turnover: dict[str, list[pd.Series]] = {name: [] for name in variant_names()}
    fold_results = _run_fold_jobs(panel, bundles, intensities, diagnostic_frame, config, folds, future_returns)
    for fold, fold_result in fold_results:
        fold_rows.extend(fold_result["fold_rows"])
        alpha_fold_rows.extend(fold_result["alpha_fold_rows"])
        gate_rows.extend(fold_result["gate_rows"])
        exposure_rows.extend(fold_result["exposure_rows"])
        for variant, series in fold_result["series"].items():
            aggregate_series[variant].append(series.rename(f"fold_{fold.fold}"))
        for variant, series in fold_result["turnover"].items():
            aggregate_turnover[variant].append(series.rename(f"fold_{fold.fold}"))
    fold_frame = pd.DataFrame(fold_rows)
    alpha_fold_frame = pd.DataFrame(alpha_fold_rows)
    aggregate = aggregate_rows(fold_frame, aggregate_series, aggregate_turnover, variant_names())
    selected_gates = pd.DataFrame(gate_rows)
    gate_stability_frame = gate_stability(selected_gates)
    exposure = pd.DataFrame(exposure_rows)
    decision = decision_frame(aggregate)
    return WalkForwardThrottleResult(fold_frame, alpha_fold_frame, aggregate, selected_gates, gate_stability_frame, exposure, decision)


def write_walk_forward_soft_throttle_reports(
    result: WalkForwardThrottleResult,
    report_dir: Path,
) -> tuple[Path, Path, Path, Path, Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    fold_path = report_dir / "soft_throttle_walk_forward_fold_metrics.csv"
    alpha_fold_path = report_dir / "soft_throttle_walk_forward_alpha_fold_metrics.csv"
    aggregate_path = report_dir / "soft_throttle_walk_forward_aggregate.csv"
    gates_path = report_dir / "soft_throttle_walk_forward_selected_gates.csv"
    stability_path = report_dir / "soft_throttle_walk_forward_gate_stability.csv"
    exposure_path = report_dir / "soft_throttle_walk_forward_exposure.csv"
    decision_path = report_dir / "soft_throttle_walk_forward_decision.md"
    result.folds.to_csv(fold_path, index=False)
    result.alpha_folds.to_csv(alpha_fold_path, index=False)
    result.aggregate.to_csv(aggregate_path, index=False)
    result.selected_gates.to_csv(gates_path, index=False)
    result.gate_stability.to_csv(stability_path, index=False)
    result.exposure.to_csv(exposure_path, index=False)
    decision_path.write_text(decision_markdown(result.decision, result.aggregate), encoding="utf-8")
    return fold_path, aggregate_path, gates_path, stability_path, exposure_path, decision_path


def build_walk_forward_fold_specs(
    index: pd.Index,
    config: WalkForwardThrottleConfig,
) -> tuple[WalkForwardFoldSpec, ...]:
    folds = tuple(
        WalkForwardFoldSpec(fold=fold, train_index=train_index, test_index=test_index)
        for fold, (train_index, test_index) in enumerate(
            purged_time_split(
                index,
                config.train_size_days,
                config.test_size_days,
                config.lookahead_days,
                config.step_size_days,
            )
        )
    )
    if config.max_folds <= 0:
        return folds
    if config.fold_selection == "latest":
        return folds[-config.max_folds :]
    if config.fold_selection != "earliest":
        raise ValueError(f"unsupported fold_selection: {config.fold_selection}")
    return folds[: config.max_folds]


@dataclass(frozen=True)
class WalkForwardFoldSpec:
    fold: int
    train_index: pd.Index
    test_index: pd.Index


def _train_recommendations(
    diagnostic_frame: pd.DataFrame,
    config: WalkForwardThrottleConfig,
    train_index: pd.Index,
) -> pd.DataFrame:
    train_frame = diagnostic_frame.loc[diagnostic_frame["date"].isin(train_index)].copy()
    train_frame = train_frame.loc[train_frame["date"].notna()]
    return tune_indicator_gates_from_frame(train_frame, _diagnostics_config(config))


def _run_fold_jobs(
    panel: Alpha101Panel,
    bundles,
    intensities: dict[str, pd.Series],
    diagnostic_frame: pd.DataFrame,
    config: WalkForwardThrottleConfig,
    folds: tuple[WalkForwardFoldSpec, ...],
    future_returns: pd.DataFrame,
) -> list[tuple[WalkForwardFoldSpec, FoldOutputs]]:
    jobs = [(panel, bundles, intensities, diagnostic_frame, config, fold, future_returns) for fold in folds]
    workers = max(1, int(config.max_workers))
    if workers == 1 or len(jobs) == 1:
        return [_run_fold_job(job) for job in jobs]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(_run_fold_job, jobs))


def _run_fold_job(
    job: tuple[
        Alpha101Panel,
        object,
        dict[str, pd.Series],
        pd.DataFrame,
        WalkForwardThrottleConfig,
        WalkForwardFoldSpec,
        pd.DataFrame,
    ],
) -> tuple[WalkForwardFoldSpec, FoldOutputs]:
    panel, bundles, intensities, diagnostic_frame, config, fold, future_returns = job
    recommendations = _train_recommendations(diagnostic_frame, config, fold.train_index)
    return fold, _evaluate_fold(panel, bundles, intensities, recommendations, config, fold, future_returns)


def _evaluate_fold(
    panel: Alpha101Panel,
    bundles,
    intensities: dict[str, pd.Series],
    recommendations: pd.DataFrame,
    config: WalkForwardThrottleConfig,
    fold: WalkForwardFoldSpec,
    future_returns: pd.DataFrame,
) -> FoldOutputs:
    test_index = fold.test_index
    with _PANDAS_REINDEX_LOCK:
        future = future_returns.reindex(test_index).copy()
    streams = _build_fold_streams(panel, bundles, intensities, recommendations, config, test_index, future, fold)
    return _fold_outputs(fold, streams, config.rolling_window_days)


def _build_fold_streams(
    panel: Alpha101Panel,
    bundles,
    intensities: dict[str, pd.Series],
    recommendations: pd.DataFrame,
    config: WalkForwardThrottleConfig,
    test_index: pd.Index,
    future: pd.DataFrame,
    fold: WalkForwardFoldSpec,
) -> FoldStreams:
    variant_series: dict[str, list[pd.Series]] = {name: [] for name in variant_names()}
    variant_turnover: dict[str, list[pd.Series]] = {name: [] for name in variant_names()}
    variant_multiplier: dict[str, list[pd.Series]] = {name: [] for name in variant_names()}
    gate_rows: list[dict[str, object]] = []
    def _bundle_job(bundle) -> tuple[str, pd.Series, pd.Series, dict[str, pd.Series], dict[str, object]]:
        with _PANDAS_REINDEX_LOCK:
            signal = bundle.signal.reindex(test_index).copy()
            rank_pct = bundle.rank_pct.reindex(test_index).copy()
            intensity = _intensity(_recommendation(recommendations, bundle.alpha), intensities, test_index)
        baseline, turnover = _baseline_stream(
            panel,
            future,
            signal,
            rank_pct,
            config,
            test_index,
        )
        rec = _recommendation(recommendations, bundle.alpha)
        multipliers = _variant_multipliers(intensity, rec)
        return bundle.alpha, baseline, turnover, multipliers, gate_row(fold, bundle.alpha, rec)

    bundle_rows = [_bundle_job(bundle) for bundle in bundles]
    for alpha, baseline, turnover, multipliers, gate in bundle_rows:
        gate_rows.append(gate)
        for variant, multiplier in multipliers.items():
            variant_series[variant].append(baseline.mul(multiplier, fill_value=0.0).rename(alpha))
            variant_turnover[variant].append(turnover.mul(multiplier.abs(), fill_value=0.0).rename(alpha))
            variant_multiplier[variant].append(multiplier.rename(alpha))
    return {
        "series": variant_series,
        "turnover": variant_turnover,
        "multiplier": variant_multiplier,
        "gate_rows": gate_rows,
    }


def _fold_outputs(
    fold: WalkForwardFoldSpec,
    streams: FoldStreams,
    rolling_window_days: int,
) -> FoldOutputs:
    variant_series = streams["series"]
    variant_turnover = streams["turnover"]
    variant_multiplier = streams["multiplier"]
    return {
        "fold_rows": [
            fold_metric_row(
                fold,
                variant,
                _combine_series(variant_series[variant]),
                _combine_series(variant_turnover[variant]),
                _combine_series(variant_multiplier[variant]),
                rolling_window_days,
            )
            for variant in variant_names()
        ],
        "alpha_fold_rows": [
            dict(
                fold_metric_row(fold, variant, series, variant_turnover[variant][idx], variant_multiplier[variant][idx], rolling_window_days),
                alpha=str(series.name),
            )
            for variant in variant_names()
            for idx, series in enumerate(variant_series[variant])
        ],
        "gate_rows": streams["gate_rows"],
        "exposure_rows": [
            fold_exposure_row(
                fold,
                variant,
                _combine_series(variant_series[variant]),
                _combine_series(variant_turnover[variant]),
                _combine_series(variant_multiplier[variant]),
                rolling_window_days,
            )
            for variant in variant_names()
        ],
        "series": {variant: _combine_series(variant_series[variant]) for variant in variant_names()},
        "turnover": {variant: _combine_series(variant_turnover[variant]) for variant in variant_names()},
    }


def _baseline_stream(
    panel: Alpha101Panel,
    future: pd.DataFrame,
    signal: pd.DataFrame,
    rank_pct: pd.DataFrame,
    config: WalkForwardThrottleConfig,
    test_index: pd.Index,
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
    with _PANDAS_REINDEX_LOCK:
        active_mask = panel.active_mask.reindex(test_index).copy()
    result = run_backtest(signal, future, bt_config, active_mask, rank_pct)
    return _daily_walk_forward(result.net_return, config), _daily_walk_forward(result.turnover, config)


def _daily_walk_forward(series: pd.Series, config: WalkForwardThrottleConfig) -> pd.Series:
    return series.fillna(0.0).div(float(config.horizon))


def _recommendation(recommendations: pd.DataFrame, alpha: str) -> pd.Series | None:
    if recommendations.empty:
        return None
    match = recommendations.loc[recommendations["alpha"].eq(alpha) & recommendations["decision"].eq("activate")]
    return match.iloc[0] if not match.empty else None


def _intensity(
    recommendation: pd.Series | None,
    intensities: dict[str, pd.Series],
    index: pd.Index,
) -> pd.Series:
    if recommendation is None:
        return pd.Series(0.0, index=index)
    return intensities[str(recommendation["indicator"])].reindex(index).fillna(0.0)


def _diagnostics_config(config: WalkForwardThrottleConfig) -> IndicatorDiagnosticsConfig:
    return IndicatorDiagnosticsConfig(
        alpha_names=config.alpha_names,
        cache_dir=config.cache_dir,
        mode=config.mode,
        horizon=config.horizon,
        cost_bps=config.cost_bps,
        lookback_days=config.lookback_days,
        top_quantile=config.top_quantile,
        bottom_quantile=config.bottom_quantile,
        threshold=config.threshold,
        min_names=config.min_names,
        min_coverage=0.05,
        max_coverage=0.80,
        quantiles=(0.50, 0.60, 0.70, 0.80, 0.90),
        max_workers=config.max_workers,
        gpu=config.gpu,
    )
