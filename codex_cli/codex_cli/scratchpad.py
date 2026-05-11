from __future__ import annotations

from .models import Task
from .paths import ProjectPaths


SCRATCHPAD_TEMPLATE = """# Task: {objective}

## Objective
- {objective}

## Files
{files}

## Constraints
{constraints}

## Done Conditions
{done_conditions}

## Decisions
- None recorded.
"""


class ScratchpadStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def create(self, task: Task) -> str:
        text = SCRATCHPAD_TEMPLATE.format(
            objective=task.objective,
            files=self._render_lines(task.files),
            constraints=self._render_lines(task.constraints),
            done_conditions=self._render_lines(task.done_conditions),
        )
        self.write(task.id, text)
        return text

    def read(self, task_id: str) -> str:
        path = self.paths.scratchpads / f"{task_id}.md"
        if not path.exists():
            raise FileNotFoundError(f"Scratchpad not found: {task_id}")
        return path.read_text(encoding="utf-8")

    def write(self, task_id: str, text: str) -> None:
        if len(text.splitlines()) > 400:
            raise ValueError("Scratchpad exceeds 400 line limit")
        path = self.paths.scratchpads / f"{task_id}.md"
        path.write_text(text, encoding="utf-8")

    def _render_lines(self, items: tuple[str, ...]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- None recorded."
