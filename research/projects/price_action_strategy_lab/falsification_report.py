from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class FalsificationReportPaths:
    results: Path
    markdown: Path


def write_falsification_report(report_dir: Path) -> FalsificationReportPaths:
    hypotheses = _read(report_dir, "alpha_regime_hypothesis_book.csv")
    results = falsification_results(hypotheses)
    paths = FalsificationReportPaths(
        report_dir / "alpha_regime_falsification_report.csv",
        report_dir / "alpha_regime_falsification_report.md",
    )
    results.to_csv(paths.results, index=False)
    paths.markdown.write_text(_markdown(results), encoding="utf-8")
    return paths


def falsification_results(hypotheses: pd.DataFrame) -> pd.DataFrame:
    if hypotheses.empty:
        return pd.DataFrame()
    frame = hypotheses.copy()
    frame["right_tail_pass"] = frame["right_tail_retention"].ge(0.95)
    frame["left_tail_pass"] = frame["left_tail_delta_pct"].gt(0.0)
    frame["ci_pass"] = frame["delta_ci_low_pct"].gt(0.0)
    frame["pvalue_pass"] = frame["paired_p_value"].lt(0.05)
    frame["stability_pass"] = frame["top_indicator_rate"].fillna(0.0).ge(0.50)
    frame["exposure_form_pass"] = frame["variant"].ne("hard_gate")
    frame["falsification_status"] = frame.apply(_status, axis=1)
    frame["failure_reasons"] = frame.apply(_failure_reasons, axis=1)
    columns = [col for col in _columns() if col in frame.columns]
    return frame.sort_values(["falsification_status", "hypothesis_score"], ascending=[True, False])[columns]


def _status(row: pd.Series) -> str:
    if not bool(row["right_tail_pass"]):
        return "falsified_right_tail_loss"
    if not bool(row["left_tail_pass"]):
        return "falsified_no_left_tail_help"
    if not bool(row["ci_pass"]) or not bool(row["pvalue_pass"]):
        return "not_significant"
    if not bool(row["stability_pass"]):
        return "not_stable"
    return "passes_initial_falsification"


def _failure_reasons(row: pd.Series) -> str:
    reasons = []
    checks = {
        "right_tail<95%": row["right_tail_pass"],
        "left_tail<=0": row["left_tail_pass"],
        "ci_low<=0": row["ci_pass"],
        "pvalue>=0.05": row["pvalue_pass"],
        "top_indicator_rate<50%": row["stability_pass"],
        "hard_gate_form": row["exposure_form_pass"],
    }
    for reason, passed in checks.items():
        if not bool(passed):
            reasons.append(reason)
    return ",".join(reasons)


def _columns() -> list[str]:
    return [
        "alpha",
        "variant",
        "indicator",
        "side",
        "falsification_status",
        "failure_reasons",
        "hypothesis_score",
        "mean_delta_vs_baseline_pct",
        "delta_ci_low_pct",
        "paired_p_value",
        "left_tail_delta_pct",
        "right_tail_retention",
        "max_drawdown_delta_pct",
        "top_indicator_rate",
        "selection_count",
        "left_tail_count",
        "right_tail_count",
    ]


def _markdown(results: pd.DataFrame) -> str:
    lines = ["# Alpha Regime Falsification Report", "", "## Status Counts", ""]
    lines.append(_markdown_table(_status_counts(results)))
    lines.extend(["", "## Top Rows", "", _markdown_table(results.head(20)), ""])
    lines.extend(["## Acceptance Contract", ""])
    lines.append("- Right-tail retention must be at least 95%.")
    lines.append("- Bootstrap lower CI and paired p-value must both clear significance.")
    lines.append("- Top indicator rate must be at least 50% before promotion.")
    lines.append("- Rows failing these tests remain research-only or rejected.")
    return "\n".join(lines)


def _status_counts(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame()
    counts = results["falsification_status"].value_counts().reset_index()
    counts.columns = ["falsification_status", "count"]
    return counts


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
