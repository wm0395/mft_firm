from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel, forward_return
from research.projects.price_action_strategy_lab.activator_registry import ActivatorRegistry
from research.projects.price_action_strategy_lab.activator_specs import ALPHA_FAMILY_ACTIVATORS, build_shared_activator_masks
from research.projects.price_action_strategy_lab.alpha_registry import AlphaRegistry
from research.projects.price_action_strategy_lab.backtest_modes import BacktestConfig, run_backtest, summarize_backtest
from research.projects.price_action_strategy_lab.costs import turnover_cost
from research.projects.price_action_strategy_lab.alpha_runner import load_signal_bundles
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.validation_pipeline import SignalBundle

SELECTION_COLUMNS = (
    "family", "selected_activator", "mean_lift_bps", "mean_gated_net_bps",
    "mean_activation_corr", "mean_activation_coverage", "rows", "decision",
)


@dataclass(frozen=True)
class ActivatorSuiteConfig:
    alpha_names: tuple[str, ...]
    modes: tuple[str, ...]
    horizons: tuple[int, ...]
    cost_bps: tuple[float, ...]
    cache_dir: Path
    report_dir: Path
    screen_mode: str = "ranked_long_only"
    screen_horizon: int = 10
    screen_cost_bps: float = 10.0
    min_names: int = 1
    top_quantile: float = 0.8
    bottom_quantile: float = 0.2
    threshold: float = 0.0
    min_lift_bps: float = 0.0
    gpu: GpuConfig = field(default_factory=GpuConfig)
    max_workers: int = 1


@dataclass(frozen=True)
class ActivatorSuiteResult:
    screen_results: pd.DataFrame
    selection: pd.DataFrame
    backtest_results: pd.DataFrame
    compute_backend: str


@dataclass(frozen=True)
class BacktestSnapshot:
    summary: dict[str, float | int | str]
    net_return: pd.Series


def run_activator_suite(
    panel: Alpha101Panel,
    alpha_registry: AlphaRegistry,
    activator_registry: ActivatorRegistry,
    config: ActivatorSuiteConfig,
) -> ActivatorSuiteResult:
    bundles = load_signal_bundles(
        panel,
        alpha_registry,
        config.alpha_names,
        config.cache_dir,
        config.gpu,
        config.max_workers,
    )
    activator_masks = build_activator_masks(panel, activator_registry, config.max_workers)
    futures = {horizon: forward_return(panel.close, horizon) for horizon in config.horizons}
    baseline = _baseline_snapshots(panel, bundles, futures, config)
    screen = _screen_results(panel, bundles, alpha_registry, activator_masks, baseline, futures, config)
    selection = select_family_activators(screen, config.min_lift_bps)
    backtests = _family_backtests(
        panel,
        bundles,
        alpha_registry,
        activator_masks,
        baseline,
        futures,
        selection,
        config,
    )
    backend = bundles[0].backend if bundles else "cpu"
    return ActivatorSuiteResult(screen, selection, backtests, backend)


def build_activator_masks(
    panel: Alpha101Panel,
    registry: ActivatorRegistry,
    max_workers: int = 1,
) -> dict[str, pd.DataFrame]:
    specs = tuple(registry.specs)
    masks = build_shared_activator_masks(panel, tuple(spec.name for spec in specs))
    missing = tuple(spec for spec in specs if spec.name not in masks)
    if not missing:
        return masks
    workers = max(1, int(max_workers))
    active = panel.active_mask.fillna(False)
    if workers == 1 or len(missing) == 1:
        rows = [_build_mask_row(panel, active, spec) for spec in missing]
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            rows = list(executor.map(lambda spec: _build_mask_row(panel, active, spec), missing))
    masks.update(dict(rows))
    return masks


def _build_mask_row(panel: Alpha101Panel, active: pd.DataFrame, spec) -> tuple[str, pd.DataFrame]:
    mask = spec.builder(panel).reindex_like(active).fillna(False)
    return spec.name, mask & active


def select_family_activators(screen: pd.DataFrame, min_lift_bps: float = 0.0) -> pd.DataFrame:
    if screen.empty:
        return pd.DataFrame(columns=SELECTION_COLUMNS)
    screen = screen.dropna(subset=["lift_bps", "gated_net_mean_bps"], how="all")
    if screen.empty:
        return pd.DataFrame(columns=SELECTION_COLUMNS)
    grouped = screen.groupby(["family", "activator"], as_index=False).agg(
        mean_lift_bps=("lift_bps", "mean"),
        mean_gated_net_bps=("gated_net_mean_bps", "mean"),
        mean_activation_corr=("activation_corr", "mean"),
        mean_activation_coverage=("activation_coverage", "mean"),
        rows=("alpha", "count"),
    )
    chosen = grouped.sort_values(
        ["family", "mean_lift_bps", "mean_gated_net_bps"],
        ascending=[True, False, False],
    ).groupby("family", as_index=False).first()
    chosen["decision"] = chosen.apply(
        lambda row: "activate"
        if float(row["mean_lift_bps"]) > min_lift_bps and float(row["mean_gated_net_bps"]) > 0.0
        else "abstain",
        axis=1,
    )
    chosen["selected_activator"] = chosen["activator"].where(chosen["decision"].eq("activate"), "none")
    chosen["_decision_rank"] = chosen["decision"].map({"activate": 0, "abstain": 1}).fillna(2)
    return chosen[list(SELECTION_COLUMNS)].assign(_decision_rank=chosen["_decision_rank"]).sort_values(
        ["_decision_rank", "mean_lift_bps"], ascending=[True, False]
    ).drop(columns="_decision_rank")


