from __future__ import annotations

import json
from pathlib import Path

from .models import MemoryEntry, Task
from .paths import ProjectPaths


class MemoryStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def create_summary(self, task: Task, title: str, body: str, tags: tuple[str, ...]) -> MemoryEntry:
        entry = MemoryEntry(
            kind="summary",
            title=title,
            body=body,
            tags=tags,
            source_task_id=task.id,
        )
        self._write_entry(self.paths.summaries / f"{task.id}.json", entry)
        return entry

    def list_documents(self) -> list[Path]:
        roots = (
            self.paths.decisions,
            self.paths.lessons,
            self.paths.patterns,
            self.paths.bugs,
            self.paths.summaries,
        )
        documents: list[Path] = []
        for root in roots:
            documents.extend(sorted(root.glob("*")))
        return documents

    def _write_entry(self, path: Path, entry: MemoryEntry) -> None:
        path.write_text(json.dumps(entry.to_dict(), indent=2) + "\n", encoding="utf-8")
