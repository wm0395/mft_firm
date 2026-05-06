from __future__ import annotations

import json
from pathlib import Path

from .models import COMPLETED, Task
from .paths import ProjectPaths


class TaskStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def create(self, description: str, route: str) -> Task:
        task = Task(
            id=self._next_id(),
            description=description,
            route=route,
        )
        self.save(task)
        return task

    def get(self, task_id: str) -> Task:
        for base in (self.paths.active_tasks, self.paths.completed_tasks):
            path = base / f"{task_id}.json"
            if path.exists():
                return Task.from_dict(json.loads(path.read_text(encoding="utf-8")))
        raise FileNotFoundError(f"Task not found: {task_id}")

    def save(self, task: Task) -> None:
        task.touch()
        directory = self.paths.completed_tasks if task.status == COMPLETED else self.paths.active_tasks
        path = directory / f"{task.id}.json"
        path.write_text(json.dumps(task.to_dict(), indent=2) + "\n", encoding="utf-8")

        other = self.paths.completed_tasks if directory == self.paths.active_tasks else self.paths.active_tasks
        other_path = other / f"{task.id}.json"
        if other_path.exists():
            other_path.unlink()

    def complete(self, task_id: str) -> Task:
        task = self.get(task_id)
        task.status = COMPLETED
        self.save(task)
        return task

    def list_active(self) -> list[Task]:
        return self._list(self.paths.active_tasks)

    def _list(self, directory: Path) -> list[Task]:
        tasks = []
        for path in sorted(directory.glob("task_*.json")):
            tasks.append(Task.from_dict(json.loads(path.read_text(encoding="utf-8"))))
        return tasks

    def _next_id(self) -> str:
        numbers = []
        for directory in (self.paths.active_tasks, self.paths.completed_tasks):
            for path in directory.glob("task_*.json"):
                try:
                    numbers.append(int(path.stem.split("_", 1)[1]))
                except (IndexError, ValueError):
                    continue
        return f"task_{max(numbers, default=0) + 1:03d}"
