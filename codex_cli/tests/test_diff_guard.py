from __future__ import annotations

import subprocess
from pathlib import Path

from codex_cli.diff_guard import dirty_scope_paths, evaluate_diff_guard, snapshot_worktree_status


def test_dirty_scope_paths_reports_preexisting_scope_changes(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    target = tmp_path / "project" / "signals" / "__init__.py"
    target.write_text("def signal():\n    return 2\n", encoding="utf-8")

    dirty = dirty_scope_paths(tmp_path, ("project/signals",))

    assert dirty == ("project/signals/__init__.py",)


def test_evaluate_diff_guard_passes_for_allowed_changes(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    before = snapshot_worktree_status(tmp_path)
    target = tmp_path / "project" / "signals" / "__init__.py"
    target.write_text("def signal():\n    return 2\n", encoding="utf-8")

    result = evaluate_diff_guard(tmp_path, before, ("project/signals",))

    assert result.status == "passed"
    assert result.scope_ok is True
    assert result.changed_files == ("project/signals/__init__.py",)


def test_evaluate_diff_guard_flags_out_of_scope_changes(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    before = snapshot_worktree_status(tmp_path)
    target = tmp_path / "project" / "decision" / "leak.py"
    target.parent.mkdir(parents=True)
    target.write_text("def leak():\n    return 1\n", encoding="utf-8")

    result = evaluate_diff_guard(tmp_path, before, ("project/signals",))

    assert result.status == "scope_violation"
    assert result.scope_ok is False
    assert result.undeclared_files == ("project/decision/leak.py",)


def _init_repo(root: Path) -> None:
    (root / ".gitignore").write_text("codex_cli/\n.pytest_cache/\n.mypy_cache/\n.ruff_cache/\n__pycache__/\n*.pyc\n", encoding="utf-8")
    (root / "project" / "signals").mkdir(parents=True)
    (root / "project" / "signals" / "__init__.py").write_text("def signal():\n    return 1\n", encoding="utf-8")
    _git(root, "init")
    _git(root, "config", "user.email", "tests@example.com")
    _git(root, "config", "user.name", "Tests")
    _git(root, "add", ".gitignore", "project/signals/__init__.py")
    _git(root, "commit", "-m", "initial")


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
