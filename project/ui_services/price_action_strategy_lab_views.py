from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml  # type: ignore[import-untyped]

from project.data.market_collector_panel import (
    MarketCollectorPanelRequest,
    load_market_collector_native_panel_from_database,
    load_market_collector_panel_from_database,
)
from research.projects.price_action_strategy_lab.universe_adapter import to_alpha101_panel


ROOT_DIR = Path(__file__).resolve().parents[2]
RESEARCH_ROOT = ROOT_DIR / "research/projects/price_action_strategy_lab"
REPORTS_ROOT = RESEARCH_ROOT / "reports"
CONFIGS_ROOT = RESEARCH_ROOT / "configs"


@dataclass(frozen=True)
class PriceActionStrategyLabUniverseConfig:
    name: str
    source: str
    database_path: Path
    exchange: str
    symbol_suffix: str
    timeframe: str
    start_timestamp: datetime | None
    end_timestamp: datetime | None
    min_history_days: int
    max_missing_ratio: float
    require_ohlcv: bool


@dataclass(frozen=True)
class PriceActionStrategyLabBacktestConfig:
    horizons: tuple[int, ...]
    turnover_cost_bps: tuple[float, ...]
    min_active_names: int
    threshold: float
    top_quantile: float
    bottom_quantile: float


@dataclass(frozen=True)
class PriceActionStrategyLabComputeConfig:
    cache_dir: Path
    report_dir: Path
    max_workers: int


@dataclass(frozen=True)
class PriceActionStrategyLabSuiteConfig:
    universe: PriceActionStrategyLabUniverseConfig
    alpha_names: tuple[str, ...]
    expression_modes: tuple[str, ...]
    backtests: PriceActionStrategyLabBacktestConfig
    compute: PriceActionStrategyLabComputeConfig


@dataclass(frozen=True)
class PriceActionStrategyLabResultRow:
    alpha: str
    cost_bps: float
    name: str
    mode: str
    horizon: int
    obs: int
    active_days: int
    coverage: float
    gross_mean_bps: float
    net_mean_bps: float
    turnover: float
    win_rate: float
    backtest_cache_hit: bool


@dataclass(frozen=True)
class PriceActionStrategyLabModeComparisonRow:
    mode: str
    horizon: int
    cost_bps: float
    alpha_count: int
    mean_net_bps: float
    median_net_bps: float
    mean_turnover: float
    mean_coverage: float


@dataclass(frozen=True)
class PriceActionStrategyLabCacheEventRow:
    alpha: str
    cache_hit: bool
    cache_path: Path


@dataclass(frozen=True)
class PriceActionStrategyLabRun:
    name: str
    report_dir: Path
    config_path: Path
    config: PriceActionStrategyLabSuiteConfig
    summary_text: str
    alpha_results: tuple[PriceActionStrategyLabResultRow, ...]
    mode_comparison: tuple[PriceActionStrategyLabModeComparisonRow, ...]
    cache_events: tuple[PriceActionStrategyLabCacheEventRow, ...]
    modified_at: datetime


def list_price_action_strategy_lab_runs() -> tuple[PriceActionStrategyLabRun, ...]:
    runs = tuple(load_price_action_strategy_lab_run(path) for path in _report_dirs())
    return tuple(sorted(runs, key=lambda run: run.modified_at, reverse=True))


def load_price_action_strategy_lab_run(report_dir: Path) -> PriceActionStrategyLabRun:
    config_path = _config_path(report_dir)
    return PriceActionStrategyLabRun(
        name=report_dir.name,
        report_dir=report_dir,
        config_path=config_path,
        config=_read_config(config_path),
        summary_text=_read_text(report_dir / "run_summary.md"),
        alpha_results=_result_rows(report_dir / "alpha_results.csv"),
        mode_comparison=_mode_rows(report_dir / "mode_comparison.csv"),
        cache_events=_cache_rows(report_dir / "cache_events.csv"),
        modified_at=_modified_at(report_dir),
    )


def load_price_action_strategy_lab_panel(
    run: PriceActionStrategyLabRun,
    *,
    symbols: tuple[str, ...] = (),
):
    request = _panel_request(run.config, symbols=symbols)
    database_path = run.config.universe.database_path
    loader = (
        load_market_collector_native_panel_from_database
        if run.config.universe.source == "market_collector_native"
        else load_market_collector_panel_from_database
    )
    return to_alpha101_panel(loader(database_path, request))


