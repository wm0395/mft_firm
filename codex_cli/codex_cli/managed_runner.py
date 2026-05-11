from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import cast

from .cache import build_index, render_context_document, retrieve_context_entries
from .checks import run_required_checks
from .executor import execute_task
from .launcher import ONESHOT, LAUNCH_PROVIDERS, build_launch_command, launch_task
from .managed_state import persist_managed_state
from .memory_store import MemoryStore
from .models import ExecutionPacket, Task, utc_now
from .paths import ProjectPaths
from .reviewer import review_task
from .scratchpad import ScratchpadStore
from .tasks import TaskStore


REVIEW_PROVIDER = "gemini"
REVIEW_PERSONA = "architecture"
FILE_PATTERN = re.compile(r"\b[A-Za-z0-9_./-]+\.(?:py|md|toml|yml|yaml|json|txt)\b")


@dataclass(frozen=True)
class RunTaskOptions:
    provider: str | None
    budget: int
    json_output: bool
    model: str | None
    resume: bool
    review_enabled: bool
    checks_enabled: bool
    dry_run: bool


def run_task_command(
    task_id: str,
    options: RunTaskOptions,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
    review_budget: int,
) -> dict[str, object]:
    task = tasks.get(task_id)
    provider = _resolve_provider(task, options.provider)
    scratchpad = _load_scratchpad(task, scratchpads)
    context = _build_context(task, paths, memory, scratchpad, options.resume)
    packet = execute_task(task, paths, scratchpad, context, provider, options.budget)
    command = build_launch_command(
        provider,
        ONESHOT,
        packet.prompt,
        paths.workspace_root,
        options.model,
        options.json_output,
    )
    if options.dry_run:
        return _dry_run_payload(task, provider, options, packet, context, command)
    return _run_managed_task(task, provider, options, paths, tasks, scratchpads, memory, packet, context, command, review_budget)


def _resolve_provider(task: Task, explicit_provider: str | None) -> str:
    provider = explicit_provider or task.recommended_provider
    if provider not in LAUNCH_PROVIDERS:
        raise ValueError(f"Unsupported managed provider: {provider}")
    return provider


def _load_scratchpad(task: Task, scratchpads: ScratchpadStore) -> str:
    try:
        return scratchpads.read(task.id)
    except FileNotFoundError:
        return scratchpads.create(task)


def _build_context(
    task: Task,
    paths: ProjectPaths,
    memory: MemoryStore,
    scratchpad: str,
    resume: bool,
) -> tuple[str, ...]:
    build_index(paths)
    entries = retrieve_context_entries(paths, task.objective, task.files)
    documents = [render_context_document(paths, entry) for entry in entries]
    documents.append("Scratchpad Context:\n" + scratchpad)
    documents.extend(_memory_documents(memory, task.memory_refs))
    if resume and task.run_history:
        documents.append("Recent Run Summary:\n" + str(task.run_history[-1].get("summary", "")))
    return tuple(documents)


def _memory_documents(memory: MemoryStore, refs: tuple[str, ...]) -> list[str]:
    documents: list[str] = []
    for ref in refs:
        try:
            entry = memory.read_entry(ref)
        except FileNotFoundError:
            continue
        lines = [f"Memory Ref: {ref}", f"Title: {entry.title}", f"Body: {entry.body}"]
        if entry.tags:
            lines.append("Tags: " + ", ".join(entry.tags))
        documents.append("\n".join(lines))
    return documents


def _dry_run_payload(
    task: Task,
    provider: str,
    options: RunTaskOptions,
    packet: ExecutionPacket,
    context: tuple[str, ...],
    command: list[str],
) -> dict[str, object]:
    return {
        "status": "ready",
        "task_id": task.id,
        "managed_steps": _planned_steps(options),
        "launch": {
            "provider": provider,
            "mode": ONESHOT,
            "budget": options.budget,
            "json_output": options.json_output,
            "model": options.model,
            "command": command,
            "token_estimate": packet.token_estimate,
            "context_items": len(context),
        },
    }


def _planned_steps(options: RunTaskOptions) -> list[str]:
    steps = [
        "prepare task context",
        "launch provider in oneshot mode",
        "persist run artifacts",
        "update scratchpad and durable memory",
    ]
    if options.review_enabled:
        steps.append("generate review packet")
    if options.checks_enabled:
        steps.append("run required checks")
        steps.append("complete task only if provider and checks pass")
    else:
        steps.append("leave task active without checks")
    return steps


def _run_managed_task(
    task: Task,
    provider: str,
    options: RunTaskOptions,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
    packet: ExecutionPacket,
    context: tuple[str, ...],
    command: list[str],
    review_budget: int,
) -> dict[str, object]:
    started_at = utc_now()
    launch = launch_task(
        provider,
        ONESHOT,
        packet.prompt,
        paths.workspace_root,
        options.model,
        options.json_output,
    )
    finished_at = utc_now()
    artifact_refs = _persist_run_artifacts(paths, task.id, launch.stdout, launch.stderr, options.json_output)
    events = _parse_json_events(launch.stdout) if options.json_output else ()
    review_record = None
    check_record = None
    if launch.exit_code == 0:
        review_record = _maybe_create_review(task, paths, review_budget, options.review_enabled, scratchpads, context, launch.stdout)
        check_record = _maybe_run_checks(paths, options.checks_enabled)
    run_record = _build_run_record(task, provider, options, command, launch, artifact_refs, events, check_record, review_record, started_at, finished_at)
    updated = persist_managed_state(task, tasks, scratchpads, memory, packet, run_record, review_record, check_record)
    return _result_payload(updated, packet, run_record, review_record, check_record)


