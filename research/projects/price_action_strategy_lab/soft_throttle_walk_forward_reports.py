from __future__ import annotations

from typing import Any

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _active_mean_bps
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _annual_sharpe
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _annual_vol_pct
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _cagr_pct
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _combine_series
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _latest
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _max_drawdown_pct
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _mean_negative
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _rolling_sharpe
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _total_return_pct


def fold_metric_row(
    fold: Any,
    variant: str,
    returns: pd.Series,
    turnover: pd.Series,
    multiplier: pd.Series,
    rolling_window_days: int,
) -> dict[str, object]:
    clean = returns.dropna()
    rolling = _rolling_sharpe(clean, rolling_window_days)
    active = multiplier.reindex(clean.index).fillna(0.0).gt(0.0)
    reduced = multiplier.reindex(clean.index).fillna(0.0).lt(1.0)
    return {
        "fold": fold.fold,
        "variant": variant,
        "train_days": len(fold.train_index),
        "test_days": len(fold.test_index),
        "train_start": str(fold.train_index[0].date()) if len(fold.train_index) else "",
        "train_end": str(fold.train_index[-1].date()) if len(fold.train_index) else "",
        "test_start": str(fold.test_index[0].date()) if len(fold.test_index) else "",
        "test_end": str(fold.test_index[-1].date()) if len(fold.test_index) else "",
        "obs": int(clean.shape[0]),
        "return_pct": _total_return_pct(clean),
        "cagr_pct": _cagr_pct(clean),
        "ann_vol_pct": _annual_vol_pct(clean),
        "ann_sharpe": _annual_sharpe(clean),
        "latest_1m_rolling_sharpe": _latest(rolling),
        "negative_1m_sharpe_windows": int(rolling.lt(0.0).sum()),
        "negative_1m_sharpe_rate": float(rolling.lt(0.0).mean()) if not rolling.empty else 0.0,
        "mean_negative_1m_sharpe": _mean_negative(rolling),
        "worst_1m_sharpe": float(rolling.min()) if not rolling.empty else float("nan"),
        "max_drawdown_pct": _max_drawdown_pct(clean),
        "avg_exposure_multiplier": float(multiplier.mean()) if not multiplier.empty else 0.0,
        "active_day_pct": float(active.mean() * 100.0) if not active.empty else 0.0,
        "return_per_active_day_bps": _active_mean_bps(clean, active),
        "turnover": float(turnover.mean()) if not turnover.empty else 0.0,
        "positive_windows_reduced": int((rolling.gt(0.0) & reduced.reindex(rolling.index).fillna(False)).sum()) if not rolling.empty else 0,
        "negative_windows_reduced": int((rolling.lt(0.0) & reduced.reindex(rolling.index).fillna(False)).sum()) if not rolling.empty else 0,
    }


def fold_exposure_row(
    fold: Any,
    variant: str,
    returns: pd.Series,
    turnover: pd.Series,
    multiplier: pd.Series,
    rolling_window_days: int,
) -> dict[str, object]:
    clean = returns.dropna()
    active = multiplier.gt(0.0)
    reduced = multiplier.lt(1.0)
    baseline_rolling = _rolling_sharpe(clean, rolling_window_days)
    return {
        "fold": fold.fold,
        "variant": variant,
        "active_day_pct": float(active.mean() * 100.0) if not active.empty else 0.0,
        "avg_exposure_multiplier": float(multiplier.mean()) if not multiplier.empty else 0.0,
        "return_per_active_day_bps": _active_mean_bps(clean, active),
        "baseline_return_reduced_days_pct": _total_return_pct(clean.loc[reduced.reindex(clean.index).fillna(False)]) if not clean.empty else 0.0,
        "positive_windows_reduced": int((baseline_rolling.gt(0.0) & reduced.reindex(baseline_rolling.index).fillna(False)).sum()) if not baseline_rolling.empty else 0,
        "negative_windows_reduced": int((baseline_rolling.lt(0.0) & reduced.reindex(baseline_rolling.index).fillna(False)).sum()) if not baseline_rolling.empty else 0,
        "scaled_turnover_est": float(turnover.mean()) if not turnover.empty else 0.0,
    }