def load_price_action_strategy_lab_chart_rows(
    run: PriceActionStrategyLabRun,
    symbol: str,
) -> tuple[tuple[datetime, float, float, float, float, float], ...]:
    panel = load_price_action_strategy_lab_panel(run, symbols=(symbol,))
    if symbol not in panel.close.columns:
        raise ValueError(f"missing chart data for {symbol}")
    rows = []
    for timestamp, close in panel.close[symbol].dropna().items():
        values = (
            panel.open.at[timestamp, symbol],
            panel.high.at[timestamp, symbol],
            panel.low.at[timestamp, symbol],
            close,
            panel.volume.at[timestamp, symbol],
        )
        if any(pd.isna(value) for value in values):
            continue
        rows.append(
            (
                pd.Timestamp(timestamp).to_pydatetime(),
                float(values[0]),
                float(values[1]),
                float(values[2]),
                float(values[3]),
                float(values[4]),
            )
        )
    return tuple(rows)


def load_price_action_strategy_lab_signal(
    run: PriceActionStrategyLabRun,
    alpha_name: str,
) -> pd.DataFrame:
    path = _signal_cache_path(run, alpha_name)
    if path is None:
        raise ValueError(f"missing cached signal for {alpha_name}")
    return pd.read_pickle(path)


def load_price_action_strategy_lab_validation_summary(run: PriceActionStrategyLabRun) -> pd.DataFrame:
    path = run.report_dir / "validation_summary.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_price_action_strategy_lab_report_text(run: PriceActionStrategyLabRun, name: str) -> str:
    path = run.report_dir / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def top_signal_symbols(
    run: PriceActionStrategyLabRun,
    alpha_name: str,
    limit: int = 25,
) -> tuple[str, ...]:
    signal = load_price_action_strategy_lab_signal(run, alpha_name)
    if signal.empty:
        return ()
    scores = signal.abs().max(axis=0).dropna().sort_values(ascending=False)
    return tuple(str(symbol) for symbol in scores.head(limit).index)


def _report_dirs() -> tuple[Path, ...]:
    if not REPORTS_ROOT.exists():
        return ()
    report_dirs = [
        path
        for path in REPORTS_ROOT.iterdir()
        if path.is_dir() and path.name.endswith("_alpha_suite")
        and _config_path(path).exists()
    ]
    return tuple(report_dirs)


def _config_path(report_dir: Path) -> Path:
    return (CONFIGS_ROOT / f"{report_dir.name}.yaml").resolve()


def _signal_cache_path(run: PriceActionStrategyLabRun, alpha_name: str) -> Path | None:
    for row in run.cache_events:
        if row.alpha == alpha_name:
            return row.cache_path
    return None


def _read_config(path: Path) -> PriceActionStrategyLabSuiteConfig:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("price action strategy lab config must be a mapping")
    return PriceActionStrategyLabSuiteConfig(
        universe=_universe_config(payload),
        alpha_names=_string_tuple(payload.get("alphas", ())),
        expression_modes=_string_tuple(payload.get("expression_modes", ())),
        backtests=_backtest_config(payload),
        compute=_compute_config(payload),
    )


def _universe_config(payload: dict[str, Any]) -> PriceActionStrategyLabUniverseConfig:
    universe = dict(payload.get("universe", {}))
    return PriceActionStrategyLabUniverseConfig(
        name=str(universe.get("name", "market_collector_nse")),
        source=str(universe.get("source", "market_collector_repository")),
        database_path=_resolve_path(universe.get("database_path", "project_mft.duckdb")),
        exchange=str(universe.get("exchange", "")),
        symbol_suffix=str(universe.get("symbol_suffix", "")),
        timeframe=str(universe.get("timeframe", "1d")),
        start_timestamp=_timestamp(universe.get("start_date")),
        end_timestamp=_timestamp(universe.get("end_date")),
        min_history_days=int(universe.get("min_history_days", 60)),
        max_missing_ratio=float(universe.get("max_missing_ratio", 0.25)),
        require_ohlcv=bool(universe.get("require_ohlcv", True)),
    )


