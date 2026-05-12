from __future__ import annotations

import time
from dataclasses import dataclass
from typing import cast

from .managed_runner import RunTaskOptions, run_task_command
from .managed_state import build_completion_record
from .memory_store import MemoryStore
from .models import Task
from .paths import ProjectPaths
from .review_runner import RunReviewOptions, run_review_command
from .scratchpad import ScratchpadStore
from .tasks import TaskStore
from .workflow import can_complete


LIMIT_MARKERS = (
    "429",
    "rate limit",
    "usage limit",
    "limit reached",
    "try again in",
    "too many requests",
    "quota",
)


@dataclass(frozen=True)
class QueueRunOptions:
    provider: str | None
    budget: int
    json_output: bool
    model: str | None
    resume: bool
    review_enabled: bool
    checks_enabled: bool
    cooldown_seconds: int

    def with_resume(self, resume: bool) -> "QueueRunOptions":
        return QueueRunOptions(
            provider=self.provider,
            budget=self.budget,
            json_output=self.json_output,
            model=self.model,
            resume=resume,
            review_enabled=self.review_enabled,
            checks_enabled=self.checks_enabled,
            cooldown_seconds=self.cooldown_seconds,
        )


def run_task_queue(
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
    review_budget: int,
    options: QueueRunOptions,
) -> dict[str, object]:
    completed = 0
    cooldowns = 0
    history: list[dict[str, object]] = []
    while True:
        active = tasks.list_active()
        if not active:
            return _completed_payload(completed, cooldowns, history)
        task = active[0]
        payload = _advance_task(task, paths, tasks, scratchpads, memory, review_budget, options)
        entry = cast(dict[str, object], payload["entry"])
        outcome = str(payload["status"])
        history.append(entry)
        if entry["status"] == "cooldown":
            cooldowns += 1
            time.sleep(options.cooldown_seconds)
            continue
        if outcome == "completed":
            completed += 1
            continue
        if outcome == "active":
            continue
        return _stopped_payload(payload, completed, cooldowns, history)


def _run_next_task(
    task_id: str,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
    review_budget: int,
    options: QueueRunOptions,
) -> dict[str, object]:
    return run_task_command(
        task_id,
        RunTaskOptions(
            provider=options.provider,
            budget=options.budget,
            json_output=options.json_output,
            model=options.model,
            resume=options.resume,
            review_enabled=options.review_enabled,
            checks_enabled=options.checks_enabled,
            dry_run=False,
        ),
        paths,
        tasks,
        scratchpads,
        memory,
        review_budget,
    )


def _advance_task(
    task: Task,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
    review_budget: int,
    options: QueueRunOptions,
) -> dict[str, object]:
    if task.workflow_stage in {"tasked", "planned"}:
        return _implementation_step(task.id, False, paths, tasks, scratchpads, memory, review_budget, options)
    if task.workflow_stage == "fix_ready":
        return _implementation_step(task.id, True, paths, tasks, scratchpads, memory, review_budget, options)
    if task.workflow_stage == "implemented":
        return _review_step(task.id, paths, tasks, scratchpads, memory, review_budget, options)
    if can_complete(task):
        completed = build_completion_record(task)
        tasks.save(completed)
        return {"status": "completed", "entry": {"task_id": task.id, "status": "completed", "step": "complete"}}
    return {"status": "stopped", "entry": {"task_id": task.id, "status": "blocked", "step": task.workflow_stage}}


def _implementation_step(
    task_id: str,
    resume: bool,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
    review_budget: int,
    options: QueueRunOptions,
) -> dict[str, object]:
    payload = _run_next_task(task_id, paths, tasks, scratchpads, memory, review_budget, options.with_resume(resume))
    run = cast(dict[str, object], payload["run"])
    if _is_codex_limit(run):
        return {"status": "active", "entry": _cooldown_entry(run, options.cooldown_seconds), "last_payload": payload}
    entry_status = "active" if str(run["status"]) == "implemented" else "stopped"
    return {"status": entry_status, "entry": _history_entry(run), "last_payload": payload}


def _review_step(
    task_id: str,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
    review_budget: int,
    options: QueueRunOptions,
) -> dict[str, object]:
    payload = run_review_command(
        task_id,
        RunReviewOptions(
            provider=options.provider or "codex",
            budget=review_budget,
            model=options.model,
            json_output=options.json_output,
        ),
        paths,
        tasks,
        scratchpads,
        memory,
    )
    run = cast(dict[str, object], payload["review_run"])
    if _is_codex_limit(run):
        return {"status": "active", "entry": _cooldown_entry(run, options.cooldown_seconds), "last_payload": payload}
    task = tasks.get(task_id)
    if task.workflow_stage == "fix_ready":
        return {"status": "active", "entry": _review_history_entry(run), "last_payload": payload}
    if can_complete(task):
        completed = build_completion_record(task)
        tasks.save(completed)
        return {"status": "completed", "entry": {"task_id": task.id, "status": "completed", "step": "complete"}, "last_payload": payload}
    return {"status": "stopped", "entry": _review_history_entry(run), "last_payload": payload}


def _history_entry(run: dict[str, object]) -> dict[str, object]:
    return {
        "task_id": str(run["task_id"]),
        "provider": str(run["provider"]),
        "status": str(run["status"]),
        "exit_code": int(run["exit_code"]),
        "finished_at": str(run["finished_at"]),
        "step": "implement",
    }


def _cooldown_entry(run: dict[str, object], cooldown_seconds: int) -> dict[str, object]:
    return {
        "task_id": str(run["task_id"]),
        "provider": str(run["provider"]),
        "status": "cooldown",
        "cooldown_seconds": cooldown_seconds,
    }


def _review_history_entry(run: dict[str, object]) -> dict[str, object]:
    return {
        "task_id": str(run["task_id"]),
        "provider": str(run["provider"]),
        "status": str(run["decision"]),
        "exit_code": int(run["exit_code"]),
        "finished_at": str(run["finished_at"]),
        "step": "review",
    }


def _is_codex_limit(run: dict[str, object]) -> bool:
    if str(run["provider"]) != "codex":
        return False
    if int(run.get("exit_code", 0)) == 0 and str(run.get("status", "")) != "provider_failed":
        return False
    text = "\n".join(_run_text(run)).lower()
    return any(marker in text for marker in LIMIT_MARKERS)


def _run_text(run: dict[str, object]) -> tuple[str, ...]:
    summary = str(run.get("summary", ""))
    issues = [str(item) for item in cast(list[object], run.get("open_issues", []))]
    return (summary, *issues)


def _completed_payload(completed: int, cooldowns: int, history: list[dict[str, object]]) -> dict[str, object]:
    return {
        "status": "completed",
        "processed_tasks": completed,
        "cooldowns": cooldowns,
        "history": history,
        "last_payload": None,
        "stop_reason": None,
    }


def _stopped_payload(
    payload: dict[str, object],
    completed: int,
    cooldowns: int,
    history: list[dict[str, object]],
) -> dict[str, object]:
    last_payload = cast(dict[str, object], payload.get("last_payload") or {})
    run = cast(dict[str, object], last_payload.get("run") or last_payload.get("review_run") or {})
    return {
        "status": "stopped",
        "processed_tasks": completed,
        "cooldowns": cooldowns,
        "history": history,
        "last_payload": last_payload,
        "stop_reason": str(run.get("status") or run.get("decision") or "blocked"),
    }