def gate_row(fold: Any, alpha: str, recommendation: pd.Series | None) -> dict[str, object]:
    row = {
        "fold": fold.fold,
        "alpha": alpha,
        "train_start": str(fold.train_index[0].date()) if len(fold.train_index) else "",
        "train_end": str(fold.train_index[-1].date()) if len(fold.train_index) else "",
        "test_start": str(fold.test_index[0].date()) if len(fold.test_index) else "",
        "test_end": str(fold.test_index[-1].date()) if len(fold.test_index) else "",
        "indicator": "",
        "side": "",
        "threshold": 0.0,
        "score": 0.0,
        "decision": "abstain",
    }
    if recommendation is not None:
        row.update(recommendation.to_dict())
        row["decision"] = "activate"
    return row


def aggregate_rows(
    fold_frame: pd.DataFrame,
    aggregate_series: dict[str, list[pd.Series]],
    aggregate_turnover: dict[str, list[pd.Series]],
    variant_names: tuple[str, ...],
) -> pd.DataFrame:
    if fold_frame.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for variant in variant_names:
        variant_folds = fold_frame.loc[fold_frame["variant"].eq(variant)].sort_values("fold")
        daily = _combine_series(aggregate_series[variant])
        turnover = _combine_series(aggregate_turnover[variant])
        rows.append(
            {
                "variant": variant,
                "fold_count": int(variant_folds["fold"].nunique()),
                "return_pct": _total_return_pct(daily),
                "cagr_pct": _cagr_pct(daily),
                "ann_vol_pct": _annual_vol_pct(daily),
                "ann_sharpe": _annual_sharpe(daily),
                "latest_fold_sharpe": float(variant_folds.iloc[-1]["ann_sharpe"]),
                "negative_fold_rate": float(variant_folds["ann_sharpe"].lt(0.0).mean()),
                "worst_fold_sharpe": float(variant_folds["ann_sharpe"].min()),
                "max_drawdown_pct": _max_drawdown_pct(daily),
                "avg_exposure_multiplier": float(variant_folds["avg_exposure_multiplier"].mean()),
                "active_day_pct": float(variant_folds["active_day_pct"].mean()),
                "return_per_active_day_bps": float(variant_folds["return_per_active_day_bps"].mean()),
                "turnover": float(turnover.mean()) if not turnover.empty else 0.0,
                "positive_windows_reduced": int(variant_folds["positive_windows_reduced"].sum()),
                "negative_windows_reduced": int(variant_folds["negative_windows_reduced"].sum()),
            }
        )
    return pd.DataFrame(rows)


