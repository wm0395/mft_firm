from __future__ import annotations

import json
from pathlib import Path

from .models import COMPLETED, Task
from .paths import ProjectPaths


class TaskStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def create(
        self,
        objective: str,
        files: tuple[str, ...],
        constraints: tuple[str, ...],
        done_conditions: tuple[str, ...],
        route: str,
        provider: str,
    ) -> Task:
        task = Task(
            id=self._next_id(),
            objective=objective,
            files=files,
            constraints=constraints,
            done_conditions=done_conditions,
            route=route,
            recommended_provider=provider,
        )
        self.save(task)
        return task

    def get(self, task_id: str) -> Task:
        path = self._find_path(task_id)
        return Task.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def save(self, task: Task) -> None:
        current = task.touch()
        directory = self.paths.completed_tasks if current.status == COMPLETED else self.paths.active_tasks
        self._write_task(directory / f"{current.id}.json", current)
        self._remove_shadow(directory, current.id)

    def complete(self, task_id: str) -> Task:
        task = self.get(task_id).complete()
        self.save(task)
        return task

    def list_active(self) -> list[Task]:
        return self._list(self.paths.active_tasks)

    def _find_path(self, task_id: str) -> Path:
        for directory in (self.paths.active_tasks, self.paths.completed_tasks):
            path = directory / f"{task_id}.json"
            if path.exists():
                return path
        raise FileNotFoundError(f"Task not found: {task_id}")

    def _write_task(self, path: Path, task: Task) -> None:
        path.write_text(json.dumps(task.to_dict(), indent=2) + "\n", encoding="utf-8")

    def _remove_shadow(self, directory: Path, task_id: str) -> None:
        other = self.paths.completed_tasks if directory == self.paths.active_tasks else self.paths.active_tasks
        other_path = other / f"{task_id}.json"
        if other_path.exists():
            other_path.unlink()

    def _list(self, directory: Path) -> list[Task]:
        return [self._read_task(path) for path in sorted(directory.glob("task_*.json"))]

    def _read_task(self, path: Path) -> Task:
        return Task.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def _next_id(self) -> str:
        numbers: list[int] = []
        for directory in (self.paths.active_tasks, self.paths.completed_tasks):
            for path in directory.glob("task_*.json"):
                parts = path.stem.split("_", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    numbers.append(int(parts[1]))
        return f"task_{max(numbers, default=0) + 1:03d}"
