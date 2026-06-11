from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class AlphaRegimeHypothesisBookPaths:
    hypotheses: Path
    markdown: Path


def write_alpha_regime_hypothesis_book(report_dir: Path) -> AlphaRegimeHypothesisBookPaths:
    alpha_tail = _read(report_dir, "tail_alpha_variant_diagnostics.csv")
    gates = _read(report_dir, "soft_throttle_walk_forward_selected_gates.csv")
    folds = _read(report_dir, "soft_throttle_walk_forward_fold_metrics.csv")
    stability = _read(report_dir, "soft_throttle_walk_forward_gate_stability.csv")
    hypotheses = alpha_regime_hypotheses(alpha_tail, gates, folds, stability)
    paths = AlphaRegimeHypothesisBookPaths(
        report_dir / "alpha_regime_hypothesis_book.csv",
        report_dir / "alpha_regime_hypothesis_book.md",
    )
    hypotheses.to_csv(paths.hypotheses, index=False)
    paths.markdown.write_text(_markdown(hypotheses), encoding="utf-8")
    return paths


def alpha_regime_hypotheses(
    alpha_tail: pd.DataFrame,
    gates: pd.DataFrame,
    folds: pd.DataFrame,
    stability: pd.DataFrame,
) -> pd.DataFrame:
    if alpha_tail.empty:
        return pd.DataFrame()
    candidates = _candidate_tail_rows(alpha_tail)
    enriched = candidates.merge(_top_gate_rows(gates, folds), on="alpha", how="left")
    enriched = enriched.merge(_stability_rows(stability), on="alpha", how="left")
    enriched["hypothesis_score"] = enriched.apply(_hypothesis_score, axis=1)
    enriched["hypothesis_status"] = enriched.apply(_hypothesis_status, axis=1)
    enriched["hypothesis_status_rank"] = enriched["hypothesis_status"].map(_status_rank)
    columns = [col for col in _columns() if col in enriched.columns]
    ranked = enriched.sort_values(["hypothesis_status_rank", "hypothesis_score"], ascending=[True, False])
    return ranked[columns]


def _candidate_tail_rows(alpha_tail: pd.DataFrame) -> pd.DataFrame:
    variants = {"soft_aggressive", "drawdown_only_throttle"}
    frame = alpha_tail.loc[alpha_tail["variant"].isin(variants)].copy()
    return frame.loc[frame["left_tail_delta_pct"].gt(0.0)]


def _top_gate_rows(gates: pd.DataFrame, folds: pd.DataFrame) -> pd.DataFrame:
    if gates.empty or folds.empty:
        return pd.DataFrame(columns=["alpha"])
    tagged = gates.copy()
    tagged["baseline_tail_bucket"] = tagged["fold"].map(_baseline_tail_buckets(folds))
    grouped = tagged.groupby(["alpha", "indicator", "side"], dropna=False)
    rows = [_gate_summary(keys, group) for keys, group in grouped]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=["alpha"])
    return frame.sort_values(["alpha", "left_tail_count", "selection_count"], ascending=[True, False, False]).drop_duplicates("alpha")


def _baseline_tail_buckets(folds: pd.DataFrame) -> dict[object, str]:
    baseline = folds.loc[folds["variant"].eq("baseline")]
    if baseline.empty:
        return {}
    left_cut = baseline["return_pct"].quantile(0.25)
    right_cut = baseline["return_pct"].quantile(0.75)
    return {
        row.fold: _tail_bucket(float(row.return_pct), float(left_cut), float(right_cut))
        for row in baseline.itertuples()
    }


def _tail_bucket(value: float, left_cut: float, right_cut: float) -> str:
    if value <= left_cut:
        return "left_tail"
    if value >= right_cut:
        return "right_tail"
    return "middle"


def _gate_summary(keys: tuple[object, object, object], group: pd.DataFrame) -> dict[str, object]:
    alpha, indicator, side = keys
    left = group.loc[group["baseline_tail_bucket"].eq("left_tail")]
    right = group.loc[group["baseline_tail_bucket"].eq("right_tail")]
    return {
        "alpha": str(alpha),
        "indicator": str(indicator),
        "side": str(side),
        "selection_count": int(len(group)),
        "left_tail_count": int(len(left)),
        "right_tail_count": int(len(right)),
        "mean_gate_score": float(group["score"].mean()),
        "mean_gate_lift_bps": float(group["lift_bps"].mean()),
    }


def _stability_rows(stability: pd.DataFrame) -> pd.DataFrame:
    if stability.empty:
        return pd.DataFrame(columns=["alpha"])
    columns = ["alpha", "top_indicator_rate", "unique_indicators", "activate_rate"]
    return stability[[col for col in columns if col in stability.columns]]


def _hypothesis_score(row: pd.Series) -> float:
    right_penalty = max(0.0, 0.95 - float(row.get("right_tail_retention", 0.0))) * 4.0
    significance = max(0.0, float(row.get("delta_ci_low_pct", 0.0))) * 4.0
    stability = float(row.get("top_indicator_rate", 0.0)) * 0.5
    return (
        float(row.get("left_tail_delta_pct", 0.0))
        + max(0.0, float(row.get("mean_delta_vs_baseline_pct", 0.0))) * 2.0
        + float(row.get("max_drawdown_delta_pct", 0.0))
        + significance
        + stability
        - right_penalty
    )


def _hypothesis_status(row: pd.Series) -> str:
    if float(row.get("delta_ci_low_pct", 0.0)) > 0.0:
        return "candidate_validate_next"
    if float(row.get("right_tail_retention", 0.0)) < 0.9:
        return "reject_right_tail_loss"
    return "research_only_needs_significance"


def _status_rank(status: str) -> int:
    order = {"candidate_validate_next": 0, "research_only_needs_significance": 1}
    return order.get(status, 2)


def _columns() -> list[str]:
    return [
        "alpha",
        "variant",
        "hypothesis_status",
        "hypothesis_score",
        "mean_delta_vs_baseline_pct",
        "delta_ci_low_pct",
        "paired_p_value",
        "left_tail_delta_pct",
        "right_tail_retention",
        "max_drawdown_delta_pct",
        "indicator",
        "side",
        "selection_count",
        "left_tail_count",
        "right_tail_count",
        "mean_gate_score",
        "mean_gate_lift_bps",
        "top_indicator_rate",
        "unique_indicators",
        "activate_rate",
    ]


def _markdown(hypotheses: pd.DataFrame) -> str:
    lines = ["# Alpha Regime Hypothesis Book", "", "## Top Hypotheses", ""]
    lines.append(_markdown_table(hypotheses.head(15)))
    lines.extend(["", "## Promotion Rules", ""])
    lines.append("- Promote only after positive lower CI under purged walk-forward validation.")
    lines.append("- Reject if right-tail retention falls below 90%.")
    lines.append("- Treat `research_only_needs_significance` as a lead, not a trading rule.")
    lines.append("- Re-test every indicator as lagged; do not use same-fold tuned gates as proof.")
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


def _read(report_dir: Path, name: str) -> pd.DataFrame:
    path = report_dir / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()
