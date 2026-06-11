from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.notebooks.alpha_001.research.alpha101_engine import forward_return, load_panel
from research.projects.price_action_strategy_meta.regime_analysis_report import strategy_daily_frame
from research.projects.price_action_strategy_meta.regime_panel_utils import subset_high_vol_panel
from research.projects.price_action_strategy_meta.selector_neutral_variant_report import strategy_specs_all
from research.projects.price_action_strategy_meta.screening_report import markdown_table as render_table

REPORT_DIR = Path(__file__).resolve().parent / "reports"
MD_PATH = REPORT_DIR / "selector_null_benchmark.md"
SUMMARY_CSV = REPORT_DIR / "selector_null_benchmark_summary.csv"
DETAIL_CSV = REPORT_DIR / "selector_null_benchmark_details.csv"
GATE_MD_PATH = REPORT_DIR / "selector_gate.md"
N_RANDOM_TRIALS = 100


@dataclass(frozen=True)
class NullResult:
    benchmark: str
    trial: int
    policy: str
    test_portfolio_mean_net_bps: float
    test_active_mean_net_bps: float
    test_precision: float
    lift_vs_baseline_bps: float


@dataclass(frozen=True)
class UniverseNullCache:
    base_returns: np.ndarray
    active_mask: np.ndarray
    return_matrix: np.ndarray
    valid_rows: list[np.ndarray]


def build_universe_cache(observed_frame: pd.DataFrame, universe: str) -> UniverseNullCache:
    frame = (
        observed_frame.loc[observed_frame["universe"].eq(universe)]
        .sort_values("date")
        .reset_index(drop=True)
    )
    dates = pd.to_datetime(frame["date"])
    pool = sorted(frame.loc[frame["active"], "strategy"].dropna().unique().tolist())
    panel = subset_high_vol_panel(load_panel(universe))
    future = forward_return(panel.close, 5)
    base_mask = panel.high_vol_mask & panel.active_mask
    frames: dict[str, pd.DataFrame] = {}
    wanted = set(pool)
    for spec in strategy_specs_all():
        if spec.name not in wanted:
            continue
        daily = strategy_daily_frame(
            panel,
            spec,
            5,
            compute_rank_ic=False,
            future=future,
            base_mask=base_mask,
        )
        frames[spec.name] = daily
    matrix = np.empty((len(frame), len(pool)), dtype=float)
    for idx, strategy in enumerate(pool):
        matrix[:, idx] = (
            frames[strategy]
            .reindex(dates)["net_return"]
            .to_numpy(dtype=float, copy=True)
        )
    valid_rows = [np.flatnonzero(~np.isnan(matrix[row])) for row in range(len(frame))]
    return UniverseNullCache(
        base_returns=frame["net_return"].fillna(0.0).to_numpy(dtype=float, copy=True),
        active_mask=frame["active"].to_numpy(dtype=bool, copy=True),
        return_matrix=matrix,
        valid_rows=valid_rows,
    )


def trial_metrics(block_returns: list[np.ndarray], block_active: list[np.ndarray]) -> tuple[float, float, float]:
    returns = np.concatenate(block_returns)
    active_mask = np.concatenate(block_active)
    active_returns = returns[active_mask]
    portfolio_mean = float(returns.mean() * 10_000.0) if returns.size else float("nan")
    active_mean = float(active_returns.mean() * 10_000.0) if active_returns.size else float("nan")
    precision = float((active_returns > 0.0).mean()) if active_returns.size else float("nan")
    return portfolio_mean, active_mean, precision


def random_strategy_trials(
    observed_frame: pd.DataFrame,
    combined_baseline: float,
) -> list[NullResult]:
    rng = np.random.default_rng(7)
    caches = {
        universe: build_universe_cache(observed_frame, universe)
        for universe in ("nifty500", "expanded")
    }
    rows: list[NullResult] = []
    for trial in range(N_RANDOM_TRIALS):
        block_returns: list[np.ndarray] = []
        block_active: list[np.ndarray] = []
        for cache in caches.values():
            returns = cache.base_returns.copy()
            active_mask = cache.active_mask.copy()
            for row in np.flatnonzero(active_mask):
                valid = cache.valid_rows[row]
                if valid.size == 0:
                    active_mask[row] = False
                    returns[row] = 0.0
                    continue
                choice = valid[int(rng.integers(valid.size))]
                returns[row] = cache.return_matrix[row, choice]
            block_returns.append(returns)
            block_active.append(active_mask)
        portfolio_mean, active_mean, precision = trial_metrics(block_returns, block_active)
        rows.append(
            NullResult(
                benchmark="random_strategy",
                trial=trial,
                policy="random",
                test_portfolio_mean_net_bps=portfolio_mean,
                test_active_mean_net_bps=active_mean,
                test_precision=precision,
                lift_vs_baseline_bps=portfolio_mean - combined_baseline,
            )
        )
    return rows


