from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from project.cli_operator import _doctor_payload, _workflow_status_payload
from project.cli_support import load_json
from project.data.quality import build_data_quality_report
from project.data.repository import DataRepository
from project.ui.views.common import StatusCardView, WorkflowStepView
from project.ui.views.mission_control_actions import (
    recommended_action_text,
    target_page,
)


@dataclass(frozen=True)
class RecommendedActionView:
    title: str
    explanation: str
    button_label: str
    command: str
    target_page: str
    workflow_context_key: str | None
    workflow_context_value: str | None
    is_executable: bool
    disabled_reason: str | None


@dataclass(frozen=True)
class WarningView:
    title: str
    why_it_matters: str
    recommended_action: str


@dataclass(frozen=True)
class ActivityView:
    title: str
    detail: str
    timestamp: str


@dataclass(frozen=True)
class MissionControlView:
    health: str
    cards: tuple[StatusCardView, ...]
    workflow_steps: tuple[WorkflowStepView, ...]
    recommended_action: RecommendedActionView
    warnings: tuple[WarningView, ...]
    recent_activity: tuple[ActivityView, ...]
    debug_payload: dict[str, object]


def get_mission_control_view(repository: DataRepository) -> MissionControlView:
    workflow = _workflow_status_payload(repository)
    doctor = _doctor_payload(repository)
    assets = repository.list_assets()
    quality_report = _quality_report(repository, tuple(asset.symbol for asset in assets))
    warnings = _warnings(workflow, doctor, quality_report, repository)
    cards = _cards(workflow, doctor, quality_report, repository)
    steps = _steps(workflow, doctor, repository)
    activity = _recent_activity(workflow, repository)
    return MissionControlView(
        health=_health_state(workflow, doctor, warnings),
        cards=cards,
        workflow_steps=steps,
        recommended_action=_recommended_action(workflow),
        warnings=warnings,
        recent_activity=activity,
        debug_payload={
            "workflow": workflow,
            "doctor": doctor,
            "quality_report": _quality_payload(quality_report),
        },
    )


def _quality_report(
    repository: DataRepository,
    symbols: tuple[str, ...],
):
    if not symbols:
        return None
    try:
        return build_data_quality_report(repository, symbols)
    except Exception:
        return None


def _quality_payload(report: object | None) -> object:
    if report is None:
        return None
    return getattr(report, "__dict__", report)


def _cards(
    workflow: dict[str, object],
    doctor: dict[str, object],
    report: object | None,
    repository: DataRepository,
) -> tuple[StatusCardView, ...]:
    return (
        _system_health_card(workflow, doctor),
        _data_coverage_card(workflow, report),
        _research_runs_card(repository),
        _trade_ideas_card(repository),
        _hypotheses_card(repository),
        _validation_card(repository),
    )


def _system_health_card(
    workflow: dict[str, object],
    doctor: dict[str, object],
) -> StatusCardView:
    return StatusCardView(
        "System Health",
        _health_score(workflow, doctor),
        _status(workflow),
        "Overall operating state",
    )


def _data_coverage_card(
    workflow: dict[str, object],
    report: object | None,
) -> StatusCardView:
    return StatusCardView(
        "Data Coverage",
        f"{workflow['assets']} assets",
        _quality_status(report),
        f"{workflow['market_data_rows']} market rows",
    )


def _research_runs_card(repository: DataRepository) -> StatusCardView:
    runs = repository.get_research_runs()
    return StatusCardView(
        "Research Runs",
        str(len(runs)),
        "ok" if runs else "warning",
        "Latest research activity",
    )


def _trade_ideas_card(repository: DataRepository) -> StatusCardView:
    open_trade_ideas = len(repository.get_open_trade_ideas())
    return StatusCardView(
        "Trade Ideas",
        str(open_trade_ideas),
        "ok" if open_trade_ideas == 0 else "action",
        "Awaiting human review",
    )


def _hypotheses_card(repository: DataRepository) -> StatusCardView:
    counts = _hypothesis_counts(repository)
    return StatusCardView(
        "Hypotheses",
        f"{counts['testing']} testing",
        "ok" if counts["testing"] == 0 else "warning",
        f"{counts['active']} active, {counts['draft']} draft",
    )


def _validation_card(repository: DataRepository) -> StatusCardView:
    failures = _validation_failure_count(repository)
    return StatusCardView(
        "Validation",
        str(failures),
        "ok" if failures == 0 else "warning",
        "Recent validation failures",
    )


def _steps(
    workflow: dict[str, object],
    doctor: dict[str, object],
    repository: DataRepository,
) -> tuple[WorkflowStepView, ...]:
    counts = _hypothesis_counts(repository)
    open_trade_ideas = len(repository.get_open_trade_ideas())
    return (
        WorkflowStepView("Setup", _step_state(workflow["database"] != "ok"), "Database schema and health"),
        WorkflowStepView("Data", _step_state(not workflow["assets"]), "Assets and market rows"),
        WorkflowStepView("Snapshot", _step_state(not workflow["dataset_snapshots"]), "Reproducible dataset snapshots"),
        WorkflowStepView("Research", _step_state(not workflow["latest_research_run"]), "Research project runs"),
        WorkflowStepView(
            "Hypothesis Review",
            _step_state(counts["testing"] or counts["draft"] or _validation_failure_count(repository)),
            "Lifecycle readiness and blockers",
        ),
        WorkflowStepView(
            "Trade Review",
            _step_state(open_trade_ideas > 0),
            "Human review queue",
        ),
        WorkflowStepView("Learning", _step_state(not repository.get_backtest_results()), "Backtests and feedback loop"),
    )