def _backtest_config(payload: dict[str, Any]) -> PriceActionStrategyLabBacktestConfig:
    backtests = dict(payload.get("backtests", {}))
    return PriceActionStrategyLabBacktestConfig(
        horizons=tuple(int(item) for item in backtests.get("horizons", ())),
        turnover_cost_bps=tuple(float(item) for item in backtests.get("turnover_cost_bps", ())),
        min_active_names=int(backtests.get("min_active_names", 1)),
        threshold=float(backtests.get("threshold", 0.0)),
        top_quantile=float(backtests.get("top_quantile", 0.8)),
        bottom_quantile=float(backtests.get("bottom_quantile", 0.2)),
    )


def _compute_config(payload: dict[str, Any]) -> PriceActionStrategyLabComputeConfig:
    compute = dict(payload.get("compute", {}))
    return PriceActionStrategyLabComputeConfig(
        cache_dir=_resolve_path(compute.get("cache_dir", ".cache/price_action_alpha_suite")),
        report_dir=_resolve_path(
            compute.get("report_dir", "research/projects/price_action_strategy_lab/reports")
        ),
        max_workers=int(compute.get("max_workers", 1)),
    )


def _result_rows(path: Path) -> tuple[PriceActionStrategyLabResultRow, ...]:
    if not path.exists():
        return ()
    frame = pd.read_csv(path)
    return tuple(_result_row(row) for row in frame.itertuples(index=False))


def _mode_rows(path: Path) -> tuple[PriceActionStrategyLabModeComparisonRow, ...]:
    if not path.exists():
        return ()
    frame = pd.read_csv(path)
    return tuple(_mode_row(row) for row in frame.itertuples(index=False))


def _cache_rows(path: Path) -> tuple[PriceActionStrategyLabCacheEventRow, ...]:
    if not path.exists():
        return ()
    frame = pd.read_csv(path)
    return tuple(_cache_row(row) for row in frame.itertuples(index=False))


def _result_row(row) -> PriceActionStrategyLabResultRow:
    return PriceActionStrategyLabResultRow(
        alpha=str(row.alpha),
        cost_bps=float(row.cost_bps),
        name=str(row.name),
        mode=str(row.mode),
        horizon=int(row.horizon),
        obs=int(row.obs),
        active_days=int(row.active_days),
        coverage=float(row.coverage),
        gross_mean_bps=float(row.gross_mean_bps),
        net_mean_bps=float(row.net_mean_bps),
        turnover=float(row.turnover),
        win_rate=float(row.win_rate),
        backtest_cache_hit=_parse_bool(row.backtest_cache_hit),
    )


def _mode_row(row) -> PriceActionStrategyLabModeComparisonRow:
    return PriceActionStrategyLabModeComparisonRow(
        mode=str(row.mode),
        horizon=int(row.horizon),
        cost_bps=float(row.cost_bps),
        alpha_count=int(row.alpha_count),
        mean_net_bps=float(row.mean_net_bps),
        median_net_bps=float(row.median_net_bps),
        mean_turnover=float(row.mean_turnover),
        mean_coverage=float(row.mean_coverage),
    )


def _cache_row(row) -> PriceActionStrategyLabCacheEventRow:
    return PriceActionStrategyLabCacheEventRow(
        alpha=str(row.alpha),
        cache_hit=_parse_bool(row.cache_hit),
        cache_path=_resolve_path(row.cache_path),
    )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _modified_at(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)


def _resolve_path(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else (ROOT_DIR / path).resolve()


def _panel_request(
    config: PriceActionStrategyLabSuiteConfig,
    *,
    symbols: tuple[str, ...] = (),
) -> MarketCollectorPanelRequest:
    universe = config.universe
    return MarketCollectorPanelRequest(
        name=universe.name,
        exchange=universe.exchange,
        symbol_suffix=universe.symbol_suffix,
        symbols=symbols,
        start_timestamp=universe.start_timestamp,
        end_timestamp=universe.end_timestamp,
        min_history_days=universe.min_history_days,
        max_missing_ratio=universe.max_missing_ratio,
    )


def _timestamp(value: object) -> datetime | None:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _string_tuple(values: object) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        return ()
    return tuple(str(value) for value in values)


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}
