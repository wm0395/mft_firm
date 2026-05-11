from __future__ import annotations

import time
from dataclasses import dataclass
from typing import cast

from .managed_runner import RunTaskOptions, run_task_command
from .memory_store import MemoryStore
from .paths import ProjectPaths
from .scratchpad import ScratchpadStore
from .tasks import TaskStore


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
        payload = _run_next_task(active[0].id, paths, tasks, scratchpads, memory, review_budget, options)
        run = cast(dict[str, object], payload["run"])
        history.append(_history_entry(run))
        if str(run["status"]) == "completed":
            completed += 1
            continue
        if _is_codex_limit(run):
            cooldowns += 1
            history.append(_cooldown_entry(run, options.cooldown_seconds))
            time.sleep(options.cooldown_seconds)
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


def _history_entry(run: dict[str, object]) -> dict[str, object]:
    return {
        "task_id": str(run["task_id"]),
        "provider": str(run["provider"]),
        "status": str(run["status"]),
        "exit_code": int(run["exit_code"]),
        "finished_at": str(run["finished_at"]),
    }


def _cooldown_entry(run: dict[str, object], cooldown_seconds: int) -> dict[str, object]:
    return {
        "task_id": str(run["task_id"]),
        "provider": str(run["provider"]),
        "status": "cooldown",
        "cooldown_seconds": cooldown_seconds,
    }


def _is_codex_limit(run: dict[str, object]) -> bool:
    if str(run["provider"]) != "codex" or str(run["status"]) != "provider_failed":
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
    run = cast(dict[str, object], payload["run"])
    return {
        "status": "stopped",
        "processed_tasks": completed,
        "cooldowns": cooldowns,
        "history": history,
        "last_payload": payload,
        "stop_reason": str(run["status"]),
    }
