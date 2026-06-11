from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from hashlib import sha256
from pathlib import Path

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
from research.projects.price_action_strategy_lab.validation_pipeline import SignalBundle


@dataclass(frozen=True)
class IndicatorDiagnosticsConfig:
    alpha_names: tuple[str, ...]
    cache_dir: Path
    mode: str = "ranked_long_only"
    horizon: int = 10
    cost_bps: float = 10.0
    lookback_days: int = 504
    top_quantile: float = 0.8
    bottom_quantile: float = 0.2
    threshold: float = 0.0
    min_names: int = 20
    min_coverage: float = 0.05
    max_coverage: float = 0.80
    quantiles: tuple[float, ...] = (0.50, 0.60, 0.70, 0.80, 0.90)
    max_workers: int = 1
    gpu: GpuConfig = field(default_factory=GpuConfig)


@dataclass(frozen=True)
class IndicatorDiagnosticsResult:
    correlations: pd.DataFrame
    threshold_grid: pd.DataFrame
    recommendations: pd.DataFrame


def run_indicator_alpha_diagnostics(
    panel: Alpha101Panel,
    alpha_registry: AlphaRegistry,
    activator_registry: ActivatorRegistry,
    config: IndicatorDiagnosticsConfig,
) -> IndicatorDiagnosticsResult:
    frame = build_indicator_diagnostic_frame(panel, alpha_registry, activator_registry, config)
    return run_indicator_alpha_diagnostics_from_frame(frame, config)


def run_indicator_alpha_diagnostics_from_frame(
    frame: pd.DataFrame,
    config: IndicatorDiagnosticsConfig,
) -> IndicatorDiagnosticsResult:
    correlations = _correlation_rows(frame)
    grid = _threshold_grid(frame, config)
    recommendations = tune_indicator_gates(grid)
    return IndicatorDiagnosticsResult(correlations, grid, recommendations)


def load_or_build_indicator_diagnostic_frame(
    panel: Alpha101Panel,
    alpha_registry: AlphaRegistry,
    activator_registry: ActivatorRegistry,
    config: IndicatorDiagnosticsConfig,
) -> pd.DataFrame:
    path = _diagnostic_frame_cache_path(panel, config)
    if path.exists():
        return pd.read_pickle(path)
    frame = build_indicator_diagnostic_frame(panel, alpha_registry, activator_registry, config)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_pickle(path)
    return frame


def build_indicator_diagnostic_frame(
    panel: Alpha101Panel,
    alpha_registry: AlphaRegistry,
    activator_registry: ActivatorRegistry,
    config: IndicatorDiagnosticsConfig,
) -> pd.DataFrame:
    bundles = load_signal_bundles(panel, alpha_registry, config.alpha_names, config.cache_dir, config.gpu, config.max_workers)
    masks = build_activator_masks(panel, activator_registry, config.max_workers)
    future = forward_return(panel.close, config.horizon)
    indicators = _indicator_intensities(masks, config.lookback_days)
    rows: list[dict[str, object]] = []
    for bundle in bundles:
        performance = _alpha_performance(panel, future, bundle, config)
        performance = _daily_equivalent(performance, config).tail(config.lookback_days)
        labels = _performance_labels(performance)
        spec = alpha_registry.by_name[bundle.alpha]
        for name, intensity in indicators.items():
            aligned = _aligned_frame(performance, intensity, labels)
            rows.extend(_frame_rows(bundle.alpha, spec.family, name, aligned))
    return pd.DataFrame(rows)


def _diagnostic_frame_cache_path(panel: Alpha101Panel, config: IndicatorDiagnosticsConfig) -> Path:
    payload = "|".join(
        [
            panel.name,
            str(panel.close.index.min()),
            str(panel.close.index.max()),
            str(panel.close.shape),
            ",".join(config.alpha_names),
            config.mode,
            str(config.horizon),
            str(config.cost_bps),
            str(config.lookback_days),
            str(config.top_quantile),
            str(config.bottom_quantile),
            str(config.threshold),
            str(config.min_names),
            ",".join(str(item) for item in config.quantiles),
        ]
    )
    key = sha256(payload.encode("utf-8")).hexdigest()[:24]
    return config.cache_dir / "indicator_diagnostic_frame" / f"{key}.pkl"


