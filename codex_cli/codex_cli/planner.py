from __future__ import annotations

from .models import Subtask, Task


DEFAULT_CONSTRAINTS = (
    "respect data → signals → hypotheses → trade_engine → decision",
    "no upward imports",
    "no DB access outside project/data/",
    "prefer minimal working solution",
)


def plan_task(task: Task) -> tuple[Task, dict[str, object]]:
    subtasks = task.subtasks or (_default_subtask(task),)
    planned = task.with_subtasks(subtasks)
    return planned, {
        "task_id": planned.id,
        "task": planned.objective,
        "subtasks": [subtask.to_dict() for subtask in planned.subtasks],
        "constraints": list(_merge_constraints(planned.constraints)),
        "risks": _risks(planned),
    }


def _default_subtask(task: Task) -> Subtask:
    return Subtask(id=1, objective=task.objective, files=task.files)


def _merge_constraints(constraints: tuple[str, ...]) -> tuple[str, ...]:
    merged = list(DEFAULT_CONSTRAINTS)
    for item in constraints:
        if item not in merged:
            merged.append(item)
    return tuple(merged)


def _risks(task: Task) -> list[str]:
    risks = ["scope creep", "architecture drift"]
    if not task.files:
        risks.append("missing target files")
    return risks
