from __future__ import annotations

from dataclasses import dataclass

from .cache import build_index, render_context_document, retrieve_context_entries
from .launcher import ONESHOT, build_launch_command, launch_task
from .managed_state import persist_review_state
from .memory_store import MemoryStore
from .models import Task, utc_now
from .paths import ProjectPaths
from .reviewer import review_task
from .scratchpad import ScratchpadStore
from .tasks import TaskStore
from .workflow import can_complete, review_decision


@dataclass(frozen=True)
class RunReviewOptions:
    provider: str
    budget: int
    model: str | None
    json_output: bool


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
    packet = review_task(task, paths, scratchpad, context, options.provider, "architecture", options.budget)
    command = build_launch_command(options.provider, ONESHOT, packet.prompt, paths.workspace_root, options.model, options.json_output)
    started_at = utc_now()
    launch = launch_task(options.provider, ONESHOT, packet.prompt, paths.workspace_root, options.model, options.json_output)
    finished_at = utc_now()
    record = _review_record(task, launch.exit_code, launch.stdout, launch.stderr, options, command, started_at, finished_at)
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


def _review_record(
    task: Task,
    exit_code: int,
    stdout: str,
    stderr: str,
    options: RunReviewOptions,
    command: list[str],
    started_at: str,
    finished_at: str,
) -> dict[str, object]:
    text = "\n".join(part for part in (stdout, stderr) if part.strip())
    decision = "review_failed" if exit_code != 0 or not text.strip() else review_decision(text)
    summary = _summary(text)
    return {
        "kind": "review_run",
        "task_id": task.id,
        "provider": options.provider,
        "command": command,
        "budget": options.budget,
        "model": options.model,
        "json_output": options.json_output,
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": exit_code,
        "decision": decision,
        "summary": summary,
        "stdout": stdout,
        "stderr": stderr,
    }


def _summary(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Review provider did not return output."
    return " ".join(lines[:3])[:240]
