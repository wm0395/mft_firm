from __future__ import annotations

import json
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]


AUDIT_FILE = "alpha101_metrics_audit/alpha101_metrics_audit_promoted_exact_ohlcv.csv"
PROGRESS_FILE = "alpha101_factory_task_progress.json"
STRICT_FILE = "alpha101_strict_liquidity_primary_report.csv"
TRADEABILITY_CSV = "alpha101_tradeable_strategy_metrics.csv"
TRADEABILITY_MD = "alpha101_tradeable_strategy_metrics.md"
RESEARCH_STATE_FILE = "projects/alpha101_formulaic_alphas/research_state.json"
STRICT_SHARPE_GATE = 0.0
STRICT_POSITIVE_RATE_GATE = 0.75


OUTPUT_COLUMNS = [
    "tradeability_status",
    "alpha_id",
    "panel",
    "family",
    "batch",
    "promotion_status",
    "robustness_lane",
    "best_mask",
    "best_signal_transform",
    "best_strategy",
    "median_test_active_sharpe",
    "median_test_active_cagr",
    "median_test_rank_ic",
    "median_turnover",
    "positive_test_sharpe_rate",
    "strict_median_test_active_sharpe",
    "strict_median_test_active_cagr",
    "strict_positive_test_sharpe_rate",
    "strict_median_test_rank_ic",
    "strict_median_turnover",
    "strict_worst_test_drawdown",
    "strict_selected_mask",
    "strict_selected_signal_transform",
    "strict_selected_strategy",
    "strategy_cagr",
    "strategy_sharpe",
    "strategy_sortino",
    "strategy_max_drawdown",
    "strategy_hit_rate",
    "strategy_avg_daily_turnover",
    "benchmark_cagr",
    "benchmark_sharpe",
    "benchmark_sortino",
    "benchmark_max_drawdown",
    "benchmark_hit_rate",
    "active_cagr",
    "active_sharpe",
    "active_sortino",
    "active_max_drawdown",
    "information_ratio",
    "beta_to_nifty50",
    "correlation_to_nifty50",
    "average_holding_period",
    "trade_count",
    "strategy_observations",
    "benchmark_observations",
    "overlap_observations",
    "overlap_start",
    "overlap_end",
    "rolling_vol_21",
    "rolling_sharpe_21",
    "rolling_corr_21",
    "rolling_beta_21",
    "rolling_vol_63",
    "rolling_sharpe_63",
    "rolling_corr_63",
    "rolling_beta_63",
    "rolling_vol_252",
    "rolling_sharpe_252",
    "rolling_corr_252",
    "rolling_beta_252",
    "promoted_universe_status",
    "cache_status",
]


TABLE_COLUMNS = [
    "tradeability_status",
    "alpha_id",
    "family",
    "strict_selected_signal_transform",
    "strict_selected_strategy",
    "strict_selected_mask",
    "median_test_active_sharpe",
    "median_test_active_cagr",
    "median_test_rank_ic",
    "median_turnover",
    "strict_median_test_active_sharpe",
    "strict_positive_test_sharpe_rate",
    "active_sharpe",
    "active_cagr",
    "strategy_sharpe",
    "strategy_cagr",
    "strategy_avg_daily_turnover",
    "benchmark_sortino",
    "benchmark_max_drawdown",
    "benchmark_hit_rate",
    "active_max_drawdown",
    "beta_to_nifty50",
    "correlation_to_nifty50",
    "average_holding_period",
    "trade_count",
    "strategy_observations",
    "benchmark_observations",
]

RESEARCH_ONLY_COLUMNS = [
    "tradeability_status",
    "alpha_id",
    "family",
    "best_signal_transform",
    "best_strategy",
    "median_test_active_sharpe",
    "median_test_active_cagr",
    "median_test_rank_ic",
    "median_turnover",
    "active_sharpe",
    "strategy_sharpe",
    "strategy_avg_daily_turnover",
    "benchmark_sortino",
    "benchmark_max_drawdown",
    "benchmark_hit_rate",
    "strategy_observations",
    "benchmark_observations",
]