def write_activator_suite_reports(
    result: ActivatorSuiteResult,
    report_dir: Path,
) -> tuple[Path, Path, Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    screen_path = report_dir / "activator_screen.csv"
    selection_path = report_dir / "activator_selection.csv"
    backtests_path = report_dir / "activator_backtests.csv"
    summary_path = report_dir / "run_summary.md"
    result.screen_results.to_csv(screen_path, index=False)
    result.selection.to_csv(selection_path, index=False)
    result.backtest_results.to_csv(backtests_path, index=False)
    summary_path.write_text(_summary_md(result), encoding="utf-8")
    return screen_path, selection_path, backtests_path, summary_path


def _baseline_snapshots(
    panel: Alpha101Panel,
    bundles: tuple[SignalBundle, ...],
    futures: dict[int, pd.DataFrame],
    config: ActivatorSuiteConfig,
) -> dict[tuple[str, str, int, float], BacktestSnapshot]:
    snapshots: dict[tuple[str, str, int, float], BacktestSnapshot] = {}
    for bundle in bundles:
        for mode in config.modes:
            for horizon in config.horizons:
                for cost in config.cost_bps:
                    snapshots[(bundle.alpha, mode, horizon, cost)] = _run_snapshot(
                        bundle.signal,
                        futures[horizon],
                        bundle.rank_pct,
                        panel.active_mask,
                        mode,
                        horizon,
                        cost,
                        config,
                    )
    return snapshots


def _screen_results(
    panel: Alpha101Panel,
    bundles: tuple[SignalBundle, ...],
    registry: AlphaRegistry,
    activator_masks: dict[str, pd.DataFrame],
    baseline: dict[tuple[str, str, int, float], BacktestSnapshot],
    futures: dict[int, pd.DataFrame],
    config: ActivatorSuiteConfig,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for bundle in bundles:
        family = registry.by_name[bundle.alpha].family
        for activator_name in ALPHA_FAMILY_ACTIVATORS.get(family, ()):
            if activator_name not in activator_masks:
                continue
            gated_mask = panel.active_mask & activator_masks[activator_name]
            gated = _run_snapshot(
                bundle.signal,
                futures[config.screen_horizon],
                bundle.rank_pct,
                gated_mask,
                config.screen_mode,
                config.screen_horizon,
                config.screen_cost_bps,
                config,
            )
            base = baseline[(bundle.alpha, config.screen_mode, config.screen_horizon, config.screen_cost_bps)]
            rows.append(
                _pair_row(
                    alpha=bundle.alpha,
                    family=family,
                    activator=activator_name,
                    mode=config.screen_mode,
                    horizon=config.screen_horizon,
                    cost_bps=config.screen_cost_bps,
                    baseline=base,
                    gated=gated,
                    activator_mask=activator_masks[activator_name],
                )
            )
    return pd.DataFrame(rows)


def _family_backtests(
    panel: Alpha101Panel,
    bundles: tuple[SignalBundle, ...],
    registry: AlphaRegistry,
    activator_masks: dict[str, pd.DataFrame],
    baseline: dict[tuple[str, str, int, float], BacktestSnapshot],
    futures: dict[int, pd.DataFrame],
    selection: pd.DataFrame,
    config: ActivatorSuiteConfig,
) -> pd.DataFrame:
    selected = dict(zip(selection["family"], selection["selected_activator"], strict=False))
    screen_corr = dict(zip(selection["family"], selection["mean_activation_corr"], strict=False))
    rows: list[dict[str, object]] = []
    for bundle in bundles:
        family = registry.by_name[bundle.alpha].family
        activator_name = selected.get(family, "none")
        for mode in config.modes:
            for horizon in config.horizons:
                for cost in config.cost_bps:
                    base = baseline[(bundle.alpha, mode, horizon, cost)]
                    if activator_name != "none":
                        gated = _run_snapshot(
                            bundle.signal,
                            futures[horizon],
                            bundle.rank_pct,
                            panel.active_mask & activator_masks[activator_name],
                            mode,
                            horizon,
                            cost,
                            config,
                        )
                    else:
                        gated = base
                    rows.append(
                        _pair_row(
                            alpha=bundle.alpha,
                            family=family,
                            activator=activator_name,
                            mode=mode,
                            horizon=horizon,
                            cost_bps=cost,
                            baseline=base,
                            gated=gated,
                            activator_mask=activator_masks.get(activator_name, panel.active_mask),
                            activation_corr=float(screen_corr.get(family, 0.0)),
                            decision="activate" if activator_name != "none" else "abstain",
                        )
                    )
    return pd.DataFrame(rows)


def _run_snapshot(
    signal: pd.DataFrame,
    future: pd.DataFrame,
    rank_pct: pd.DataFrame,
    active_mask: pd.DataFrame,
    mode: str,
    horizon: int,
    cost_bps: float,
    config: ActivatorSuiteConfig,
) -> BacktestSnapshot:
    bt_config = BacktestConfig(
        name=f"{mode}:{horizon}d:{cost_bps:g}bps",
        mode=mode,
        horizon=horizon,
        cost_model=turnover_cost(cost_bps),
        top_quantile=config.top_quantile,
        bottom_quantile=config.bottom_quantile,
        threshold=config.threshold,
        min_names=config.min_names,
    )
    result = run_backtest(signal, future, bt_config, active_mask, rank_pct)
    return BacktestSnapshot(summarize_backtest(result), result.net_return)


def _pair_row(
    *,
    alpha: str,
    family: str,
    activator: str,
    mode: str,
    horizon: int,
    cost_bps: float,
    baseline: BacktestSnapshot,
    gated: BacktestSnapshot,
    activator_mask: pd.DataFrame,
    activation_corr: float | None = None,
    decision: str = "screen",
) -> dict[str, object]:
    base = baseline.summary
    gate = gated.summary
    intensity = activator_mask.mean(axis=1).fillna(0.0)
    on_mask = intensity.ge(0.5)
    net = baseline.net_return.reindex(intensity.index).fillna(0.0)
    on_mean = float(net.loc[on_mask].mean() * 10_000.0) if on_mask.any() else 0.0
    off_mean = float(net.loc[~on_mask].mean() * 10_000.0) if (~on_mask).any() else 0.0
    corr = activation_corr if activation_corr is not None else _corr(net, intensity)
    return {
        "alpha": alpha,
        "family": family,
        "activator": activator,
        "mode": mode,
        "horizon": horizon,
        "cost_bps": cost_bps,
        "baseline_net_mean_bps": float(base["net_mean_bps"]),
        "gated_net_mean_bps": float(gate["net_mean_bps"]),
        "lift_bps": float(gate["net_mean_bps"]) - float(base["net_mean_bps"]),
        "baseline_coverage": float(base["coverage"]),
        "gated_coverage": float(gate["coverage"]),
        "baseline_turnover": float(base["turnover"]),
        "gated_turnover": float(gate["turnover"]),
        "activation_corr": float(corr),
        "activation_coverage": float(intensity.mean()),
        "on_mean_net_bps": on_mean,
        "off_mean_net_bps": off_mean,
        "activation_lift_bps": on_mean - off_mean,
        "decision": decision,
    }


def _corr(series: pd.Series, intensity: pd.Series) -> float:
    aligned = series.reindex(intensity.index).fillna(0.0)
    if aligned.std(ddof=0) == 0.0 or intensity.std(ddof=0) == 0.0:
        return 0.0
    return float(aligned.corr(intensity))


def _summary_md(result: ActivatorSuiteResult) -> str:
    selected = result.selection
    active = selected.loc[selected["decision"].eq("activate")]
    lines = [
        "# Activator Suite Run",
        "",
        f"- screen rows: {len(result.screen_results)}",
        f"- selection rows: {len(selected)}",
        f"- activated families: {len(active)}",
        f"- backtest rows: {len(result.backtest_results)}",
        f"- compute backend: {result.compute_backend}",
        "",
    ]
    if not active.empty:
        lines.extend(
            [
                "## Selected Family Activators",
                "",
                active[["family", "selected_activator", "mean_lift_bps", "mean_gated_net_bps"]]
                .sort_values("mean_lift_bps", ascending=False)
                .to_string(index=False),
                "",
            ]
        )
    lines.extend(
        [
            "## Indicator Inventory",
            "",
            "- trend alignment: higher timeframe trend, supertrend, and trend filters",
            "- breakout environment: trend alignment plus breadth, expansion, and relative strength",
            "- mean reversion environment: choppy mean-reverting regime with weak breadth",
            "- volatility expansion / compression: realized-volatility state",
            "- breadth thrust / risk-off: market breadth overlays",
            "- gap continuation / fade: opening gap regime",
            "- volume acceptance: volume profile acceptance and value area",
            "- relative strength leaders / laggards: multi-horizon ranking",
            "- oscillator extreme: RSI, stochastic, and Williams %R extremes",
            "",
            "Macro indicators to wire next: India VIX, yield curve slope, USD/INR, crude, rates, flows, CPI surprise, PMI.",
        ]
    )
    return "\n".join(lines)