def gate_stability(selected_gates: pd.DataFrame) -> pd.DataFrame:
    if selected_gates.empty:
        return selected_gates
    frame = selected_gates.copy()
    for column, default in {"indicator": "", "side": "", "threshold": 0.0, "score": 0.0}.items():
        if column not in frame.columns:
            frame[column] = default
    rows: list[dict[str, object]] = []
    for alpha, alpha_frame in frame.groupby("alpha"):
        indicator_counts = alpha_frame["indicator"].value_counts()
        top_indicator = str(indicator_counts.index[0]) if not indicator_counts.empty else ""
        rows.append(
            {
                "alpha": alpha,
                "fold_count": int(alpha_frame["fold"].nunique()),
                "unique_indicators": int(alpha_frame["indicator"].nunique()),
                "top_indicator": top_indicator,
                "top_indicator_rate": float(indicator_counts.iloc[0] / len(alpha_frame)) if not indicator_counts.empty else 0.0,
                "unique_sides": int(alpha_frame["side"].nunique()),
                "threshold_mean": float(pd.to_numeric(alpha_frame["threshold"], errors="coerce").mean()),
                "threshold_std": float(pd.to_numeric(alpha_frame["threshold"], errors="coerce").std(ddof=1)),
                "score_mean": float(pd.to_numeric(alpha_frame["score"], errors="coerce").mean()),
                "score_std": float(pd.to_numeric(alpha_frame["score"], errors="coerce").std(ddof=1)),
                "activate_rate": float(alpha_frame["decision"].eq("activate").mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["top_indicator_rate", "score_mean"], ascending=[False, False]).reset_index(drop=True)


def decision_frame(aggregate: pd.DataFrame) -> pd.DataFrame:
    if aggregate.empty:
        return aggregate
    baseline = aggregate.loc[aggregate["variant"].eq("baseline")].iloc[0]
    soft = aggregate.loc[aggregate["variant"].eq("soft_aggressive")].iloc[0]
    conditions = {
        "sharpe": float(soft["ann_sharpe"]) > float(baseline["ann_sharpe"]),
        "max_dd": float(soft["max_drawdown_pct"]) > float(baseline["max_drawdown_pct"]),
        "worst_fold": float(soft["worst_fold_sharpe"]) > float(baseline["worst_fold_sharpe"]),
        "return_retention": float(soft["return_pct"]) >= 0.85 * float(baseline["return_pct"]),
    }
    decision = "promote" if all(conditions.values()) else "research_only"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "baseline_return_pct": float(baseline["return_pct"]),
                "soft_aggressive_return_pct": float(soft["return_pct"]),
                "baseline_ann_sharpe": float(baseline["ann_sharpe"]),
                "soft_aggressive_ann_sharpe": float(soft["ann_sharpe"]),
                "baseline_max_drawdown_pct": float(baseline["max_drawdown_pct"]),
                "soft_aggressive_max_drawdown_pct": float(soft["max_drawdown_pct"]),
                "baseline_worst_fold_sharpe": float(baseline["worst_fold_sharpe"]),
                "soft_aggressive_worst_fold_sharpe": float(soft["worst_fold_sharpe"]),
                "baseline_latest_fold_sharpe": float(baseline["latest_fold_sharpe"]),
                "soft_aggressive_latest_fold_sharpe": float(soft["latest_fold_sharpe"]),
                "return_retention": float(soft["return_pct"]) / float(baseline["return_pct"]) if float(baseline["return_pct"]) else 0.0,
                "sharpe_pass": conditions["sharpe"],
                "drawdown_pass": conditions["max_dd"],
                "worst_fold_pass": conditions["worst_fold"],
                "return_pass": conditions["return_retention"],
            }
        ]
    )


def decision_markdown(decision: pd.DataFrame, aggregate: pd.DataFrame) -> str:
    if decision.empty:
        return "# Soft Throttle Walk-Forward Decision\n\n_No decision available._\n"
    row = decision.iloc[0].to_dict()
    lines = ["# Soft Throttle Walk-Forward Decision", ""]
    lines.extend(
        [
            f"- decision: {row.get('decision', 'research_only')}",
            f"- return_retention: {float(row.get('return_retention', 0.0)):.3f}",
            f"- sharpe_pass: {bool(row.get('sharpe_pass', False))}",
            f"- drawdown_pass: {bool(row.get('drawdown_pass', False))}",
            f"- worst_fold_pass: {bool(row.get('worst_fold_pass', False))}",
            f"- return_pass: {bool(row.get('return_pass', False))}",
        ]
    )
    lines.extend(["", markdown_table(aggregate, max_rows=10)])
    return "\n".join(lines) + "\n"


def markdown_table(frame: pd.DataFrame, max_rows: int = 10) -> str:
    if frame.empty:
        return "_No rows._"
    view = frame.head(max_rows).copy()
    header = "| " + " | ".join(view.columns) + " |"
    separator = "| " + " | ".join("---" for _ in view.columns) + " |"
    rows = [header, separator]
    for _, row in view.iterrows():
        rows.append("| " + " | ".join(format_cell(row[col]) for col in view.columns) + " |")
    return "\n".join(rows)


def format_cell(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def slice_panel(panel: Alpha101Panel, index: pd.Index) -> Alpha101Panel:
    return Alpha101Panel(
        name=panel.name,
        open=panel.open.reindex(index),
        high=panel.high.reindex(index),
        low=panel.low.reindex(index),
        close=panel.close.reindex(index),
        adj_close=panel.adj_close.reindex(index),
        volume=panel.volume.reindex(index),
        vwap=panel.vwap.reindex(index),
        returns=panel.returns.reindex(index),
        active_mask=panel.active_mask.reindex(index).fillna(False).astype(bool),
        high_vol_mask=panel.high_vol_mask.reindex(index).fillna(False).astype(bool),
        constituents=panel.constituents,
        industry=panel.industry,
        pit_risk=panel.pit_risk,
    )


def variant_names() -> tuple[str, ...]:
    return ("baseline", "hard_gate", "soft_conservative", "soft_aggressive", "drawdown_only_throttle")
