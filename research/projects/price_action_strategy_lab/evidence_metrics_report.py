from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EvidenceMetricsPaths:
    alpha_metrics: Path
    alpha_deltas: Path
    top_candidates: Path
    gate_metrics: Path
    variant_metrics: Path
    summary: Path


def write_evidence_metrics(report_dir: Path) -> EvidenceMetricsPaths:
    metrics = _read(report_dir, "soft_throttle_2yr_metrics.csv")
    exposure = _read(report_dir, "soft_throttle_exposure_diagnostics.csv")
    gates = _read(report_dir, "indicator_alpha_tuned_gates.csv")
    correlations = _read(report_dir, "indicator_alpha_correlations.csv")
    wf_gates = _read(report_dir, "soft_throttle_walk_forward_selected_gates.csv")
    wf_stability = _read(report_dir, "soft_throttle_walk_forward_gate_stability.csv")
    alpha_metrics = _alpha_metrics(metrics, exposure)
    alpha_deltas = _alpha_deltas(alpha_metrics)
    top_candidates = _top_candidates(alpha_deltas)
    gate_metrics = _gate_metrics(gates, correlations, wf_gates, wf_stability)
    variant_metrics = _variant_metrics(report_dir)
    paths = _paths(report_dir)
    _write_frames(paths, alpha_metrics, alpha_deltas, top_candidates, gate_metrics, variant_metrics)
    paths.summary.write_text(_summary(alpha_deltas, top_candidates, variant_metrics), encoding="utf-8")
    return paths