def summarize(results: list[NullResult]) -> pd.DataFrame:
    frame = pd.DataFrame([result.__dict__ for result in results])
    observed_value = float(
        frame.loc[frame["benchmark"].eq("observed"), "test_portfolio_mean_net_bps"].iloc[0]
    )
    summary = (
        frame.groupby("benchmark", as_index=False)
        .agg(
            trials=("trial", "count"),
            median_portfolio_net_bps=("test_portfolio_mean_net_bps", "median"),
            p05_portfolio_net_bps=("test_portfolio_mean_net_bps", lambda s: float(s.quantile(0.05))),
            p95_portfolio_net_bps=("test_portfolio_mean_net_bps", lambda s: float(s.quantile(0.95))),
            median_lift_vs_baseline_bps=("lift_vs_baseline_bps", "median"),
            p_ge_observed=("test_portfolio_mean_net_bps", lambda s: float((s >= observed_value).mean())),
        )
        .sort_values("benchmark")
    )
    return summary


def build_report(summary: pd.DataFrame, observed: NullResult, random_results: list[NullResult]) -> str:
    observed_row = pd.DataFrame([observed.__dict__])
    lines = [
        "# Selector Null Benchmark",
        "",
        "## Protocol",
        "",
        f"- Random-strategy null: {N_RANDOM_TRIALS} seeded draws over the cached active-day strategy pool.",
        "- The observed policy is read from cached gate outputs.",
        "",
        "## Observed",
        "",
        render_table(
            observed_row[
                [
                    "policy",
                    "test_portfolio_mean_net_bps",
                    "test_active_mean_net_bps",
                    "test_precision",
                    "lift_vs_baseline_bps",
                ]
            ]
        ),
        "",
        "## Summary",
        "",
        render_table(summary),
        "",
        "## Interpretation",
        "",
        "- The random-strategy null asks whether the chosen activation pool is better than picking among the same active strategies at random.",
        "- If the null overlaps the observed selector materially, the selector remains fragile.",
        "",
        "## Decision",
        "",
        "- `SUSPECT_OVERFIT`",
        "- The selector still trails the always-on baseline; this cached null check is a sanity test, not promotion evidence.",
    ]
    return "\n".join(lines)


def write_outputs(summary: pd.DataFrame, details: pd.DataFrame, md: str) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text(md, encoding="utf-8")
    SUMMARY_CSV.write_text(summary.to_csv(index=False), encoding="utf-8")
    DETAIL_CSV.write_text(details.to_csv(index=False), encoding="utf-8")


def main() -> int:
    backtest = pd.read_csv(REPORT_DIR / "selector_gate_backtest.csv")
    selected = pd.read_csv(REPORT_DIR / "selector_gate_selected.csv")
    gate_md = GATE_MD_PATH.read_text(encoding="utf-8")
    match = re.search(r"\|\s+combined\s+\|\s+per-universe_best\s+\|\s+([0-9.]+)\s+\|", gate_md)
    if match is None:
        raise ValueError("Could not parse combined baseline from selector_gate.md")
    combined = float(match.group(1))
    policy_row = backtest.loc[backtest["policy"].eq("loose")].iloc[0]
    observed = NullResult(
        benchmark="observed",
        trial=-1,
        policy=str(policy_row["policy"]),
        test_portfolio_mean_net_bps=float(policy_row["test_portfolio_mean_net_bps"]),
        test_active_mean_net_bps=float(policy_row["test_mean_net_bps"]),
        test_precision=float(policy_row["test_precision"]),
        lift_vs_baseline_bps=float(policy_row["test_portfolio_mean_net_bps"] - combined),
    )
    random_results = random_strategy_trials(selected, combined)
    details = pd.DataFrame([observed.__dict__, *[r.__dict__ for r in random_results]])
    summary_frame = summarize([observed, *random_results])
    write_outputs(summary_frame, details, build_report(summary_frame, observed, random_results))
    print(f"Wrote {MD_PATH}")
    print(f"Wrote {SUMMARY_CSV}")
    print(f"Wrote {DETAIL_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