def _recent_activity(
    workflow: dict[str, object],
    repository: DataRepository,
) -> tuple[ActivityView, ...]:
    activity: list[ActivityView] = []
    run = cast(dict[str, object] | None, workflow.get("latest_research_run"))
    if run is not None:
        activity.append(
            ActivityView(
                "Latest research run",
                str(run.get("status", "unknown")),
                str(run.get("started_at", "")),
            )
        )
    backtest = cast(dict[str, object] | None, workflow.get("latest_backtest"))
    if backtest is not None:
        activity.append(
            ActivityView(
                "Latest backtest",
                f"{backtest.get('hypothesis_id', '')} {backtest.get('total_return_pct', '')}",
                str(backtest.get("start_timestamp", "")),
            )
        )
    if (trade := _latest_trade_idea(repository)):
        activity.append(
            ActivityView(
                "Latest trade idea",
                f"{trade.asset_id} {trade.direction} {trade.confidence:.2f}",
                trade.timestamp,
            )
        )
    return tuple(activity)


def _warnings(
    workflow: dict[str, object],
    doctor: dict[str, object],
    report: object | None,
    repository: DataRepository,
) -> tuple[WarningView, ...]:
    warnings: list[WarningView] = []
    _append_database_warning(workflow, warnings)
    _append_snapshot_warning(workflow, warnings)
    _append_validation_warning(repository, warnings)
    if report is not None and getattr(report, "status", "") in {"warn", "fail"}:
        warnings.extend(_quality_warnings(report))
    _append_doctor_warning(doctor, warnings)
    return tuple(warnings)


def _append_database_warning(
    workflow: dict[str, object],
    warnings: list[WarningView],
) -> None:
    if workflow["database"] == "ok":
        return
    warnings.append(
        WarningView(
            "Database status needs attention",
            "The cockpit cannot rely on complete state until the schema is healthy.",
            "Initialize or repair the local database.",
        )
    )


def _append_snapshot_warning(
    workflow: dict[str, object],
    warnings: list[WarningView],
) -> None:
    if workflow["dataset_snapshots"]:
        return
    warnings.append(
        WarningView(
            "No dataset snapshot exists",
            "Research runs need reproducible dataset snapshots.",
            "Create a dataset snapshot from the Data page.",
        )
    )


def _append_validation_warning(
    repository: DataRepository,
    warnings: list[WarningView],
) -> None:
    failures = _validation_failure_count(repository)
    if failures == 0:
        return
    warnings.append(
        WarningView(
            f"{failures} validation failure(s)",
            "Invalid evaluations reduce confidence in promoted hypotheses.",
            "Open Hypotheses or Explainability to inspect blockers.",
        )
    )


def _append_doctor_warning(
    doctor: dict[str, object],
    warnings: list[WarningView],
) -> None:
    if doctor.get("status") != "fail":
        return
    warnings.append(
        WarningView(
            "Doctor check failed",
            "A required table or source check did not pass.",
            "Resolve the failing check before promoting decisions.",
        )
    )


def _quality_warnings(report: object) -> tuple[WarningView, ...]:
    symbols = cast(tuple[Any, ...], getattr(report, "symbols", ()))
    items: list[WarningView] = []
    for symbol in symbols:
        if getattr(symbol, "status", "ok") == "ok":
            continue
        detail = ", ".join(getattr(symbol, "errors", ()) or getattr(symbol, "warnings", ()))
        items.append(
            WarningView(
                f"Data issue for {getattr(symbol, 'symbol', 'unknown')}",
                detail or "Data freshness or quality needs review.",
                f"Review {getattr(symbol, 'symbol', 'unknown')} in the Data page.",
            )
        )
    return tuple(items[:3])


def _recommended_action(workflow: dict[str, object]) -> RecommendedActionView:
    command = str(workflow.get("next_recommended_command", ""))
    title, explanation, button = recommended_action_text(command)
    return RecommendedActionView(
        title,
        explanation,
        button,
        command,
        target_page(command),
        "workflow_action_command" if command else None,
        command or None,
        bool(command),
        None if command else "No recommended action is available.",
    )


def _health_state(
    workflow: dict[str, object],
    doctor: dict[str, object],
    warnings: tuple[WarningView, ...],
) -> str:
    if workflow["database"] != "ok" or doctor.get("status") == "fail":
        return "Blocked"
    if warnings:
        return "Warning"
    return "Healthy"


def _health_score(workflow: dict[str, object], doctor: dict[str, object]) -> str:
    if workflow["database"] != "ok" or doctor.get("status") == "fail":
        return "Warning"
    return "OK"


def _status(workflow: dict[str, object]) -> str:
    return "ok" if workflow["database"] == "ok" else "warning"


def _quality_status(report: object | None) -> str:
    if report is None:
        return "unknown"
    return str(getattr(report, "status", "unknown"))


def _step_state(needs_attention: object) -> str:
    return "action required" if needs_attention else "ok"


def _hypothesis_counts(repository: DataRepository) -> dict[str, int]:
    counts = {"draft": 0, "testing": 0, "active": 0, "deprecated": 0, "archived": 0}
    for hypothesis in repository.get_hypotheses():
        counts[hypothesis.status] = counts.get(hypothesis.status, 0) + 1
    return counts


def _validation_failure_count(repository: DataRepository) -> int:
    count = 0
    for evaluation in repository.get_hypothesis_evaluations():
        payload = load_json(evaluation.validation_result_json)
        if payload and not payload.get("is_valid", True):
            count += 1
    return count


def _latest_trade_idea(repository: DataRepository):
    ideas = repository.get_trade_ideas()
    return ideas[-1] if ideas else None