def _read(report_dir: Path, name: str) -> pd.DataFrame:
    path = report_dir / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _alpha_metrics(metrics: pd.DataFrame, exposure: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return metrics
    merged = metrics.merge(exposure, on=["alpha", "variant"], how="left")
    soft_rank = _variant_rank(merged, "soft_aggressive")
    base_rank = _variant_rank(merged, "baseline")
    merged = merged.merge(soft_rank, on="alpha", how="left")
    merged = merged.merge(base_rank, on="alpha", how="left")
    merged["top10_by_soft_aggressive_return"] = merged["soft_aggressive_return_rank"].le(10)
    return merged.sort_values(["soft_aggressive_return_rank", "alpha", "variant"]).reset_index(drop=True)


def _variant_rank(frame: pd.DataFrame, variant: str) -> pd.DataFrame:
    ranked = frame.loc[frame["variant"].eq(variant), ["alpha", "return_pct"]].copy()
    column = f"{variant}_return_rank"
    ranked[column] = ranked["return_pct"].rank(method="first", ascending=False).astype(int)
    return ranked[["alpha", column]]


def _alpha_deltas(alpha_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for alpha, frame in alpha_metrics.groupby("alpha", sort=False):
        base = _variant_row(frame, "baseline")
        soft = _variant_row(frame, "soft_aggressive")
        hard = _variant_row(frame, "hard_gate")
        rows.append(_delta_row(alpha, base, soft, hard))
    return pd.DataFrame(rows).sort_values("soft_return_pct", ascending=False).reset_index(drop=True)


def _variant_row(frame: pd.DataFrame, variant: str) -> pd.Series:
    match = frame.loc[frame["variant"].eq(variant)]
    return match.iloc[0] if not match.empty else pd.Series(dtype=object)


def _delta_row(alpha: str, base: pd.Series, soft: pd.Series, hard: pd.Series) -> dict[str, object]:
    soft_return = _num(soft, "return_pct")
    base_return = _num(base, "return_pct")
    return {
        "alpha": alpha,
        "soft_return_rank": int(_num(soft, "soft_aggressive_return_rank")),
        "baseline_return_rank": int(_num(base, "baseline_return_rank")),
        "soft_return_pct": soft_return,
        "baseline_return_pct": base_return,
        "soft_return_delta_pct": soft_return - base_return,
        "soft_return_retention": _ratio(soft_return, base_return),
        "soft_sharpe": _num(soft, "ann_sharpe"),
        "baseline_sharpe": _num(base, "ann_sharpe"),
        "soft_sharpe_delta": _num(soft, "ann_sharpe") - _num(base, "ann_sharpe"),
        "soft_max_dd_pct": _num(soft, "max_drawdown_pct"),
        "baseline_max_dd_pct": _num(base, "max_drawdown_pct"),
        "soft_drawdown_improvement_pct": _num(soft, "max_drawdown_pct") - _num(base, "max_drawdown_pct"),
        "soft_latest_1m_sharpe": _num(soft, "latest_1m_rolling_sharpe"),
        "soft_negative_1m_rate": _num(soft, "negative_1m_sharpe_rate"),
        "hard_return_pct": _num(hard, "return_pct"),
        "hard_sharpe": _num(hard, "ann_sharpe"),
        "soft_avg_exposure": _num(soft, "avg_exposure_multiplier"),
        "soft_active_day_pct": _num(soft, "active_day_pct"),
        "soft_turnover": _num(soft, "scaled_turnover_est"),
        "soft_positive_windows_reduced": int(_num(soft, "positive_windows_reduced")),
        "soft_negative_windows_reduced": int(_num(soft, "negative_windows_reduced")),
    }


def _top_candidates(deltas: pd.DataFrame) -> pd.DataFrame:
    if deltas.empty:
        return deltas
    frame = deltas.head(10).copy()
    frame["candidate_tier"] = np.where(frame["soft_return_rank"].le(5), "core_return_engine", "validation_candidate")
    frame["soft_beats_baseline_return"] = frame["soft_return_delta_pct"].gt(0.0)
    frame["soft_beats_baseline_sharpe"] = frame["soft_sharpe_delta"].gt(0.0)
    frame["soft_reduces_drawdown"] = frame["soft_drawdown_improvement_pct"].gt(0.0)
    frame["passes_all_in_sample_gates"] = frame[
        ["soft_beats_baseline_return", "soft_beats_baseline_sharpe", "soft_reduces_drawdown"]
    ].all(axis=1)
    return frame


def _gate_metrics(
    gates: pd.DataFrame,
    correlations: pd.DataFrame,
    wf_gates: pd.DataFrame,
    wf_stability: pd.DataFrame,
) -> pd.DataFrame:
    frame = _gate_base(gates)
    frame = frame.merge(_best_correlations(correlations), on="alpha", how="left")
    frame = frame.merge(_latest_fold_gates(wf_gates), on="alpha", how="left")
    frame = frame.merge(wf_stability.add_prefix("wf_"), left_on="alpha", right_on="wf_alpha", how="left")
    return frame.drop(columns=["wf_alpha"], errors="ignore")


def _gate_base(gates: pd.DataFrame) -> pd.DataFrame:
    if gates.empty:
        return pd.DataFrame(columns=["alpha"])
    cols = ["alpha", "family", "indicator", "side", "coverage", "score", "lift_bps", "on_return_bps", "off_return_bps"]
    return gates.loc[gates["decision"].eq("activate"), cols].rename(columns={col: f"full_gate_{col}" for col in cols if col != "alpha"})


def _best_correlations(correlations: pd.DataFrame) -> pd.DataFrame:
    if correlations.empty:
        return pd.DataFrame(columns=["alpha"])
    frame = correlations.copy()
    frame["abs_return_spearman"] = frame["return_spearman"].abs()
    best = frame.sort_values("abs_return_spearman", ascending=False).groupby("alpha", as_index=False).head(1)
    return best[["alpha", "indicator", "return_spearman", "underperform_corr", "overperform_corr"]].rename(
        columns={col: f"best_corr_{col}" for col in ["indicator", "return_spearman", "underperform_corr", "overperform_corr"]}
    )


def _latest_fold_gates(wf_gates: pd.DataFrame) -> pd.DataFrame:
    if wf_gates.empty:
        return pd.DataFrame(columns=["alpha"])
    cols = ["alpha", "fold", "indicator", "side", "coverage", "score", "lift_bps", "test_start", "test_end"]
    return wf_gates[cols].rename(columns={col: f"wf_gate_{col}" for col in cols if col != "alpha"})


def _variant_metrics(report_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for name, scope in [("soft_throttle_2yr_aggregate.csv", "in_sample_2yr"), ("soft_throttle_walk_forward_aggregate.csv", "walk_forward")]:
        frame = _read(report_dir, name)
        if not frame.empty:
            frame.insert(0, "scope", scope)
            frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _paths(report_dir: Path) -> EvidenceMetricsPaths:
    return EvidenceMetricsPaths(
        alpha_metrics=report_dir / "evidence_alpha_metrics.csv",
        alpha_deltas=report_dir / "evidence_alpha_deltas.csv",
        top_candidates=report_dir / "evidence_top10_candidates.csv",
        gate_metrics=report_dir / "evidence_gate_metrics.csv",
        variant_metrics=report_dir / "evidence_variant_metrics.csv",
        summary=report_dir / "evidence_summary.md",
    )


def _write_frames(
    paths: EvidenceMetricsPaths,
    alpha_metrics: pd.DataFrame,
    alpha_deltas: pd.DataFrame,
    top_candidates: pd.DataFrame,
    gate_metrics: pd.DataFrame,
    variant_metrics: pd.DataFrame,
) -> None:
    alpha_metrics.to_csv(paths.alpha_metrics, index=False)
    alpha_deltas.to_csv(paths.alpha_deltas, index=False)
    top_candidates.to_csv(paths.top_candidates, index=False)
    gate_metrics.to_csv(paths.gate_metrics, index=False)
    variant_metrics.to_csv(paths.variant_metrics, index=False)


def _summary(deltas: pd.DataFrame, top: pd.DataFrame, variants: pd.DataFrame) -> str:
    lines = ["# Evidence Metrics Summary", ""]
    lines.extend(_summary_counts(deltas, top))
    lines.extend(["", "## Variant Metrics", "", _markdown(variants)])
    lines.extend(["", "## Top 10 Candidates", "", _markdown(top)])
    lines.extend(["", "## Limitations", "", "- Current walk-forward evidence is one latest fold only.", "- Multi-fold OOS is still required to prove stability."])
    return "\n".join(lines) + "\n"


def _summary_counts(deltas: pd.DataFrame, top: pd.DataFrame) -> list[str]:
    if deltas.empty:
        return ["No alpha metrics available."]
    return [
        f"- Alpha count: {len(deltas)}",
        f"- Top-10 candidates: {len(top)}",
        f"- Soft throttle improves return: {int(deltas['soft_return_delta_pct'].gt(0.0).sum())}",
        f"- Soft throttle improves Sharpe: {int(deltas['soft_sharpe_delta'].gt(0.0).sum())}",
        f"- Soft throttle reduces drawdown: {int(deltas['soft_drawdown_improvement_pct'].gt(0.0).sum())}",
        f"- Top-10 passing all in-sample gates: {int(top.get('passes_all_in_sample_gates', pd.Series(dtype=bool)).sum())}",
    ]


def _markdown(frame: pd.DataFrame, max_rows: int = 12) -> str:
    if frame.empty:
        return "_No rows._"
    view = frame.head(max_rows).copy()
    header = "| " + " | ".join(view.columns) + " |"
    separator = "| " + " | ".join("---" for _ in view.columns) + " |"
    rows = [header, separator]
    for _, row in view.iterrows():
        rows.append("| " + " | ".join(_cell(row[col]) for col in view.columns) + " |")
    return "\n".join(rows)


def _cell(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _num(row: pd.Series, column: str) -> float:
    value = row.get(column, np.nan)
    return float(value) if pd.notna(value) else float("nan")


def _ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else float("nan")
