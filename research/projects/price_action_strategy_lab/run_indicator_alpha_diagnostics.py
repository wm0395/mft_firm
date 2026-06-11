from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from project.data.market_collector_panel import load_market_collector_native_panel_from_database
from project.data.market_collector_panel import load_market_collector_panel_from_database
from research.projects.price_action_strategy_lab.activator_specs import default_activator_registry
from research.projects.price_action_strategy_lab.activator_suite import build_activator_masks
from research.projects.price_action_strategy_lab.alpha_regime_hypothesis_book import write_alpha_regime_hypothesis_book
from research.projects.price_action_strategy_lab.alpha_specs import default_alpha_registry
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.falsification_report import write_falsification_report
from research.projects.price_action_strategy_lab.indicator_alpha_diagnostics import IndicatorDiagnosticsConfig
from research.projects.price_action_strategy_lab.indicator_alpha_diagnostics import load_or_build_indicator_diagnostic_frame
from research.projects.price_action_strategy_lab.indicator_alpha_diagnostics import run_indicator_alpha_diagnostics_from_frame
from research.projects.price_action_strategy_lab.indicator_alpha_diagnostics import write_indicator_alpha_diagnostics_reports
from research.projects.price_action_strategy_lab.run_activator_suite import _database_path
from research.projects.price_action_strategy_lab.run_activator_suite import _panel_request
from research.projects.price_action_strategy_lab.run_activator_suite import _read_config
from research.projects.price_action_strategy_lab.soft_throttle_analysis import SoftThrottleConfig
from research.projects.price_action_strategy_lab.soft_throttle_analysis import run_soft_throttle_analysis
from research.projects.price_action_strategy_lab.soft_throttle_analysis import write_soft_throttle_reports
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward import WalkForwardThrottleConfig
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward import run_walk_forward_soft_throttle
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward import write_walk_forward_soft_throttle_reports
from research.projects.price_action_strategy_lab.tail_failure_report import write_tail_failure_report
from research.projects.price_action_strategy_lab.universe_adapter import to_alpha101_panel
from research.projects.price_action_strategy_lab.weak_fold_event_report import write_weak_fold_event_report


@dataclass(frozen=True)
class IndicatorDiagnosticsRunResult:
    report_dir: Path
    correlations_path: Path
    threshold_grid_path: Path
    recommendations_path: Path
    soft_throttle_paths: tuple[Path, Path, Path, Path] | None = None
    walk_forward_paths: tuple[Path, Path, Path, Path, Path, Path] | None = None
    tail_failure_paths: tuple[Path, Path, Path, Path] | None = None
    hypothesis_book_paths: tuple[Path, Path] | None = None
    falsification_paths: tuple[Path, Path] | None = None
    weak_fold_event_paths: tuple[Path, Path] | None = None


