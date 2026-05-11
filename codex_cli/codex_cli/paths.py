from __future__ import annotations

from pathlib import Path


class ProjectPaths:
    def __init__(self, root: Path | None = None) -> None:
        cwd = Path.cwd()
        self.package_root = Path(__file__).resolve().parent
        self.workspace_root = cwd
        self.root = root or cwd / "codex_cli"
        self.tasks = self.root / "tasks"
        self.active_tasks = self.tasks / "active"
        self.completed_tasks = self.tasks / "completed"
        self.memory = self.root / "memory"
        self.scratchpads = self.memory / "scratchpads"
        self.runs = self.memory / "runs"
        self.decisions = self.memory / "decisions"
        self.lessons = self.memory / "lessons"
        self.patterns = self.memory / "patterns"
        self.bugs = self.memory / "bugs"
        self.summaries = self.memory / "summaries"
        self.violations = self.memory / "violations"
        self.violation_patterns = self.violations / "patterns.json"
        self.cache = self.root / "cache"
        self.cache_index = self.cache / "index"
        self.cache_tokens = self.cache / "tokens"
        self.bundled_memory = self.package_root / "memory"
        self.bundled_violation_patterns = self.bundled_memory / "violations" / "patterns.json"
        self.agents_file = cwd / "AGENTS.md"

    def ensure(self) -> None:
        for path in self._directories():
            path.mkdir(parents=True, exist_ok=True)
        if not self.violation_patterns.exists() and self.bundled_violation_patterns.exists():
            self.violation_patterns.write_text(
                self.bundled_violation_patterns.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

    def _directories(self) -> tuple[Path, ...]:
        return (
            self.active_tasks,
            self.completed_tasks,
            self.scratchpads,
            self.runs,
            self.decisions,
            self.lessons,
            self.patterns,
            self.bugs,
            self.summaries,
            self.violations,
            self.cache_index,
            self.cache_tokens,
        )

    def run_directory(self, task_id: str) -> Path:
        path = self.runs / task_id
        path.mkdir(parents=True, exist_ok=True)
        return path
