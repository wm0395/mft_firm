from __future__ import annotations

from .models import Subtask, Task


def plan_task(task: Task) -> dict[str, object]:
    if task.subtasks:
        subtasks = task.subtasks
    else:
        subtasks = [
            Subtask(
                id=1,
                desc=task.description,
                layer="",
                inputs=[],
                outputs=[],
                files=task.files,
            )
        ]
        task.subtasks = subtasks

    return {
        "task": task.description,
        "subtasks": [subtask.to_dict() for subtask in subtasks],
        "constraints": [
            "one subtask = one layer",
            "respect pipeline order",
            "avoid unnecessary abstraction",
            "prefer minimal working solution",
            "code must remain readable",
        ],
        "risks": [
            "scope creep",
            "hidden coupling",
            "architecture drift",
        ],
    }
