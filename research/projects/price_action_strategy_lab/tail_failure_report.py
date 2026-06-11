from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TailFailureReportPaths:
    variant_diagnostics: Path
    alpha_variant_diagnostics: Path
    gate_diagnostics: Path
    markdown: Path


def write_tail_failure_report(report_dir: Path) -> TailFailureReportPaths:
    folds = pd.read_csv(report_dir / "soft_throttle_walk_forward_fold_metrics.csv")
    alpha_folds = _read_optional(report_dir / "soft_throttle_walk_forward_alpha_fold_metrics.csv")
    gates = _read_optional(report_dir / "soft_throttle_walk_forward_selected_gates.csv")
    variants = tail_variant_diagnostics(folds)
    alpha_variants = tail_alpha_variant_diagnostics(alpha_folds)
    gate_diag = tail_gate_diagnostics(gates, folds)
    variant_path = report_dir / "tail_variant_diagnostics.csv"
    alpha_variant_path = report_dir / "tail_alpha_variant_diagnostics.csv"
    gate_path = report_dir / "tail_gate_diagnostics.csv"
    markdown_path = report_dir / "tail_failure_report.md"
    variants.to_csv(variant_path, index=False)
    alpha_variants.to_csv(alpha_variant_path, index=False)
    gate_diag.to_csv(gate_path, index=False)
    markdown_path.write_text(_markdown(variants, alpha_variants, gate_diag), encoding="utf-8")
    return TailFailureReportPaths(variant_path, alpha_variant_path, gate_path, markdown_path)


def tail_variant_diagnostics(folds: pd.DataFrame) -> pd.DataFrame:
    if folds.empty:
        return pd.DataFrame()
    base = _baseline_series(folds, "return_pct")
    base_sharpe = _baseline_series(folds, "ann_sharpe")
    base_drawdown = _baseline_series(folds, "max_drawdown_pct")
    left_folds = set(base.loc[base.le(base.quantile(0.25))].index)
    right_folds = set(base.loc[base.ge(base.quantile(0.75))].index)
    rows = [
        _variant_row(variant, frame, base, base_sharpe, base_drawdown, left_folds, right_folds)
        for variant, frame in folds.groupby("variant", sort=False)
    ]
    return pd.DataFrame(rows).sort_values(["tail_decision_rank", "sharpe_delta"], ascending=[True, False]).drop(
        columns="tail_decision_rank"
    )


def tail_alpha_variant_diagnostics(alpha_folds: pd.DataFrame) -> pd.DataFrame:
    if alpha_folds.empty or "alpha" not in alpha_folds:
        return pd.DataFrame()
    rows = []
    for alpha, frame in alpha_folds.groupby("alpha", sort=False):
        diagnostics = tail_variant_diagnostics(frame).copy()
        diagnostics.insert(0, "alpha", alpha)
        rows.append(diagnostics)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def tail_gate_diagnostics(gates: pd.DataFrame, folds: pd.DataFrame) -> pd.DataFrame:
    if gates.empty:
        return pd.DataFrame()
    base = _baseline_series(folds, "return_pct")
    left = set(base.loc[base.le(base.quantile(0.25))].index)
    right = set(base.loc[base.ge(base.quantile(0.75))].index)
    active = gates.loc[gates["decision"].eq("activate") & gates["indicator"].notna()].copy()
    active["tail_bucket"] = np.select([active["fold"].isin(left), active["fold"].isin(right)], ["left_tail", "right_tail"], "middle")
    grouped = active.groupby(["tail_bucket", "indicator", "side"], dropna=False)
    rows = [_gate_row(keys, frame) for keys, frame in grouped]
    return pd.DataFrame(rows).sort_values(["tail_bucket", "selection_count"], ascending=[True, False])


def _variant_row(
    variant: str,
    frame: pd.DataFrame,
    base_return: pd.Series,
    base_sharpe: pd.Series,
    base_drawdown: pd.Series,
    left_folds: set[int],
    right_folds: set[int],
) -> dict[str, object]:
    aligned = frame.set_index("fold").sort_index()
    returns = aligned["return_pct"].reindex(base_return.index)
    delta = returns - base_return
    left_delta = delta.loc[delta.index.isin(left_folds)]
    right_base = base_return.loc[base_return.index.isin(right_folds)]
    right_returns = returns.loc[returns.index.isin(right_folds)]
    ci_low, ci_high = _bootstrap_mean_ci(delta)
    t_stat, p_value = _paired_t(delta)
    return {
        "variant": variant,
        "fold_count": int(delta.dropna().shape[0]),
        "mean_return_pct": float(returns.mean()),
        "mean_delta_vs_baseline_pct": float(delta.mean()),
        "delta_ci_low_pct": ci_low,
        "delta_ci_high_pct": ci_high,
        "paired_t_stat": t_stat,
        "paired_p_value": p_value,
        "left_tail_delta_pct": float(left_delta.mean()),
        "right_tail_retention": _safe_ratio(float(right_returns.mean()), float(right_base.mean())),
        "negative_fold_rate": float(returns.lt(0.0).mean()),
        "worse_than_baseline_rate": float(delta.lt(0.0).mean()),
        "sharpe_delta": _metric_delta(aligned, base_sharpe, "ann_sharpe"),
        "max_drawdown_delta_pct": _metric_delta(aligned, base_drawdown, "max_drawdown_pct"),
        "tail_decision": _tail_decision(variant, left_delta, right_returns, right_base, ci_low),
        "tail_decision_rank": _tail_rank(variant, left_delta, right_returns, right_base, ci_low),
    }


