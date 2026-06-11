from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from research.projects.price_action_strategy_lab.validation_pipeline import ValidationArtifacts


def write_validation_reports(report_dir: Path, artifacts: ValidationArtifacts) -> dict[str, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "validation_folds": report_dir / "validation_folds.csv",
        "validation_summary": report_dir / "validation_summary.csv",
        "selector_results": report_dir / "selector_results.csv",
        "research_audit": report_dir / "research_audit.md",
        "embargo_failure": report_dir / "embargo_failure_diagnosis.md",
        "selector_robustness": report_dir / "selector_robustness.md",
        "decision_report": report_dir / "alpha_suite_decision_report.md",
    }
    artifacts.folds.to_csv(paths["validation_folds"], index=False)
    artifacts.summary.to_csv(paths["validation_summary"], index=False)
    artifacts.selector_results.to_csv(paths["selector_results"], index=False)
    paths["research_audit"].write_text(_research_audit_md(artifacts.audit), encoding="utf-8")
    paths["embargo_failure"].write_text(_embargo_failure_md(artifacts.embargo_diagnostics), encoding="utf-8")
    paths["selector_robustness"].write_text(
        _selector_robustness_md(artifacts.selector_results),
        encoding="utf-8",
    )
    paths["decision_report"].write_text(
        _decision_report_md(artifacts.decision, artifacts.summary),
        encoding="utf-8",
    )
    return paths


def _research_audit_md(audit: pd.DataFrame) -> str:
    if audit.empty:
        return "# Research Audit\n\n_No validation audit available._\n"
    row = audit.iloc[0].to_dict()
    lines = ["# Research Audit", ""]
    for key in (
        "panel_name",
        "alpha_count",
        "result_rows",
        "fold_rows",
        "schemes",
        "train_size",
        "test_size",
        "step_size",
        "lookahead",
        "embargo",
        "outer_folds",
        "bootstrap_reps",
        "bootstrap_block_length",
        "target_cost_bps",
        "min_active_days",
        "primary_scheme",
        "turnover_penalty_bps",
        "instability_penalty_bps",
    ):
        if key in row:
            lines.append(f"- {key}: {row[key]}")
    return "\n".join(lines) + "\n"


def _embargo_failure_md(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "# Embargo Failure Diagnosis\n\n_No embargo diagnostics available._\n"
    lines = ["# Embargo Failure Diagnosis", ""]
    lines.append(_markdown_table(frame, max_rows=10))
    if {"embargo_delta_bps", "walk_forward"}.issubset(frame.columns):
        worst = frame.sort_values("embargo_delta_bps").iloc[0]
        lines.extend(
            [
                "",
                f"- Worst embargo delta: {float(worst['embargo_delta_bps']):.3f} bps",
                f"- Selected row: {worst['alpha']} / {worst['mode']} / {int(worst['horizon'])}d",
            ]
        )
    return "\n".join(lines) + "\n"


def _selector_robustness_md(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "# Selector Robustness\n\n_No selector ranking available._\n"
    lines = ["# Selector Robustness", "", _markdown_table(frame, max_rows=10)]
    if "selector_score" in frame.columns:
        top = frame.sort_values("selector_score", ascending=False).iloc[0]
        lines.extend(
            [
                "",
                f"- top_candidate: {top.get('alpha', '')}",
                f"- top_selector_score: {float(top.get('selector_score', 0.0)):.3f}",
                f"- abstain: {bool(top.get('abstain', False))}",
            ]
        )
    return "\n".join(lines) + "\n"


def _decision_report_md(frame: pd.DataFrame, summary: pd.DataFrame) -> str:
    if frame.empty:
        return "# Alpha Suite Decision Report\n\n_No validation decision available._\n"
    row = frame.iloc[0].to_dict()
    lines = ["# Alpha Suite Decision Report", ""]
    lines.extend(
        [
            f"- decision: {row.get('decision', 'research_only')}",
            f"- chosen_name: {row.get('chosen_name', '')}",
            f"- chosen_alpha: {row.get('chosen_alpha', '')}",
            f"- selected_scheme: {row.get('selected_scheme', '')}",
            f"- selector_score: {float(row.get('selector_score', 0.0)):.3f}",
            f"- lower_bps: {float(row.get('lower_bps', 0.0)):.3f}",
            f"- fold_pass_rate: {float(row.get('fold_pass_rate', 0.0)):.3f}",
            f"- summary_rows: {int(row.get('summary_rows', 0))}",
        ]
    )
    if row.get("decision") != "promote":
        lines.extend(["", "- status: research_only", "- reason: validation gates did not clear"])
    lines.extend(["", _markdown_table(summary.head(10), max_rows=10)])
    return "\n".join(lines) + "\n"


def _markdown_table(frame: pd.DataFrame, max_rows: int = 10) -> str:
    if frame.empty:
        return "_No rows._"
    view = frame.head(max_rows).copy()
    columns = list(view.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = [header, separator]
    for _, row in view.iterrows():
        rows.append("| " + " | ".join(_format_cell(row[col]) for col in columns) + " |")
    return "\n".join(rows)


def _format_cell(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