MISSING_AUDIT_COLUMNS = [
    "tradeability_status",
    "alpha_id",
    "batch",
    "promotion_status",
    "median_test_active_sharpe",
    "median_test_active_cagr",
    "median_test_rank_ic",
    "best_signal_transform",
    "best_strategy",
    "best_mask",
]


def read_progress(artifact_dir: Path) -> dict[str, object]:
    path = artifact_dir / PROGRESS_FILE
    return json.loads(path.read_text()) if path.exists() else {}


def read_promoted_frame(artifact_dir: Path) -> pd.DataFrame:
    state_path = artifact_dir.parents[1] / RESEARCH_STATE_FILE
    if not state_path.exists():
        return pd.DataFrame()
    state = json.loads(state_path.read_text())
    return pd.DataFrame(state.get("promotion_rows", []))


def promoted_base_frame(audit: pd.DataFrame, promoted: pd.DataFrame) -> pd.DataFrame:
    if promoted.empty:
        return audit.copy()
    missing = promoted[~promoted["alpha_id"].isin(audit["alpha_id"])]
    combined = pd.concat([audit, missing], ignore_index=True, sort=False)
    combined["promoted_universe_status"] = "metrics_audit_covered"
    combined.loc[combined["alpha_id"].isin(missing["alpha_id"]), "promoted_universe_status"] = "missing_metrics_audit"
    return combined


def strict_metric_frame(strict: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "alpha_id",
        "median_test_active_sharpe",
        "median_test_active_cagr",
        "positive_test_sharpe_rate",
        "median_test_rank_ic",
        "median_turnover",
        "worst_test_drawdown",
        "selected_mask",
        "selected_signal_transform",
        "selected_strategy",
    ]
    renames = {name: f"strict_{name}" for name in columns if name != "alpha_id"}
    return strict[columns].rename(columns=renames)


def tradeability_status(row: pd.Series) -> str:
    sharpe = row.get("strict_median_test_active_sharpe")
    rate = row.get("strict_positive_test_sharpe_rate")
    if pd.notna(sharpe) and pd.notna(rate):
        if sharpe > STRICT_SHARPE_GATE and rate >= STRICT_POSITIVE_RATE_GATE:
            return "strict_liquidity_tradeable_candidate"
        return "strict_liquidity_not_tradeable_yet"
    if row.get("promoted_universe_status") == "missing_metrics_audit":
        return "promoted_exact_missing_metrics_audit"
    return "high_vol_research_only_candidate"


def build_tradeability_frame(artifact_dir: Path) -> pd.DataFrame:
    audit = pd.read_csv(artifact_dir / AUDIT_FILE)
    strict = pd.read_csv(artifact_dir / STRICT_FILE)
    promoted = read_promoted_frame(artifact_dir)
    progress = read_progress(artifact_dir)
    base = promoted_base_frame(audit, promoted)
    merged = base.merge(strict_metric_frame(strict), on="alpha_id", how="left")
    merged["tradeability_status"] = merged.apply(tradeability_status, axis=1)
    merged["cache_status"] = cache_status(progress)
    for column in OUTPUT_COLUMNS:
        if column not in merged.columns:
            merged[column] = pd.NA
    return rank_tradeability(merged)[OUTPUT_COLUMNS]


def cache_status(progress: dict[str, object]) -> str:
    return "complete" if progress.get("missing_tasks") == 0 else "incomplete_factory_cache"


def rank_tradeability(frame: pd.DataFrame) -> pd.DataFrame:
    rank_map = {
        "strict_liquidity_tradeable_candidate": 0,
        "high_vol_research_only_candidate": 1,
        "strict_liquidity_not_tradeable_yet": 2,
        "promoted_exact_missing_metrics_audit": 3,
    }
    ranked = frame.copy()
    ranked["tradeability_rank_key"] = ranked["tradeability_status"].map(rank_map).fillna(9)
    return ranked.sort_values(
        ["tradeability_rank_key", "strict_median_test_active_sharpe", "median_test_active_sharpe", "active_sharpe"],
        ascending=[True, False, False, False],
    )


def markdown_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value).replace("|", "/")


