from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from research.projects.price_action_strategy_lab.backtest_modes import (
    BacktestConfig,
    BacktestResult,
    run_backtest,
    summarize_backtest,
)
from research.projects.price_action_strategy_lab.chart_pack import (
    ChartPackConfig,
    generate_chart_pack,
    signals_from_positions,
)
from research.projects.price_action_strategy_lab.costs import turnover_cost
from research.projects.price_action_strategy_lab.selector_registry import selector_registry


@dataclass(frozen=True)
class LabRunResult:
    report_dir: Path
    run_summary_path: Path
    alpha_results_path: Path
    mode_comparison_path: Path
    selector_results_path: Path
    chart_index_path: Path


def run_lab(config_path: Path) -> LabRunResult:
    config = _read_config(config_path)
    report_dir = Path(config["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    data = _read_market_data(Path(config["data_csv"]))
    signal = data["signal"].unstack("symbol")
    forward = data["forward_return"].unstack("symbol")
    active = data["active"].unstack("symbol").astype(bool)
    results = tuple(_run_configs(signal, forward, active, config))
    selector_rows = _selector_rows(results)
    charts = _write_charts(data, results, config, report_dir)
    return _write_reports(results, selector_rows, charts, report_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args(argv)
    run_lab(Path(args.config))
    return 0


def _read_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def _read_market_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path, parse_dates=["date"])
    required = {"date", "symbol", "open", "high", "low", "close", "volume"}
    required |= {"signal", "forward_return"}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"missing data columns: {missing}")
    if "active" not in data.columns:
        data["active"] = True
    return data.set_index(["date", "symbol"]).sort_index()


def _run_configs(
    signal: pd.DataFrame,
    forward: pd.DataFrame,
    active: pd.DataFrame,
    config: dict[str, Any],
) -> list[BacktestResult]:
    rows = []
    rank_pct = signal.rank(axis=1, pct=True, method="average")
    for item in config.get("backtests", []):
        cost = item.get("cost", {})
        bt_config = BacktestConfig(
            name=str(item["name"]),
            mode=str(item["mode"]),
            horizon=int(item.get("horizon", 1)),
            cost_model=turnover_cost(float(cost.get("turnover_bps", 0.0))),
            threshold=float(item.get("threshold", 0.0)),
            min_names=int(item.get("min_names", 1)),
        )
        rows.append(run_backtest(signal, forward, bt_config, active, rank_pct))
    return rows


def _selector_rows(results: tuple[BacktestResult, ...]) -> list[dict[str, float | str | bool]]:
    rows: list[dict[str, float | str | bool]] = []
    for spec in selector_registry():
        decision = spec.builder(results)
        rows.append(
            {
                "selector": spec.name,
                "chosen_name": decision.chosen_name,
                "confidence": decision.confidence,
                "abstain": decision.abstain,
                "reason_code": decision.reason_code,
            }
        )
    return rows


def _write_charts(
    data: pd.DataFrame,
    results: tuple[BacktestResult, ...],
    config: dict[str, Any],
    report_dir: Path,
) -> list[Path]:
    chart_paths: list[Path] = []
    chart_symbols = tuple(str(symbol) for symbol in config.get("chart_symbols", []))
    if not results:
        return chart_paths
    signals = signals_from_positions(results[0].positions, results[0].name, results[0].reason_code)
    for symbol in chart_symbols:
        ohlcv = data.xs(symbol, level="symbol")[["open", "high", "low", "close", "volume"]]
        chart = generate_chart_pack(ohlcv, signals, ChartPackConfig(symbol, report_dir / "charts"))
        chart_paths.append(chart.html_path)
    return chart_paths


def _write_reports(
    results: tuple[BacktestResult, ...],
    selector_rows: list[dict[str, float | str | bool]],
    charts: list[Path],
    report_dir: Path,
) -> LabRunResult:
    alpha_path = report_dir / "alpha_results.csv"
    mode_path = report_dir / "mode_comparison.csv"
    selector_path = report_dir / "selector_results.csv"
    chart_index_path = report_dir / "chart_index.md"
    summary_path = report_dir / "run_summary.md"
    summary = pd.DataFrame([summarize_backtest(result) for result in results])
    summary.to_csv(alpha_path, index=False)
    _mode_comparison(summary).to_csv(mode_path, index=False)
    pd.DataFrame(selector_rows).to_csv(selector_path, index=False)
    chart_index_path.write_text(_chart_index(charts), encoding="utf-8")
    summary_path.write_text(_run_summary(results, selector_rows), encoding="utf-8")
    return LabRunResult(report_dir, summary_path, alpha_path, mode_path, selector_path, chart_index_path)


def _mode_comparison(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return summary
    return (
        summary.groupby("mode", as_index=False)
        .agg(
            runs=("name", "count"),
            mean_net_bps=("net_mean_bps", "mean"),
            mean_turnover=("turnover", "mean"),
            mean_coverage=("coverage", "mean"),
            mean_win_rate=("win_rate", "mean"),
        )
        .sort_values("mean_net_bps", ascending=False)
    )


def _chart_index(charts: list[Path]) -> str:
    if not charts:
        return "# Chart Index\n\nNo charts requested.\n"
    rows = "\n".join(f"- {path.as_posix()}" for path in charts)
    return f"# Chart Index\n\n{rows}\n"


def _run_summary(
    results: tuple[BacktestResult, ...],
    selector_rows: list[dict[str, float | str | bool]],
) -> str:
    best = selector_rows[0]["chosen_name"] if selector_rows else ""
    return "\n".join(
        [
            "# Price Action Strategy Lab Run",
            "",
            f"- backtests: {len(results)}",
            f"- selectors: {len(selector_rows)}",
            f"- first_selector_choice: {best}",
            "",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
