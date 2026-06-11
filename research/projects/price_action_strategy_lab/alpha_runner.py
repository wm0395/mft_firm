from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from dataclasses import field
from hashlib import sha256
from pathlib import Path

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.notebooks.alpha_001.research.alpha101_engine import forward_return
from research.projects.price_action_strategy_lab.alpha_registry import AlphaRegistry
from research.projects.price_action_strategy_lab.alpha_registry import AlphaSpec
from research.projects.price_action_strategy_lab.backtest_modes import BacktestConfig
from research.projects.price_action_strategy_lab.backtest_modes import summarize_backtest
from research.projects.price_action_strategy_lab.backtest_modes import run_backtest
from research.projects.price_action_strategy_lab.costs import turnover_cost
from research.projects.price_action_strategy_lab.compute_backend import ComputeBackend
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.compute_backend import build_rank_pct
from research.projects.price_action_strategy_lab.compute_backend import resolve_compute_backend
from research.projects.price_action_strategy_lab.validation_pipeline import ValidationArtifacts
from research.projects.price_action_strategy_lab.validation_pipeline import ValidationConfig
from research.projects.price_action_strategy_lab.validation_pipeline import SelectorHardeningConfig
from research.projects.price_action_strategy_lab.validation_pipeline import SignalBundle
from research.projects.price_action_strategy_lab.validation_pipeline import run_validation_suite
from research.projects.price_action_strategy_lab.validation_reports import write_validation_reports