def tune_indicator_gates_from_frame(frame: pd.DataFrame, config: IndicatorDiagnosticsConfig) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=_recommendation_columns())
    rows: list[dict[str, object]] = []
    grouped = frame.groupby(["alpha", "family", "indicator"], sort=False)
    for (alpha, family, indicator), group in grouped:
        aligned = group.set_index("date")[["return", "intensity", "underperform", "overperform"]]
        rows.extend(_threshold_rows(alpha, family, indicator, aligned, config))
    return tune_indicator_gates(pd.DataFrame(rows))


def _correlation_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    rows = []
    for (alpha, family, indicator), group in frame.groupby(["alpha", "family", "indicator"], sort=False):
        aligned = group.set_index("date")[["return", "intensity", "underperform", "overperform"]]
        rows.append(_correlation_row(alpha, family, indicator, aligned))
    return pd.DataFrame(rows)


def _threshold_grid(frame: pd.DataFrame, config: IndicatorDiagnosticsConfig) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for (alpha, family, indicator), group in frame.groupby(["alpha", "family", "indicator"], sort=False):
        aligned = group.set_index("date")[["return", "intensity", "underperform", "overperform"]]
        rows.extend(_threshold_rows(alpha, family, indicator, aligned, config))
    return pd.DataFrame(rows)


