from __future__ import annotations

import time
from dataclasses import dataclass
from typing import cast

from .launch_policy import (
    DEFAULT_EXECUTION_PROVIDER,
    LaunchTarget,
    default_execution_target,
    default_review_target,
    is_rate_limit_text,
    next_launch_target,
)
from .managed_runner import RunTaskOptions, run_task_command
from .managed_state import build_completion_record
from .memory_store import MemoryStore
from .models import Task
from .paths import ProjectPaths
from .review_runner import RunReviewOptions, run_review_command
from .scratchpad import ScratchpadStore
from .tasks import TaskStore
from .workflow import can_complete, next_required_reviewer


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

    def with_target(self, provider: str | None, model: str | None) -> "QueueRunOptions":
        return QueueRunOptions(
            provider=provider,
            budget=self.budget,
            json_output=self.json_output,
            model=model,
            resume=self.resume,
            review_enabled=self.review_enabled,
            checks_enabled=self.checks_enabled,
            cooldown_seconds=self.cooldown_seconds,
        )

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
    switches = 0
    history: list[dict[str, object]] = []
    while True:
        active = tasks.list_active()
        if not active:
            return _completed_payload(completed, cooldowns, switches, history)
        task = active[0]
        payload = _advance_task(task, paths, tasks, scratchpads, memory, review_budget, options)
        entries = cast(tuple[dict[str, object], ...], payload.get("entries", ()))
        outcome = str(payload["status"])
        history.extend(entries)
        switches += sum(1 for entry in entries if str(entry["status"]) == "switch")
        if any(str(entry["status"]) == "cooldown" for entry in entries):
            cooldowns += 1
            time.sleep(options.cooldown_seconds)
            continue
        if outcome == "completed":
            completed += 1
            continue
        if outcome == "active":
            continue
        return _stopped_payload(payload, completed, cooldowns, switches, history)


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
        if not options.review_enabled:
            return {
                "status": "stopped",
                "entries": ({"task_id": task.id, "status": "blocked", "step": "review_disabled"},),
            }
        return _implementation_step(task.id, True, paths, tasks, scratchpads, memory, review_budget, options)
    if task.workflow_stage in {"implemented", "reviewed"}:
        if can_complete(task):
            completed = build_completion_record(task)
            tasks.save(completed)
            return {"status": "completed", "entries": (_completion_entry(completed),)}
        if not options.review_enabled:
            return {
                "status": "stopped",
                "entries": ({"task_id": task.id, "status": "blocked", "step": "review_disabled"},),
            }
        return _review_step(task.id, paths, tasks, scratchpads, memory, review_budget, options)
    if can_complete(task):
        completed = build_completion_record(task)
        tasks.save(completed)
        return {"status": "completed", "entries": (_completion_entry(completed),)}
    return {"status": "stopped", "entries": ({"task_id": task.id, "status": "blocked", "step": task.workflow_stage},)}


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
    target = _resolve_execution_target(tasks.get(task_id), options)
    seen = {target}
    entries: list[dict[str, object]] = []
    current = target
    while True:
        payload = _run_next_task(
            task_id,
            paths,
            tasks,
            scratchpads,
            memory,
            review_budget,
            options.with_target(current.provider, current.model).with_resume(resume),
        )
        run = cast(dict[str, object], payload["run"])
        if _is_rate_limited_record(run):
            next_target = next_launch_target(current)
            if next_target in seen:
                entries.append(_cooldown_entry(run, options.cooldown_seconds, current, "implement"))
                return {"status": "active", "entries": tuple(entries), "last_payload": payload}
            entries.append(_switch_entry(run, current, next_target, "implement"))
            seen.add(next_target)
            current = next_target
            continue
        entries.append(_history_entry(run))
        entry_status = "active" if str(run["status"]) == "implemented" else "stopped"
        return {"status": entry_status, "entries": tuple(entries), "last_payload": payload}


def _review_step(
    task_id: str,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
    review_budget: int,
    options: QueueRunOptions,
) -> dict[str, object]:
    task = tasks.get(task_id)
    persona = next_required_reviewer(task)
    target = _resolve_review_target(persona, options)
    seen = {target}
    entries: list[dict[str, object]] = []
    current = target
    while True:
        payload = run_review_command(
            task_id,
            RunReviewOptions(
                provider=current.provider,
                budget=review_budget,
                model=current.model,
                json_output=options.json_output,
                persona=persona,
            ),
            paths,
            tasks,
            scratchpads,
            memory,
        )
        run = cast(dict[str, object], payload["review_run"])
        if _is_rate_limited_record(run):
            next_target = next_launch_target(current)
            if next_target in seen:
                entries.append(_cooldown_entry(run, options.cooldown_seconds, current, "review"))
                return {"status": "active", "entries": tuple(entries), "last_payload": payload}
            entries.append(_switch_entry(run, current, next_target, "review"))
            seen.add(next_target)
            current = next_target
            continue
        entries.append(_review_history_entry(run))
        task = tasks.get(task_id)
        if can_complete(task):
            completed = build_completion_record(task)
            tasks.save(completed)
            entries.append(_completion_entry(completed))
            return {"status": "completed", "entries": tuple(entries), "last_payload": payload}
        return {"status": "active", "entries": tuple(entries), "last_payload": payload}