def markdown_table(frame: pd.DataFrame) -> str:
    headers = [str(col) for col in frame.columns]
    rows = [[markdown_value(value) for value in row] for row in frame.to_numpy()]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def format_tradeability_markdown(frame: pd.DataFrame, progress: dict[str, object]) -> str:
    tradeable = frame[frame["tradeability_status"].eq("strict_liquidity_tradeable_candidate")]
    research_only = frame[frame["tradeability_status"].eq("high_vol_research_only_candidate")]
    holdouts = frame[frame["tradeability_status"].eq("strict_liquidity_not_tradeable_yet")]
    missing_audit = frame[frame["promoted_universe_status"].eq("missing_metrics_audit")]
    strict_rows = len(tradeable) + len(holdouts)
    focus = ", ".join(f"`{alpha_id}`" for alpha_id in tradeable["alpha_id"])
    return "\n".join(
        [
            "# Alpha101 Tradeable Strategy Metrics",
            "",
            "## Cache and Evidence Status",
            f"- Factory task cache: {progress.get('completed_tasks')}/{progress.get('total_tasks')} complete; {progress.get('missing_tasks')} missing.",
            f"- Promoted exact-OHLCV coverage: {len(frame) - len(missing_audit)}/{len(frame)} names have metrics-audit rows; {len(missing_audit)} names are listed below as missing audit evidence.",
            f"- Strict-liquidity evidence coverage: {strict_rows}/{len(frame)} promoted names have strict-liquidity rows.",
            "- This report uses exact-OHLCV promoted candidates from `alpha101_metrics_audit_promoted_exact_ohlcv.csv` plus strict-liquidity evidence from `alpha101_strict_liquidity_primary_report.csv`.",
            "- Proxy VWAP and snapshot-industry candidates are excluded from the tradeable list.",
            "- High-vol-only rows are research-only and are not production-tradeable until strict-liquidity and capacity evidence exists.",
            "",
            "## Promotion Interpretation",
            "- `strict_liquidity_tradeable_candidate`: exact-OHLCV candidate with positive strict-liquidity median test active Sharpe and at least 75% positive test-Sharpe folds.",
            "- `high_vol_research_only_candidate`: exact-OHLCV candidate with full high-vol audit metrics, but no strict-liquidity proof in the current strict report.",
            "- `strict_liquidity_not_tradeable_yet`: exact-OHLCV candidate whose strict-liquidity recompute failed the positive gate.",
            "- `promoted_exact_missing_metrics_audit`: promoted exact-OHLCV name present in project state but absent from the current metrics-audit source.",
            "",
            "## Strict-Liquidity Tradeable Strategies",
            markdown_table(tradeable[TABLE_COLUMNS]),
            "",
            "## Research-Only High-Vol Candidates",
            markdown_table(research_only[RESEARCH_ONLY_COLUMNS]),
            "",
            "## Strict-Liquidity Holdouts",
            markdown_table(holdouts[TABLE_COLUMNS]),
            "",
            "## Promoted Exact-OHLCV Names Missing Metrics-Audit Evidence",
            markdown_table(missing_audit[MISSING_AUDIT_COLUMNS]),
            "",
            "## Decision",
            f"- Current strict-liquidity tradeable focus list: {focus}.",
            f"- Strict-liquidity holdouts: {len(holdouts)} promoted exact-OHLCV names.",
            f"- Metrics-audit gaps: {len(missing_audit)} promoted exact-OHLCV names need full audit metrics refreshed.",
            "",
        ]
    )


def write_tradeability_metrics(artifact_dir: Path) -> tuple[Path, Path]:
    frame = build_tradeability_frame(artifact_dir)
    progress = read_progress(artifact_dir)
    csv_path = artifact_dir / TRADEABILITY_CSV
    md_path = artifact_dir / TRADEABILITY_MD
    frame.to_csv(csv_path, index=False)
    md_path.write_text(format_tradeability_markdown(frame, progress))
    return csv_path, md_path


if __name__ == "__main__":
    write_tradeability_metrics(Path("research/artifacts/alpha101_research_factory"))
