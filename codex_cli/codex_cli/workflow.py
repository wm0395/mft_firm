from __future__ import annotations

import hashlib
from pathlib import Path

from .models import Task


TRACKED_SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".txt"}
REVIEW_APPROVED = "approved"
REVIEW_CHANGES_REQUESTED = "changes_requested"


def snapshot_task_files(root: Path, declared_files: tuple[str, ...]) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for relative in declared_files:
        path = root / relative
        if path.is_file():
            _add_file(snapshot, root, path)
            continue
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    _add_file(snapshot, root, child)
    return snapshot


def changed_files(before: dict[str, str], after: dict[str, str]) -> tuple[str, ...]:
    changed = []
    keys = sorted(set(before) | set(after))
    for key in keys:
        if before.get(key) != after.get(key):
            changed.append(key)
    return tuple(changed)


def can_complete(task: Task) -> bool:
    return (
        task.workflow_stage == "reviewed"
        and task.implementation_status == "verified"
        and task.review_status == REVIEW_APPROVED
        and _required_reviewers_approved(task)
        and _latest_checks_passed(task)
        and _latest_diff_guard_passed(task)
    )


def review_decision(text: str) -> str:
    lowered = text.lower()
    if "review decision: approve" in lowered:
        return REVIEW_APPROVED
    return REVIEW_CHANGES_REQUESTED


def _add_file(snapshot: dict[str, str], root: Path, path: Path) -> None:
    if path.suffix and path.suffix not in TRACKED_SUFFIXES:
        return
    relative = str(path.relative_to(root))
    snapshot[relative] = _digest(path)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _required_reviewers_approved(task: Task) -> bool:
    required = set(task.required_reviewers or ("architecture_reviewer",))
    approved = {
        str(review.get("reviewer"))
        for review in task.review_history
        if str(review.get("review_status", review.get("decision", ""))) == REVIEW_APPROVED
    }
    return required.issubset(approved)


def _latest_diff_guard_passed(task: Task) -> bool:
    for run in reversed(task.run_history):
        if str(run.get("kind", "")) != "managed_run":
            continue
        diff_guard = run.get("diff_guard")
        if isinstance(diff_guard, dict):
            return bool(diff_guard.get("scope_ok"))
        return False
    return False


def _latest_checks_passed(task: Task) -> bool:
    for record in reversed(task.check_history):
        if str(record.get("kind", "")) != "checks":
            continue
        return str(record.get("status", "")) == "pass"
    return False
