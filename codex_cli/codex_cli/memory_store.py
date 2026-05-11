from __future__ import annotations

import json
from pathlib import Path

from .models import MemoryEntry, Task
from .paths import ProjectPaths


ENTRY_DIRECTORIES = {
    "summaries": "summaries",
    "decisions": "decisions",
    "patterns": "patterns",
    "bugs": "bugs",
    "lessons": "lessons",
}


class MemoryStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def create_summary(self, task: Task, title: str, body: str, tags: tuple[str, ...]) -> MemoryEntry:
        return self.create_entry("summaries", task, title, body, tags)

    def create_entry(
        self,
        kind: str,
        task: Task,
        title: str,
        body: str,
        tags: tuple[str, ...],
    ) -> MemoryEntry:
        directory = self._directory_for_kind(kind)
        ref = self._next_ref(kind, task.id, title)
        entry = MemoryEntry(
            kind=kind,
            title=title,
            body=body,
            tags=tags,
            source_task_id=task.id,
            ref=ref,
        )
        self._write_entry(directory / Path(ref).name, entry)
        return entry

    def read_entry(self, ref: str) -> MemoryEntry:
        path = self.paths.memory / ref
        if not path.exists():
            raise FileNotFoundError(f"Memory entry not found: {ref}")
        return MemoryEntry(**json.loads(path.read_text(encoding="utf-8")))

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

    def _directory_for_kind(self, kind: str) -> Path:
        directory_name = ENTRY_DIRECTORIES.get(kind)
        if directory_name is None:
            raise ValueError(f"Unsupported memory entry kind: {kind}")
        return getattr(self.paths, directory_name)

    def _safe_title(self, title: str) -> str:
        cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in title).strip("_")
        return cleaned[:48] or "entry"

    def _next_ref(self, kind: str, task_id: str, title: str) -> str:
        directory = self._directory_for_kind(kind)
        stem = f"{task_id}_{self._safe_title(title)}"
        count = len(tuple(directory.glob(f"{stem}*.json"))) + 1
        suffix = f"_{count:03d}" if count > 1 else ""
        return f"{kind}/{stem}{suffix}.json"