def _persist_run_artifacts(
    paths: ProjectPaths,
    task_id: str,
    stdout: str,
    stderr: str,
    json_output: bool,
) -> dict[str, str]:
    run_dir = paths.run_directory(task_id)
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    refs = {"stdout": str(stdout_path.relative_to(paths.root)), "stderr": str(stderr_path.relative_to(paths.root))}
    events = _parse_json_events(stdout) if json_output else ()
    if events:
        events_path = run_dir / "events.jsonl"
        events_path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
        refs["events"] = str(events_path.relative_to(paths.root))
    return refs


def _parse_json_events(stdout: str) -> tuple[dict[str, object], ...]:
    events = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return tuple(events)


def _maybe_create_review(
    task: Task,
    paths: ProjectPaths,
    review_budget: int,
    enabled: bool,
    scratchpads: ScratchpadStore,
    context: tuple[str, ...],
    provider_output: str,
) -> dict[str, object] | None:
    if not enabled:
        return None
    scratchpad = scratchpads.render(task)
    review_context = (*context, "Provider Output Summary:\n" + _extract_summary(provider_output, "", ()))
    packet = review_task(task, paths, scratchpad, review_context, REVIEW_PROVIDER, REVIEW_PERSONA, review_budget)
    record = packet.to_dict()
    record["kind"] = "review"
    record["status"] = "generated"
    return record


def _maybe_run_checks(paths: ProjectPaths, enabled: bool) -> dict[str, object] | None:
    if not enabled:
        return None
    result = run_required_checks(paths.workspace_root)
    return {"kind": "checks", **result}


def _build_run_record(
    task: Task,
    provider: str,
    options: RunTaskOptions,
    command: list[str],
    launch,
    artifact_refs: dict[str, str],
    events: tuple[dict[str, object], ...],
    check_record: dict[str, object] | None,
    review_record: dict[str, object] | None,
    started_at: str,
    finished_at: str,
) -> dict[str, object]:
    status = _run_status(launch.exit_code, check_record, options.checks_enabled)
    summary = _extract_summary(launch.stdout, launch.stderr, events)
    files_changed = _extract_files(launch.stdout + "\n" + launch.stderr, task.files)
    return {
        "kind": "managed_run",
        "task_id": task.id,
        "provider": provider,
        "mode": ONESHOT,
        "command": command,
        "budget": options.budget,
        "model": options.model,
        "json_output": options.json_output,
        "resume": options.resume,
        "review_enabled": options.review_enabled,
        "checks_enabled": options.checks_enabled,
        "exit_code": launch.exit_code,
        "started_at": started_at,
        "finished_at": finished_at,
        "status": status,
        "summary": summary,
        "understanding": f"Objective: {task.objective}",
        "plan": "Execute the prepared packet, persist results, and validate required checks.",
        "actions_taken": _actions_taken(launch.exit_code, review_record, check_record),
        "files_changed": files_changed,
        "checks_run": _check_names(check_record),
        "open_issues": _open_issues(status, launch.stderr, check_record),
        "final_decision": _final_decision(status),
        "context_refs": list(artifact_refs.values()),
        "artifacts": artifact_refs,
    }


def _run_status(exit_code: int, check_record: dict[str, object] | None, checks_enabled: bool) -> str:
    if exit_code != 0:
        return "provider_failed"
    if not checks_enabled:
        return "awaiting_checks"
    return "completed" if check_record and check_record.get("status") == "pass" else "checks_failed"


def _extract_summary(stdout: str, stderr: str, events: tuple[dict[str, object], ...]) -> str:
    for event in reversed(events):
        for key in ("summary", "message", "content", "text"):
            value = event.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for source in (stdout, stderr):
        lines = [line.strip() for line in source.splitlines() if line.strip()]
        if lines:
            return " ".join(lines[-3:])[:240]
    return "Provider completed without a textual summary."


def _extract_files(text: str, declared_files: tuple[str, ...]) -> list[str]:
    matches = list(dict.fromkeys(FILE_PATTERN.findall(text)))
    if matches:
        return matches[:8]
    return list(declared_files[:8])


def _actions_taken(
    exit_code: int,
    review_record: dict[str, object] | None,
    check_record: dict[str, object] | None,
) -> list[str]:
    actions = [f"Provider exited with code {exit_code}."]
    if review_record:
        actions.append("Generated review packet.")
    if check_record:
        actions.append("Ran required checks.")
    return actions


def _check_names(check_record: dict[str, object] | None) -> list[str]:
    if not check_record:
        return []
    checks = cast(list[dict[str, object]], check_record.get("checks", []))
    return [str(item["name"]) for item in checks]


def _open_issues(status: str, stderr: str, check_record: dict[str, object] | None) -> list[str]:
    if status == "completed":
        return []
    issues = []
    if stderr.strip():
        issues.append(stderr.strip().splitlines()[-1])
    if check_record and check_record.get("status") != "pass":
        issues.append("Required checks failed.")
    return issues or ["Task remains active until required checks pass."]


def _final_decision(status: str) -> str:
    if status == "completed":
        return "Task completed after provider success and green checks."
    if status == "awaiting_checks":
        return "Task remains active because checks were skipped."
    if status == "checks_failed":
        return "Task remains active until failing checks are resolved."
    return "Task remains active because provider execution failed."


def _result_payload(
    task: Task,
    packet: ExecutionPacket,
    run_record: dict[str, object],
    review_record: dict[str, object] | None,
    check_record: dict[str, object] | None,
) -> dict[str, object]:
    status = "completed" if task.status == "completed" else "active"
    return {
        "status": status,
        "task": task.to_dict(),
        "execution": packet.to_dict(),
        "run": run_record,
        "review": review_record,
        "checks": check_record,
    }
