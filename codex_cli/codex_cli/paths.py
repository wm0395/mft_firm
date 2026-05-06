from __future__ import annotations

from pathlib import Path


class ProjectPaths:
    def __init__(self, root: Path | None = None) -> None:
        cwd = Path.cwd()
        self.package_root = Path(__file__).resolve().parent
        self.root = root or cwd / "codex_cli"
        self.tasks = self.root / "tasks"
        self.active_tasks = self.tasks / "active"
        self.completed_tasks = self.tasks / "completed"
        self.memory = self.root / "memory"
        self.scratchpads = self.memory / "scratchpads"
        self.violations = self.memory / "violations"
        self.violation_patterns = self.violations / "patterns.json"
        self.bundled_violation_patterns = self.package_root / "memory" / "violations" / "patterns.json"
        self.agents_file = cwd / "AGENTS.md"

    def ensure(self) -> None:
        for path in (
            self.active_tasks,
            self.completed_tasks,
            self.scratchpads,
            self.violations,
            self.memory,
        ):
            path.mkdir(parents=True, exist_ok=True)

        if not self.violation_patterns.exists() and self.bundled_violation_patterns.exists():
            self.violation_patterns.write_text(
                self.bundled_violation_patterns.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
