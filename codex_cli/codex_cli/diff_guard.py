from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


IGNORED_PREFIXES = (
    "codex_cli/memory/",
    "codex_cli/runtime/",
    "codex_cli/tasks/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
)
IGNORED_SUFFIXES = (".pyc",)
IGNORED_NAMES = (".coverage",)


@dataclass(frozen=True)
class DiffGuardResult:
    status: str
    changed_files: tuple[str, ...]
    undeclared_files: tuple[str, ...]
    scope_ok: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "changed_files": list(self.changed_files),
            "undeclared_files": list(self.undeclared_files),
            "scope_ok": self.scope_ok,
        }


class DiffGuardUnavailableError(RuntimeError):
    pass


def dirty_scope_paths(root: Path, scope_paths: tuple[str, ...]) -> tuple[str, ...]:
    if not scope_paths:
        return ()
    return tuple(sorted(_status_map(root, scope_paths)))


def snapshot_worktree_status(root: Path) -> dict[str, str]:
    return _status_map(root)


def evaluate_diff_guard(
    root: Path,
    before: dict[str, str],
    allowed_change_set: tuple[str, ...],
) -> DiffGuardResult:
    after = _status_map(root)
    changed = tuple(
        sorted(
            path
            for path, status in after.items()
            if before.get(path) != status
        )
    )
    undeclared = tuple(path for path in changed if not _is_allowed_path(path, allowed_change_set))
    if undeclared:
        return DiffGuardResult(
            status="scope_violation",
            changed_files=changed,
            undeclared_files=undeclared,
            scope_ok=False,
        )
    return DiffGuardResult(
        status="passed",
        changed_files=changed,
        undeclared_files=(),
        scope_ok=True,
    )


def _status_map(root: Path, pathspecs: tuple[str, ...] = ()) -> dict[str, str]:
    _ensure_git_repo(root)
    command = ["git", "status", "--porcelain=v1", "--untracked-files=all", "--"]
    command.extend(pathspecs)
    result = subprocess.run(
        command,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise DiffGuardUnavailableError(result.stderr.strip() or "git status failed")
    entries: dict[str, str] = {}
    for raw_line in result.stdout.splitlines():
        line = raw_line.rstrip()
        if len(line) < 4:
            continue
        path = _normalize_status_path(line[3:].strip())
        if not path or _is_ignored_path(path):
            continue
        entries[path] = line[:2]
    return entries


def _ensure_git_repo(root: Path) -> None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise DiffGuardUnavailableError("git repository required for managed diff guard")


def _normalize_status_path(path: str) -> str:
    if " -> " in path:
        return path.split(" -> ", 1)[1].strip()
    return path


def _is_allowed_path(path: str, allowed_change_set: tuple[str, ...]) -> bool:
    for allowed in allowed_change_set:
        normalized = allowed.rstrip("/")
        if path == normalized or path.startswith(normalized + "/"):
            return True
    return False


def _is_ignored_path(path: str) -> bool:
    if path in IGNORED_NAMES:
        return True
    if any(path.startswith(prefix) for prefix in IGNORED_PREFIXES):
        return True
    return path.endswith(IGNORED_SUFFIXES)