@dataclass(frozen=True)
class AlphaSuiteConfig:
    alpha_names: tuple[str, ...]
    modes: tuple[str, ...]
    horizons: tuple[int, ...]
    cost_bps: tuple[float, ...]
    cache_dir: Path
    max_workers: int = 1
    min_names: int = 1
    top_quantile: float = 0.8
    bottom_quantile: float = 0.2
    threshold: float = 0.0
    gpu: GpuConfig = field(default_factory=GpuConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    selector_hardening: SelectorHardeningConfig = field(default_factory=SelectorHardeningConfig)


@dataclass(frozen=True)
class AlphaSuiteResult:
    rows: pd.DataFrame
    mode_comparison: pd.DataFrame
    cache_events: pd.DataFrame
    compute_backend: str
    validation: ValidationArtifacts = field(default_factory=ValidationArtifacts.empty)


@dataclass(frozen=True)
class _CachedSignal:
    alpha_name: str
    signal: pd.DataFrame
    rank_pct: pd.DataFrame
    cache_key: str
    signal_cache_path: Path
    rank_cache_path: Path
    cache_hit: bool
    rank_cache_hit: bool
    backend: str


def run_alpha_suite(
    panel: Alpha101Panel,
    registry: AlphaRegistry,
    config: AlphaSuiteConfig,
) -> AlphaSuiteResult:
    backend = resolve_compute_backend(config.gpu)
    specs = _selected_specs(registry, config.alpha_names)
    cached = _cached_signals(panel, specs, config.cache_dir, backend, config.max_workers)
    rows = _run_jobs(panel, cached, config)
    frame = pd.DataFrame(rows).sort_values(["alpha", "mode", "horizon", "cost_bps"])
    validation = run_validation_suite(
        panel,
        _validation_bundles(cached),
        frame,
        config.validation,
        config.selector_hardening,
        config.max_workers,
    )
    return AlphaSuiteResult(
        rows=frame.reset_index(drop=True),
        mode_comparison=_mode_comparison(frame),
        cache_events=_cache_events(cached),
        compute_backend=backend.name,
        validation=validation,
    )


def load_signal_bundles(
    panel: Alpha101Panel,
    registry: AlphaRegistry,
    alpha_names: tuple[str, ...],
    cache_dir: Path,
    gpu: GpuConfig,
    max_workers: int = 1,
) -> tuple[SignalBundle, ...]:
    backend = resolve_compute_backend(gpu)
    specs = _selected_specs(registry, alpha_names)
    cached = _cached_signals(panel, specs, cache_dir, backend, max_workers)
    return _validation_bundles(cached)


def write_alpha_suite_reports(
    result: AlphaSuiteResult,
    report_dir: Path,
) -> tuple[Path, Path, Path, Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    alpha_path = report_dir / "alpha_results.csv"
    mode_path = report_dir / "mode_comparison.csv"
    matrix_path = report_dir / "alpha_mode_matrix.csv"
    cache_path = report_dir / "cache_events.csv"
    summary_path = report_dir / "run_summary.md"
    result.rows.to_csv(alpha_path, index=False)
    result.mode_comparison.to_csv(mode_path, index=False)
    _alpha_mode_matrix(result.rows).to_csv(matrix_path)
    result.cache_events.to_csv(cache_path, index=False)
    if not result.validation.summary.empty:
        write_validation_reports(report_dir, result.validation)
    summary_path.write_text(_summary(result), encoding="utf-8")
    return alpha_path, mode_path, matrix_path, cache_path, summary_path


def _selected_specs(
    registry: AlphaRegistry,
    alpha_names: tuple[str, ...],
) -> tuple[AlphaSpec, ...]:
    names = alpha_names or tuple(spec.name for spec in registry.specs)
    missing = [name for name in names if name not in registry.by_name]
    if missing:
        raise KeyError(f"unknown alpha specs: {missing}")
    return tuple(registry.by_name[name] for name in names)


def _cached_signals(
    panel: Alpha101Panel,
    specs: tuple[AlphaSpec, ...],
    cache_dir: Path,
    backend: ComputeBackend,
    max_workers: int,
) -> list[_CachedSignal]:
    workers = max(1, int(max_workers))
    if workers == 1 or len(specs) == 1:
        return [_cached_signal(panel, spec, cache_dir, backend) for spec in specs]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(lambda spec: _cached_signal(panel, spec, cache_dir, backend), specs))


def _cached_signal(
    panel: Alpha101Panel,
    spec: AlphaSpec,
    cache_dir: Path,
    backend: ComputeBackend,
) -> _CachedSignal:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = _signal_cache_key(panel, spec)
    signal_path = cache_dir / "signals" / f"{cache_key}.pkl"
    rank_path = cache_dir / "rank_pct" / backend.name / f"{cache_key}.pkl"
    signal_path.parent.mkdir(parents=True, exist_ok=True)
    rank_path.parent.mkdir(parents=True, exist_ok=True)
    if signal_path.exists():
        signal = pd.read_pickle(signal_path)
        signal_hit = True
    else:
        signal = spec.builder(panel).where(panel.active_mask)
        signal.to_pickle(signal_path)
        signal_hit = False
    if rank_path.exists():
        rank_pct = pd.read_pickle(rank_path)
        rank_hit = True
    else:
        rank_pct = build_rank_pct(signal, backend)
        rank_pct.to_pickle(rank_path)
        rank_hit = False
    return _CachedSignal(
        spec.name,
        signal,
        rank_pct,
        cache_key,
        signal_path,
        rank_path,
        signal_hit,
        rank_hit,
        backend.name,
    )


def _validation_bundles(cached: list[_CachedSignal]) -> tuple[SignalBundle, ...]:
    return tuple(
        SignalBundle(
            alpha=item.alpha_name,
            signal=item.signal,
            rank_pct=item.rank_pct,
            backend=item.backend,
        )
        for item in cached
    )


def _signal_cache_key(panel: Alpha101Panel, spec: AlphaSpec) -> str:
    payload = "|".join(
        [
            panel.name,
            spec.name,
            str(panel.close.index.min()),
            str(panel.close.index.max()),
            str(panel.close.shape),
            str(tuple(panel.close.columns)),
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()[:24]


def _run_jobs(
    panel: Alpha101Panel,
    cached: list[_CachedSignal],
    config: AlphaSuiteConfig,
) -> list[dict[str, float | int | str]]:
    jobs = [
        (item, mode, horizon, cost)
        for item in cached
        for mode in config.modes
        for horizon in config.horizons
        for cost in config.cost_bps
    ]
    workers = max(1, int(config.max_workers))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(lambda job: _run_job(panel, config, job), jobs))


def _run_job(
    panel: Alpha101Panel,
    config: AlphaSuiteConfig,
    job: tuple[_CachedSignal, str, int, float],
) -> dict[str, float | int | str]:
    cached, mode, horizon, cost = job
    path = _backtest_cache_path(cached, config, mode, horizon, cost)
    if path.exists():
        row = dict(pd.read_pickle(path))
        row.setdefault("compute_backend", cached.backend)
        return dict(row, backtest_cache_hit=True)
    future = forward_return(panel.close, horizon)
    bt_config = BacktestConfig(
        name=f"{cached.alpha_name}:{mode}:{horizon}d:{cost:g}bps",
        mode=mode,
        horizon=horizon,
        cost_model=turnover_cost(cost),
        top_quantile=config.top_quantile,
        bottom_quantile=config.bottom_quantile,
        threshold=config.threshold,
        min_names=config.min_names,
    )
    summary = summarize_backtest(
        run_backtest(cached.signal, future, bt_config, panel.active_mask, cached.rank_pct)
    )
    row = {
        "alpha": cached.alpha_name,
        "cost_bps": cost,
        "compute_backend": cached.backend,
        **summary,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.to_pickle(row, path)
    return dict(row, backtest_cache_hit=False)


def _backtest_cache_path(
    cached: _CachedSignal,
    config: AlphaSuiteConfig,
    mode: str,
    horizon: int,
    cost: float,
) -> Path:
    parts = [
        cached.cache_key,
        mode,
        str(horizon),
        f"{cost:g}",
        f"{config.top_quantile:g}",
        f"{config.bottom_quantile:g}",
        f"{config.threshold:g}",
        str(config.min_names),
    ]
    if cached.backend != "cpu":
        parts.insert(1, cached.backend)
    digest = sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
    return config.cache_dir / "backtests" / f"{digest}.pkl"


def _mode_comparison(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby(["mode", "horizon", "cost_bps"], as_index=False)
    return grouped.agg(
        alpha_count=("alpha", "nunique"),
        mean_net_bps=("net_mean_bps", "mean"),
        median_net_bps=("net_mean_bps", "median"),
        mean_turnover=("turnover", "mean"),
        mean_coverage=("coverage", "mean"),
    )


def _alpha_mode_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.pivot_table(
        index="alpha",
        columns="mode",
        values="net_mean_bps",
        aggfunc="mean",
    )


def _cache_events(cached: list[_CachedSignal]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "alpha": item.alpha_name,
                "cache_hit": item.cache_hit,
                "rank_cache_hit": item.rank_cache_hit,
                "backend": item.backend,
                "signal_cache_path": str(item.signal_cache_path),
                "rank_cache_path": str(item.rank_cache_path),
            }
            for item in cached
        ]
    )


def _summary(result: AlphaSuiteResult) -> str:
    hits = int(result.cache_events["cache_hit"].sum()) if not result.cache_events.empty else 0
    rank_hits = (
        int(result.cache_events["rank_cache_hit"].sum()) if not result.cache_events.empty else 0
    )
    backend = result.compute_backend
    validation_rows = len(result.validation.summary)
    decision = (
        str(result.validation.decision.iloc[0]["decision"])
        if not result.validation.decision.empty
        else "research_only"
    )
    return "\n".join(
        [
            "# Alpha Suite Run",
            "",
            f"- alpha rows: {len(result.rows)}",
            f"- signal cache hits: {hits}/{len(result.cache_events)}",
            f"- rank cache hits: {rank_hits}/{len(result.cache_events)}",
            f"- compute backend: {backend}",
            f"- validation rows: {validation_rows}",
            f"- decision: {decision}",
            "- expression modes compared in `mode_comparison.csv`",
        ]
    )
