from __future__ import annotations

from dataclasses import dataclass

from .launch_policy import default_review_target, is_rate_limit_text
from .cache import build_index, render_context_document, retrieve_context_entries
from .launcher import ONESHOT, build_launch_command, launch_task
from .managed_state import persist_review_state
from .memory_store import MemoryStore
from .models import Task, utc_now
from .paths import ProjectPaths
from .review_schema import REVIEW_FAILED, parse_review_output, review_status, reviewer_name
from .reviewer import review_task
from .scratchpad import ScratchpadStore
from .tasks import TaskStore
from .workflow import can_complete, next_required_reviewer


@dataclass(frozen=True)
class RunReviewOptions:
    provider: str | None
    budget: int
    model: str | None
    json_output: bool
    persona: str | None


def run_review_command(
    task_id: str,
    options: RunReviewOptions,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
) -> dict[str, object]:
    task = tasks.get(task_id)
    scratchpad = scratchpads.read(task.id)
    context = _build_context(task, paths, scratchpad)
    persona = options.persona or next_required_reviewer(task)
    target = _resolve_review_target(persona, options.provider, options.model)
    packet = review_task(task, paths, scratchpad, context, target.provider, persona, options.budget)
    command = build_launch_command(target.provider, ONESHOT, packet.prompt, paths.workspace_root, target.model, options.json_output)
    started_at = utc_now()
    launch = launch_task(target.provider, ONESHOT, packet.prompt, paths.workspace_root, target.model, options.json_output)
    finished_at = utc_now()
    record = _review_record(
        task,
        launch.exit_code,
        launch.stdout,
        launch.stderr,
        target.provider,
        target.model,
        options,
        command,
        started_at,
        finished_at,
        persona,
    )
    updated = persist_review_state(task, tasks, scratchpads, memory, record)
    return {
        "status": "completed" if can_complete(updated) else "active",
        "task": updated.to_dict(),
        "review": packet.to_dict(),
        "review_run": record,
    }


def _build_context(task: Task, paths: ProjectPaths, scratchpad: str) -> tuple[str, ...]:
    build_index(paths)
    entries = retrieve_context_entries(paths, task.objective, task.files)
    documents = [render_context_document(paths, entry) for entry in entries]
    documents.append("Scratchpad Context:\n" + scratchpad)
    return tuple(documents)


def _resolve_review_target(persona: str, provider: str | None, model: str | None):
    if provider is not None and provider not in {"codex", "opencode"}:
        raise ValueError(f"Unsupported review provider: {provider}")
    return default_review_target(persona, provider, model)


def _review_record(
    task: Task,
    exit_code: int,
    stdout: str,
    stderr: str,
    provider: str,
    model: str | None,
    options: RunReviewOptions,
    command: list[str],
    started_at: str,
    finished_at: str,
    persona: str,
) -> dict[str, object]:
    text = "\n".join(part for part in (stdout, stderr) if part.strip())
    reviewer = reviewer_name(persona)
    rate_limited = is_rate_limit_text(stdout, stderr)
    if exit_code != 0 or not text.strip():
        return _failed_record(
            task,
            exit_code,
            stdout,
            stderr,
            provider,
            model,
            options,
            command,
            started_at,
            finished_at,
            reviewer,
            "Review provider did not return valid output.",
            rate_limited,
        )
    try:
        parsed = parse_review_output(text, reviewer)
    except ValueError as error:
        return _failed_record(
            task,
            exit_code,
            stdout,
            stderr,
            provider,
            model,
            options,
            command,
            started_at,
            finished_at,
            reviewer,
            str(error),
            rate_limited,
        )
    return {
        "kind": "review_run",
        "task_id": task.id,
        "provider": provider,
        "command": command,
        "budget": options.budget,
        "model": model,
        "json_output": options.json_output,
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": exit_code,
        "rate_limited": rate_limited,
        "decision": parsed.decision,
        "review_status": review_status(parsed.decision),
        "reviewer": parsed.reviewer,
        "violations": [item.to_dict() for item in parsed.violations],
        "required_fixes": list(parsed.required_fixes),
        "evidence": [item.to_dict() for item in parsed.evidence],
        "summary": _summary(parsed),
        "stdout": stdout,
        "stderr": stderr,
    }


def _failed_record(
    task: Task,
    exit_code: int,
    stdout: str,
    stderr: str,
    provider: str,
    model: str | None,
    options: RunReviewOptions,
    command: list[str],
    started_at: str,
    finished_at: str,
    reviewer: str,
    reason: str,
    rate_limited: bool,
) -> dict[str, object]:
    return {
        "kind": "review_run",
        "task_id": task.id,
        "provider": provider,
        "command": command,
        "budget": options.budget,
        "model": model,
        "json_output": options.json_output,
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": exit_code,
        "rate_limited": rate_limited,
        "decision": REVIEW_FAILED,
        "review_status": REVIEW_FAILED,
        "reviewer": reviewer,
        "violations": [],
        "required_fixes": [],
        "evidence": [],
        "summary": reason,
        "stdout": stdout,
        "stderr": stderr,
    }


def _summary(review) -> str:
    if review.decision == "approve":
        return f"{review.reviewer} approved the implementation."
    if review.required_fixes:
        return review.required_fixes[0][:240]
    if review.violations:
        return review.violations[0].evidence[:240]
    return f"{review.reviewer} requested changes."