def _gate_row(keys: tuple[object, object, object], frame: pd.DataFrame) -> dict[str, object]:
    bucket, indicator, side = keys
    return {
        "tail_bucket": str(bucket),
        "indicator": str(indicator),
        "side": str(side),
        "selection_count": int(len(frame)),
        "unique_alphas": int(frame["alpha"].nunique()),
        "unique_folds": int(frame["fold"].nunique()),
        "mean_score": float(frame["score"].mean()),
        "mean_lift_bps": float(frame["lift_bps"].mean()),
        "mean_on_return_bps": float(frame["on_return_bps"].mean()),
        "mean_off_return_bps": float(frame["off_return_bps"].mean()),
    }


def _baseline_series(folds: pd.DataFrame, column: str) -> pd.Series:
    base = folds.loc[folds["variant"].eq("baseline"), ["fold", column]]
    return base.set_index("fold")[column].sort_index()


def _metric_delta(frame: pd.DataFrame, baseline: pd.Series, column: str) -> float:
    if column not in frame:
        return 0.0
    aligned = frame[column].reindex(baseline.index)
    return float((aligned - baseline).mean())


def _bootstrap_mean_ci(values: pd.Series) -> tuple[float, float]:
    clean = values.dropna().to_numpy(dtype=float)
    if clean.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(7)
    draws = rng.choice(clean, size=(2000, clean.size), replace=True).mean(axis=1)
    return float(np.quantile(draws, 0.05)), float(np.quantile(draws, 0.95))


def _paired_t(values: pd.Series) -> tuple[float, float]:
    clean = values.dropna().to_numpy(dtype=float)
    if clean.size < 2 or float(np.std(clean, ddof=1)) == 0.0:
        return 0.0, 1.0
    result = import_module("scipy.stats").ttest_1samp(clean, 0.0)
    return float(result.statistic), float(result.pvalue)


def _safe_ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator != 0.0 else float("nan")


def _tail_decision(variant: str, left_delta: pd.Series, right_returns: pd.Series, right_base: pd.Series, ci_low: float) -> str:
    if variant == "baseline":
        return "control"
    if float(left_delta.mean()) <= 0.0:
        return "reject_no_left_tail_help"
    if _safe_ratio(float(right_returns.mean()), float(right_base.mean())) < 0.85:
        return "reject_loses_right_tail"
    if ci_low <= 0.0:
        return "research_only_not_significant"
    return "candidate_tail_throttle"


def _tail_rank(variant: str, left_delta: pd.Series, right_returns: pd.Series, right_base: pd.Series, ci_low: float) -> int:
    order = {"candidate_tail_throttle": 0, "research_only_not_significant": 1, "control": 2}
    return order.get(_tail_decision(variant, left_delta, right_returns, right_base, ci_low), 3)


def _read_optional(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _markdown(variants: pd.DataFrame, alpha_variants: pd.DataFrame, gates: pd.DataFrame) -> str:
    top = variants.head(8).drop(columns=[col for col in ("tail_decision_rank",) if col in variants])
    lines = ["# Tail Failure Report", "", "## Variant Diagnostics", "", _markdown_table(top), ""]
    lines.extend(["## Alpha-Level Tail Candidates", ""])
    if alpha_variants.empty:
        lines.append("_No alpha-level fold diagnostics available. Re-run walk-forward to populate them._")
    else:
        candidates = alpha_variants.loc[alpha_variants["tail_decision"].eq("candidate_tail_throttle")].head(15)
        lines.append(_markdown_table(candidates))
    lines.append("")
    lines.extend(["## Gate Concentration In Baseline Tail Folds", ""])
    if gates.empty:
        lines.append("No selected-gate diagnostics were available.")
    else:
        left = gates.loc[gates["tail_bucket"].eq("left_tail")].head(10)
        lines.append(_markdown_table(left))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `left_tail_delta_pct` is variant return minus baseline return on baseline bottom-quartile folds.",
            "- `right_tail_retention` is variant mean return divided by baseline mean return on baseline top-quartile folds.",
            "- `delta_ci_low_pct` is a deterministic bootstrap 5% lower bound for paired fold return deltas.",
            "- Promotion requires left-tail improvement, at least 85% right-tail retention, and positive lower CI.",
            "",
            "## External Hypotheses To Test Next",
            "",
            "- Volatility scaling: test NIFTY realized volatility and India VIX as soft exposure inputs.",
            "- Liquidity stress: test Amihud-style illiquidity and traded-value collapse before drawdown folds.",
            "- Breadth/trend stress: test broad selloff breadth, index drawdown, and NIFTY trend state.",
            "- News/event clues: tag January 2025, July 2025, and February 2026 drawdown folds before use.",
            "- These are hypothesis-generation inputs only; every feature needs lagged, purged OOS validation.",
        ]
    )
    return "\n".join(lines)


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    cols = list(frame.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in frame.itertuples(index=False):
        lines.append("| " + " | ".join(_cell(item) for item in row) + " |")
    return "\n".join(lines)


def _cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
