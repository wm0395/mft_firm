from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from project.data.market_collector_panel import MarketCollectorPanelRequest
from project.data.market_collector_panel import load_market_collector_native_panel_from_database
from project.data.market_collector_panel import load_market_collector_panel_from_database
from research.projects.price_action_strategy_lab.alpha_runner import AlphaSuiteConfig
from research.projects.price_action_strategy_lab.alpha_runner import run_alpha_suite
from research.projects.price_action_strategy_lab.alpha_runner import write_alpha_suite_reports
from research.projects.price_action_strategy_lab.alpha_specs import default_alpha_registry
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.validation_pipeline import SelectorHardeningConfig
from research.projects.price_action_strategy_lab.validation_pipeline import ValidationConfig
from research.projects.price_action_strategy_lab.universe_adapter import to_alpha101_panel


@dataclass(frozen=True)
class AlphaSuiteRunResult:
    report_dir: Path
    alpha_results_path: Path
    mode_comparison_path: Path
    alpha_mode_matrix_path: Path
    cache_events_path: Path
    run_summary_path: Path


def run_alpha_suite_config(config_path: str | Path) -> AlphaSuiteRunResult:
    config = _read_config(Path(config_path))
    panel = _load_panel(config)
    result = run_alpha_suite(
        to_alpha101_panel(panel),
        default_alpha_registry(),
        _suite_config(config),
    )
    paths = write_alpha_suite_reports(result, _report_dir(config))
    return AlphaSuiteRunResult(_report_dir(config), paths[0], paths[1], paths[2], paths[3], paths[4])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    result = run_alpha_suite_config(args.config)
    print(f"wrote alpha suite reports to {result.report_dir}")
    return 0


def _read_config(path: Path) -> dict[str, Any]:
    return dict(yaml.safe_load(path.read_text(encoding="utf-8")))


def _database_path(config: dict[str, Any]) -> Path:
    universe = dict(config.get("universe", {}))
    return Path(str(universe.get("database_path", "project_mft.duckdb")))


def _panel_request(config: dict[str, Any]) -> MarketCollectorPanelRequest:
    universe = dict(config.get("universe", {}))
    return MarketCollectorPanelRequest(
        name=str(universe.get("name", "market_collector_nse")),
        exchange=str(universe.get("exchange", "NSE")),
        symbol_suffix=str(universe.get("symbol_suffix", "")),
        start_timestamp=_timestamp(universe.get("start_date")),
        end_timestamp=_timestamp(universe.get("end_date")),
        min_history_days=int(universe.get("min_history_days", 60)),
        max_missing_ratio=float(universe.get("max_missing_ratio", 0.25)),
    )


def _load_panel(config: dict[str, Any]):
    universe = dict(config.get("universe", {}))
    source = str(universe.get("source", "market_collector_repository"))
    if source == "market_collector_native":
        return load_market_collector_native_panel_from_database(
            _database_path(config),
            _panel_request(config),
        )
    return load_market_collector_panel_from_database(_database_path(config), _panel_request(config))


def _suite_config(config: dict[str, Any]) -> AlphaSuiteConfig:
    backtests = dict(config.get("backtests", {}))
    compute = dict(config.get("compute", {}))
    gpu = dict(config.get("gpu", {}))
    validation = dict(config.get("validation", {}))
    hardening = dict(config.get("selector_hardening", {}))
    return AlphaSuiteConfig(
        alpha_names=tuple(config.get("alphas", ())),
        modes=tuple(config.get("expression_modes", ())),
        horizons=tuple(int(item) for item in backtests.get("horizons", (5,))),
        cost_bps=tuple(float(item) for item in backtests.get("turnover_cost_bps", (10.0,))),
        cache_dir=Path(str(compute.get("cache_dir", ".cache/price_action_alpha_suite"))),
        max_workers=int(compute.get("max_workers", 1)),
        min_names=int(backtests.get("min_active_names", 1)),
        top_quantile=float(backtests.get("top_quantile", 0.8)),
        bottom_quantile=float(backtests.get("bottom_quantile", 0.2)),
        threshold=float(backtests.get("threshold", 0.0)),
        gpu=GpuConfig(
            enabled=bool(gpu.get("enabled", False)),
            backend=str(gpu.get("backend") or "auto"),
        ),
        validation=ValidationConfig(
            enabled=bool(validation.get("enabled", False)),
            schemes=tuple(validation.get("schemes", ("walk_forward", "purged", "embargo"))),
            outer_folds=int(validation.get("outer_folds", 6)),
            train_size=int(validation.get("train_size", 756)),
            test_size=int(validation.get("test_size", 63)),
            step_size=(
                int(validation["step_size"])
                if validation.get("step_size") not in {None, ""}
                else None
            ),
            lookahead=int(validation.get("lookahead", 10)),
            embargo=int(validation.get("embargo", 10)),
            bootstrap_reps=int(validation.get("bootstrap_reps", 1000)),
            bootstrap_block_length=int(validation.get("bootstrap_block_length", 10)),
            target_cost_bps=float(validation.get("target_cost_bps", 10.0)),
            min_active_days=int(validation.get("min_active_days", 40)),
        ),
        selector_hardening=SelectorHardeningConfig(
            lower_bound_margin_bps=float(hardening.get("lower_bound_margin_bps", 0.0)),
            turnover_penalty_bps=float(hardening.get("turnover_penalty_bps", 25.0)),
            instability_penalty_bps=float(hardening.get("instability_penalty_bps", 1.0)),
            minimum_fold_pass_rate=float(hardening.get("minimum_fold_pass_rate", 0.5)),
            abstain_lower_bound_bps=float(hardening.get("abstain_lower_bound_bps", 0.0)),
            primary_scheme=str(hardening.get("primary_scheme", "embargo")),
        ),
    )


def _report_dir(config: dict[str, Any]) -> Path:
    compute = dict(config.get("compute", {}))
    return Path(str(compute.get("report_dir", "research/projects/price_action_strategy_lab/reports")))


def _timestamp(value: object) -> datetime | None:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


if __name__ == "__main__":
    raise SystemExit(main())
