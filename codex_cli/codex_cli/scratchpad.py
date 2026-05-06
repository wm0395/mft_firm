from __future__ import annotations

from .models import Task
from .paths import ProjectPaths


SCRATCHPAD_TEMPLATE = """# Task: {description}

## Understanding
- Task id: {task_id}
- Route: {route}

## Plan
1. Keep the implementation minimal.
2. Execute only the requested task.
3. Run reviewer checks before completion.

## Open Questions
- None recorded.

## Decisions
- Created deterministic scratchpad from task metadata.
"""


class ScratchpadStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def create(self, task: Task) -> str:
        text = SCRATCHPAD_TEMPLATE.format(
            description=task.description,
            task_id=task.id,
            route=task.route,
        )
        self.write(task.id, text)
        return text

    def read(self, task_id: str) -> str:
        path = self.paths.scratchpads / f"{task_id}.md"
        if not path.exists():
            raise FileNotFoundError(f"Scratchpad not found: {task_id}")
        return path.read_text(encoding="utf-8")

    def write(self, task_id: str, text: str) -> None:
        line_count = len(text.splitlines())
        if line_count > 400:
            raise ValueError("Scratchpad exceeds 400 line limit")
        path = self.paths.scratchpads / f"{task_id}.md"
        path.write_text(text, encoding="utf-8")
