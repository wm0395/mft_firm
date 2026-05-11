from __future__ import annotations

from .models import Task
from .paths import ProjectPaths


class ScratchpadStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def create(self, task: Task) -> str:
        text = self.render(task)
        self.write(task.id, text)
        return text

    def refresh(self, task: Task) -> str:
        text = self.render(task)
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

    def render(self, task: Task) -> str:
        latest_run = task.run_history[-1] if task.run_history else {}
        history = self._render_history(task.run_history)
        return "\n".join(
            (
                f"# Task: {task.objective}",
                "",
                "## Objective",
                f"- {task.objective}",
                "",
                "## Files",
                self._render_lines(task.files),
                "",
                "## Constraints",
                self._render_lines(task.constraints),
                "",
                "## Done Conditions",
                self._render_lines(task.done_conditions),
                "",
                "## Understanding",
                self._render_text(latest_run.get("understanding")),
                "",
                "## Plan",
                self._render_text(latest_run.get("plan")),
                "",
                "## Execution History",
                history,
                "",
                "## Current Status",
                self._render_status(task, latest_run),
                "",
            )
        )

    def _render_lines(self, items: tuple[str, ...]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- None recorded."

    def _render_history(self, runs: tuple[dict[str, object], ...]) -> str:
        if not runs:
            return "- No managed runs recorded."
        entries = [self._render_run(run) for run in runs[-5:]]
        return "\n\n".join(entries)

    def _render_run(self, run: dict[str, object]) -> str:
        lines = [
            f"### Run: {run.get('finished_at', run.get('started_at', 'unknown'))}",
            f"- Provider: {run.get('provider', 'unknown')}",
            f"- Outcome: {run.get('status', 'unknown')}",
            f"- Summary: {run.get('summary') or 'None recorded.'}",
            f"- Actions Taken: {self._inline_items(run.get('actions_taken'))}",
            f"- Files Changed: {self._inline_items(run.get('files_changed'))}",
            f"- Checks Run: {self._inline_items(run.get('checks_run'))}",
            f"- Open Issues: {self._inline_items(run.get('open_issues'))}",
            f"- Final Decision: {run.get('final_decision') or 'None recorded.'}",
        ]
        return "\n".join(lines)

    def _render_status(self, task: Task, latest_run: dict[str, object]) -> str:
        return "\n".join(
            (
                f"- Task Status: {task.status}",
                f"- Review Status: {task.review_status}",
                f"- Last Outcome: {latest_run.get('status', 'pending')}",
                f"- Open Issues: {self._inline_items(latest_run.get('open_issues'))}",
            )
        )

    def _render_text(self, value: object) -> str:
        text = str(value).strip() if value else ""
        return text if text else "- None recorded."

    def _inline_items(self, value: object) -> str:
        if not value:
            return "None recorded."
        if isinstance(value, (list, tuple)):
            items = [str(item) for item in value if str(item).strip()]
            return ", ".join(items) if items else "None recorded."
        return str(value)
