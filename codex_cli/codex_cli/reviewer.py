from __future__ import annotations

from .models import Task


CHECKLIST = (
    "boundary violation",
    "coupling issue",
    "unclear ownership",
    "non-deterministic logic",
)


def review_task(task: Task) -> dict[str, object]:
    issues: list[str] = []
    suggestions: list[str] = []

    if not task.subtasks:
        suggestions.append("Record at least one subtask for auditability.")

    if not task.files:
        suggestions.append("Attach relevant files before implementation when possible.")

    return {
        "verdict": "accept" if not issues else "revise",
        "architecture_violations": issues,
        "coupling_issues": [],
        "fix_instructions": suggestions,
        "issues": issues,
        "suggestions": suggestions,
        "checklist": list(CHECKLIST),
    }