def write_indicator_alpha_diagnostics_reports(
    result: IndicatorDiagnosticsResult,
    report_dir: Path,
) -> tuple[Path, Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    corr_path = report_dir / "indicator_alpha_correlations.csv"
    grid_path = report_dir / "indicator_alpha_threshold_grid.csv"
    rec_path = report_dir / "indicator_alpha_tuned_gates.csv"
    result.correlations.to_csv(corr_path, index=False)
    result.threshold_grid.to_csv(grid_path, index=False)
    result.recommendations.to_csv(rec_path, index=False)
    return corr_path, grid_path, rec_path


def tune_indicator_gates(grid: pd.DataFrame) -> pd.DataFrame:
    columns = _recommendation_columns()
    if grid.empty:
        return pd.DataFrame(columns=columns)
    eligible = grid.loc[grid["eligible"]].copy()
    if eligible.empty:
        return pd.DataFrame(columns=columns)
    ordered = eligible.sort_values(["alpha", "score", "lift_bps"], ascending=[True, False, False])
    chosen = ordered.groupby("alpha", as_index=False).first()
    chosen["decision"] = chosen.apply(_decision, axis=1)
    return chosen[columns].sort_values(["decision", "score"], ascending=[True, False])


def _indicator_intensities(masks: dict[str, pd.DataFrame], lookback_days: int) -> dict[str, pd.Series]:
    intensities: dict[str, pd.Series] = {}
    for name, mask in masks.items():
        intensities[name] = mask.mean(axis=1).fillna(0.0).tail(lookback_days)
    return intensities


def _alpha_performance(
    panel: Alpha101Panel,
    future: pd.DataFrame,
    bundle: SignalBundle,
    config: IndicatorDiagnosticsConfig,
) -> pd.Series:
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
    result = run_backtest(bundle.signal, future, bt_config, panel.active_mask, bundle.rank_pct)
    return result.net_return


def _daily_equivalent(series: pd.Series, config: IndicatorDiagnosticsConfig) -> pd.Series:
    return series.fillna(0.0) / float(config.horizon)


def _performance_labels(performance: pd.Series) -> pd.DataFrame:
    lower = performance.quantile(0.20)
    upper = performance.quantile(0.80)
    return pd.DataFrame(
        {
            "underperform": performance.le(lower).astype(float),
            "overperform": performance.ge(upper).astype(float),
        },
        index=performance.index,
    )


def _aligned_frame(performance: pd.Series, intensity: pd.Series, labels: pd.DataFrame) -> pd.DataFrame:
    frame = pd.DataFrame({"return": performance, "intensity": intensity}).join(labels, how="inner")
    return frame.dropna()


def _frame_rows(alpha: str, family: str, indicator: str, frame: pd.DataFrame) -> list[dict[str, object]]:
    if frame.empty:
        return []
    indexed = frame.copy()
    indexed.index.name = "date"
    indexed = indexed.reset_index()
    indexed["alpha"] = alpha
    indexed["family"] = family
    indexed["indicator"] = indicator
    return indexed[["alpha", "family", "indicator", "date", "return", "intensity", "underperform", "overperform"]].to_dict(
        orient="records"
    )


def _correlation_row(alpha: str, family: str, indicator: str, frame: pd.DataFrame) -> dict[str, object]:
    return {
        "alpha": alpha,
        "family": family,
        "indicator": indicator,
        "obs": len(frame),
        "coverage": float(frame["intensity"].gt(0.0).mean()) if not frame.empty else 0.0,
        "return_corr": _corr(frame["intensity"], frame["return"]),
        "return_spearman": _spearman(frame["intensity"], frame["return"]),
        "underperform_corr": _corr(frame["intensity"], frame["underperform"]),
        "overperform_corr": _corr(frame["intensity"], frame["overperform"]),
    }


def _threshold_rows(
    alpha: str,
    family: str,
    indicator: str,
    frame: pd.DataFrame,
    config: IndicatorDiagnosticsConfig,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for quantile in config.quantiles:
        rows.append(_threshold_row(alpha, family, indicator, frame, config, quantile, "high"))
        rows.append(_threshold_row(alpha, family, indicator, frame, config, quantile, "low"))
    return rows


def _threshold_row(
    alpha: str,
    family: str,
    indicator: str,
    frame: pd.DataFrame,
    config: IndicatorDiagnosticsConfig,
    quantile: float,
    side: str,
) -> dict[str, object]:
    gate = _threshold_gate(frame["intensity"], quantile, side)
    metrics = _gate_metrics(frame, gate)
    score = _score(metrics)
    return {
        "alpha": alpha,
        "family": family,
        "indicator": indicator,
        "side": side,
        "quantile": quantile,
        "threshold": _threshold_value(frame["intensity"], quantile, side),
        "eligible": config.min_coverage <= metrics["coverage"] <= config.max_coverage,
        "score": score,
        **metrics,
    }


def _threshold_gate(intensity: pd.Series, quantile: float, side: str) -> pd.Series:
    if side == "high":
        return intensity.ge(float(intensity.quantile(quantile)))
    return intensity.le(float(intensity.quantile(1.0 - quantile)))


def _threshold_value(intensity: pd.Series, quantile: float, side: str) -> float:
    target = quantile if side == "high" else 1.0 - quantile
    return float(intensity.quantile(target))


def _gate_metrics(frame: pd.DataFrame, gate: pd.Series) -> dict[str, float]:
    on = frame.loc[gate]
    off = frame.loc[~gate]
    on_mean = float(on["return"].mean() * 10_000.0) if not on.empty else 0.0
    off_mean = float(off["return"].mean() * 10_000.0) if not off.empty else 0.0
    return {
        "coverage": float(gate.mean()),
        "on_return_bps": on_mean,
        "off_return_bps": off_mean,
        "lift_bps": on_mean - off_mean,
        "bad_rate_on": _label_rate(on, "underperform"),
        "bad_rate_off": _label_rate(off, "underperform"),
        "good_rate_on": _label_rate(on, "overperform"),
        "good_rate_off": _label_rate(off, "overperform"),
    }


def _score(metrics: dict[str, float]) -> float:
    bad_avoidance = metrics["bad_rate_off"] - metrics["bad_rate_on"]
    good_capture = metrics["good_rate_on"] - metrics["good_rate_off"]
    return metrics["lift_bps"] + 100.0 * bad_avoidance + 50.0 * good_capture


def _label_rate(frame: pd.DataFrame, column: str) -> float:
    return float(frame[column].mean()) if not frame.empty else 0.0


def _corr(left: pd.Series, right: pd.Series) -> float:
    if left.std(ddof=0) == 0.0 or right.std(ddof=0) == 0.0:
        return 0.0
    return float(left.corr(right))


def _spearman(left: pd.Series, right: pd.Series) -> float:
    return _corr(left.rank(method="average"), right.rank(method="average"))


def _decision(row: pd.Series) -> str:
    if float(row["score"]) > 0.0 and float(row["lift_bps"]) > 0.0:
        return "activate"
    return "abstain"


def _recommendation_columns() -> list[str]:
    return [
        "alpha",
        "family",
        "indicator",
        "side",
        "quantile",
        "threshold",
        "coverage",
        "score",
        "lift_bps",
        "on_return_bps",
        "off_return_bps",
        "bad_rate_on",
        "bad_rate_off",
        "good_rate_on",
        "good_rate_off",
        "decision",
    ]