def _resolve_execution_target(task: Task, options: QueueRunOptions) -> LaunchTarget:
    provider = options.provider or DEFAULT_EXECUTION_PROVIDER
    if provider not in {"codex", "opencode"}:
        raise ValueError(f"Unsupported queue provider: {provider}")
    return default_execution_target(task.objective, task.route, provider, options.model)


def _resolve_review_target(persona: str, options: QueueRunOptions) -> LaunchTarget:
    provider = options.provider or DEFAULT_EXECUTION_PROVIDER
    if provider not in {"codex", "opencode"}:
        raise ValueError(f"Unsupported queue provider: {provider}")
    return default_review_target(persona, provider, options.model)


def _history_entry(run: dict[str, object]) -> dict[str, object]:
    return {
        "task_id": str(run["task_id"]),
        "provider": str(run["provider"]),
        "model": run.get("model"),
        "status": str(run["status"]),
        "exit_code": _int_value(run["exit_code"]),
        "finished_at": str(run["finished_at"]),
        "rate_limited": bool(run.get("rate_limited", False)),
        "step": "implement",
    }


def _switch_entry(
    run: dict[str, object],
    current: LaunchTarget,
    next_target: LaunchTarget,
    step: str,
) -> dict[str, object]:
    return {
        "task_id": str(run["task_id"]),
        "provider": str(run["provider"]),
        "model": run.get("model"),
        "status": "switch",
        "step": step,
        "from_provider": current.provider,
        "from_model": current.model,
        "to_provider": next_target.provider,
        "to_model": next_target.model,
        "exit_code": _int_value(run["exit_code"]),
        "finished_at": str(run["finished_at"]),
        "rate_limited": True,
    }


def _cooldown_entry(run: dict[str, object], cooldown_seconds: int, current: LaunchTarget, step: str) -> dict[str, object]:
    return {
        "task_id": str(run["task_id"]),
        "provider": current.provider,
        "model": current.model,
        "status": "cooldown",
        "step": step,
        "cooldown_seconds": cooldown_seconds,
        "rate_limited": True,
    }


def _review_history_entry(run: dict[str, object]) -> dict[str, object]:
    return {
        "task_id": str(run["task_id"]),
        "provider": str(run["provider"]),
        "model": run.get("model"),
        "status": str(run["decision"]),
        "exit_code": _int_value(run["exit_code"]),
        "finished_at": str(run["finished_at"]),
        "rate_limited": bool(run.get("rate_limited", False)),
        "reviewer": str(run.get("reviewer", "")),
        "step": "review",
    }


def _completion_entry(task: Task) -> dict[str, object]:
    return {"task_id": task.id, "status": "completed", "step": "complete"}


def _is_rate_limited_record(run: dict[str, object]) -> bool:
    if bool(run.get("rate_limited", False)):
        return True
    open_issues = [str(item) for item in cast(list[object], run.get("open_issues", []))]
    parts = (
        str(run.get("summary", "")),
        str(run.get("stdout", "")),
        str(run.get("stderr", "")),
        *open_issues,
    )
    return is_rate_limit_text(*parts)


def _int_value(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise ValueError(f"Invalid integer value: {value!r}")


def _run_text(run: dict[str, object]) -> tuple[str, ...]:
    summary = str(run.get("summary", ""))
    issues = [str(item) for item in cast(list[object], run.get("open_issues", []))]
    return (summary, *issues)


def _completed_payload(
    completed: int,
    cooldowns: int,
    switches: int,
    history: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "status": "completed",
        "processed_tasks": completed,
        "cooldowns": cooldowns,
        "switches": switches,
        "history": history,
        "last_payload": None,
        "stop_reason": None,
    }


def _stopped_payload(
    payload: dict[str, object],
    completed: int,
    cooldowns: int,
    switches: int,
    history: list[dict[str, object]],
) -> dict[str, object]:
    last_payload = cast(dict[str, object], payload.get("last_payload") or {})
    run = cast(dict[str, object], last_payload.get("run") or last_payload.get("review_run") or {})
    return {
        "status": "stopped",
        "processed_tasks": completed,
        "cooldowns": cooldowns,
        "switches": switches,
        "history": history,
        "last_payload": last_payload,
        "stop_reason": str(run.get("status") or run.get("decision") or "blocked"),
    }