def run_indicator_alpha_diagnostics_config(config_path: str | Path) -> IndicatorDiagnosticsRunResult:
    config = _read_config(Path(config_path))
    raw_panel = _load_panel(config)
    panel = to_alpha101_panel(raw_panel)
    alpha_registry = default_alpha_registry()
    activator_registry = default_activator_registry()
    diagnostics_config = _diagnostics_config(config)
    diagnostic_frame = load_or_build_indicator_diagnostic_frame(
        panel,
        alpha_registry,
        activator_registry,
        diagnostics_config,
    )
    result = run_indicator_alpha_diagnostics_from_frame(diagnostic_frame, diagnostics_config)
    paths = write_indicator_alpha_diagnostics_reports(result, _report_dir(config))
    activator_masks = _shared_activator_masks(config, panel, activator_registry)
    soft_paths = _soft_throttle_paths(config, panel, alpha_registry, activator_registry, result.recommendations, activator_masks)
    walk_paths = _walk_forward_paths(config, panel, alpha_registry, activator_registry, diagnostic_frame, activator_masks)
    tail_paths = _tail_failure_paths(config, walk_paths)
    book_paths = _hypothesis_book_paths(config, tail_paths)
    falsification_paths = _falsification_paths(config, book_paths)
    weak_fold_paths = _weak_fold_event_paths(config, walk_paths)
    return IndicatorDiagnosticsRunResult(
        _report_dir(config),
        paths[0],
        paths[1],
        paths[2],
        soft_paths,
        walk_paths,
        tail_paths,
        book_paths,
        falsification_paths,
        weak_fold_paths,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    result = run_indicator_alpha_diagnostics_config(args.config)
    print(f"wrote indicator diagnostics to {result.report_dir}")
    return 0


def _diagnostics_config(config: dict[str, Any]) -> IndicatorDiagnosticsConfig:
    backtests = dict(config.get("backtests", {}))
    compute = dict(config.get("compute", {}))
    gpu = dict(config.get("gpu", {}))
    screen = dict(config.get("activator_screen", {}))
    diagnostics = dict(config.get("indicator_diagnostics", {}))
    return IndicatorDiagnosticsConfig(
        alpha_names=tuple(config.get("alphas", ())),
        cache_dir=Path(str(compute.get("cache_dir", ".cache/price_action_activators"))),
        mode=str(screen.get("mode", "ranked_long_only")),
        horizon=int(screen.get("horizon", 10)),
        cost_bps=float(screen.get("cost_bps", 10.0)),
        lookback_days=int(diagnostics.get("lookback_days", 504)),
        top_quantile=float(backtests.get("top_quantile", 0.8)),
        bottom_quantile=float(backtests.get("bottom_quantile", 0.2)),
        threshold=float(backtests.get("threshold", 0.0)),
        min_names=int(backtests.get("min_active_names", 1)),
        min_coverage=float(diagnostics.get("min_coverage", 0.05)),
        max_coverage=float(diagnostics.get("max_coverage", 0.80)),
        quantiles=tuple(float(item) for item in diagnostics.get("quantiles", (0.50, 0.60, 0.70, 0.80, 0.90))),
        max_workers=int(compute.get("max_workers") or 1),
        gpu=GpuConfig(enabled=bool(gpu.get("enabled", False)), backend=str(gpu.get("backend") or "auto")),
    )


def _soft_throttle_paths(
    config: dict[str, Any],
    panel,
    alpha_registry,
    activator_registry,
    recommendations,
    activator_masks,
) -> tuple[Path, Path, Path, Path] | None:
    soft = dict(config.get("soft_throttle", {}))
    if not bool(soft.get("enabled", False)):
        return None
    result = run_soft_throttle_analysis(
        panel,
        alpha_registry,
        activator_registry,
        recommendations,
        _soft_throttle_config(config),
        activator_masks,
    )
    return write_soft_throttle_reports(result, _report_dir(config))


def _walk_forward_paths(
    config: dict[str, Any],
    panel,
    alpha_registry,
    activator_registry,
    diagnostic_frame,
    activator_masks,
) -> tuple[Path, Path, Path, Path, Path, Path] | None:
    walk = dict(config.get("walk_forward_validation", {}))
    if not bool(walk.get("enabled", False)):
        return None
    result = run_walk_forward_soft_throttle(
        panel,
        alpha_registry,
        activator_registry,
        _walk_forward_config(config),
        diagnostic_frame,
        activator_masks,
    )
    return write_walk_forward_soft_throttle_reports(result, _report_dir(config))


def _shared_activator_masks(config: dict[str, Any], panel, activator_registry):
    soft = dict(config.get("soft_throttle", {}))
    walk = dict(config.get("walk_forward_validation", {}))
    if not bool(soft.get("enabled", False)) and not bool(walk.get("enabled", False)):
        return None
    compute = dict(config.get("compute", {}))
    return build_activator_masks(panel, activator_registry, int(compute.get("max_workers") or 1))


def _tail_failure_paths(config: dict[str, Any], walk_paths) -> tuple[Path, Path, Path, Path] | None:
    if walk_paths is None:
        return None
    paths = write_tail_failure_report(_report_dir(config))
    return paths.variant_diagnostics, paths.alpha_variant_diagnostics, paths.gate_diagnostics, paths.markdown


def _hypothesis_book_paths(config: dict[str, Any], tail_paths) -> tuple[Path, Path] | None:
    if tail_paths is None:
        return None
    paths = write_alpha_regime_hypothesis_book(_report_dir(config))
    return paths.hypotheses, paths.markdown


def _falsification_paths(config: dict[str, Any], book_paths) -> tuple[Path, Path] | None:
    if book_paths is None:
        return None
    paths = write_falsification_report(_report_dir(config))
    return paths.results, paths.markdown


def _weak_fold_event_paths(config: dict[str, Any], walk_paths) -> tuple[Path, Path] | None:
    if walk_paths is None:
        return None
    paths = write_weak_fold_event_report(_report_dir(config))
    return paths.weak_folds, paths.markdown


def _soft_throttle_config(config: dict[str, Any]) -> SoftThrottleConfig:
    diagnostics = _diagnostics_config(config)
    compute = dict(config.get("compute", {}))
    soft = dict(config.get("soft_throttle", {}))
    return SoftThrottleConfig(
        alpha_names=diagnostics.alpha_names,
        cache_dir=diagnostics.cache_dir,
        mode=diagnostics.mode,
        horizon=diagnostics.horizon,
        cost_bps=diagnostics.cost_bps,
        lookback_days=int(soft.get("lookback_days", diagnostics.lookback_days)),
        rolling_window_days=int(soft.get("rolling_window_days", 21)),
        top_quantile=diagnostics.top_quantile,
        bottom_quantile=diagnostics.bottom_quantile,
        threshold=diagnostics.threshold,
        min_names=diagnostics.min_names,
        max_workers=int(compute.get("max_workers") or 1),
        gpu=diagnostics.gpu,
    )


def _walk_forward_config(config: dict[str, Any]) -> WalkForwardThrottleConfig:
    diagnostics = _diagnostics_config(config)
    compute = dict(config.get("compute", {}))
    walk = dict(config.get("walk_forward_validation", {}))
    compute_workers = int(compute.get("max_workers") or 1)
    walk_workers = walk.get("max_workers")
    return WalkForwardThrottleConfig(
        alpha_names=diagnostics.alpha_names,
        cache_dir=diagnostics.cache_dir,
        mode=diagnostics.mode,
        horizon=diagnostics.horizon,
        cost_bps=diagnostics.cost_bps,
        lookback_days=int(walk.get("lookback_days", diagnostics.lookback_days)),
        rolling_window_days=int(walk.get("rolling_window_days", 21)),
        train_size_days=int(walk.get("train_size_days", 126)),
        test_size_days=int(walk.get("test_size_days", 21)),
        step_size_days=int(walk.get("step_size_days", 21)),
        lookahead_days=int(walk.get("lookahead_days", 10)),
        max_folds=int(walk.get("max_folds", 0)),
        fold_selection=str(walk.get("fold_selection", "earliest")),
        max_workers=int(walk_workers or compute_workers),
        top_quantile=diagnostics.top_quantile,
        bottom_quantile=diagnostics.bottom_quantile,
        threshold=diagnostics.threshold,
        min_names=diagnostics.min_names,
        gpu=diagnostics.gpu,
    )


def _load_panel(config: dict[str, Any]):
    universe = dict(config.get("universe", {}))
    source = str(universe.get("source", "market_collector_repository"))
    if source == "market_collector_native":
        return load_market_collector_native_panel_from_database(_database_path(config), _panel_request(config))
    return load_market_collector_panel_from_database(_database_path(config), _panel_request(config))


def _report_dir(config: dict[str, Any]) -> Path:
    compute = dict(config.get("compute", {}))
    return Path(str(compute.get("report_dir", "research/projects/price_action_strategy_lab/reports")))


if __name__ == "__main__":
    raise SystemExit(main())
