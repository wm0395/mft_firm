from __future__ import annotations

import json
from dataclasses import dataclass
from typing import cast

from .cache import build_index, render_context_document, retrieve_context_entries
from .checks import run_required_checks
from .diff_guard import (
    DiffGuardUnavailableError,
    dirty_scope_paths,
    evaluate_diff_guard,
    snapshot_worktree_status,
)
from .launch_policy import DEFAULT_EXECUTION_PROVIDER, default_execution_target, is_rate_limit_text
from .executor import execute_task
from .launcher import ONESHOT, LAUNCH_PROVIDERS, build_launch_command, launch_task
from .managed_state import persist_managed_state
from .memory_store import MemoryStore
from .models import ExecutionPacket, Task, utc_now
from .paths import ProjectPaths
from .reviewer import review_task
from .scratchpad import ScratchpadStore
from .tasks import TaskStore
from .workflow import changed_files, next_required_reviewer, snapshot_task_files


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

    def with_target(self, provider: str | None, model: str | None) -> "RunTaskOptions":
        return RunTaskOptions(
            provider=provider,
            budget=self.budget,
            json_output=self.json_output,
            model=model,
            resume=self.resume,
            review_enabled=self.review_enabled,
            checks_enabled=self.checks_enabled,
            dry_run=self.dry_run,
        )


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
    target = _resolve_execution_target(task, options.provider, options.model)
    scratchpad = _load_scratchpad(task, scratchpads)
    context = _build_context(task, paths, memory, scratchpad, options.resume)
    packet = execute_task(task, paths, scratchpad, context, target.provider, options.budget)
    command = build_launch_command(
        target.provider,
        ONESHOT,
        packet.prompt,
        paths.workspace_root,
        target.model,
        options.json_output,
    )
    if options.dry_run:
        return _dry_run_payload(task, target, options, packet, context, command)
    scope_paths = _task_scope(task)
    if not options.resume:
        dirty_paths = _dirty_scope_paths(paths, scope_paths)
        if dirty_paths is None:
            return _diff_guard_unavailable_payload(task, packet, target, options, command)
        if dirty_paths:
            return _preflight_blocked_payload(task, packet, target, options, command, dirty_paths)
    return _run_managed_task(task, target, options, paths, tasks, scratchpads, memory, packet, context, command, review_budget)


def _resolve_execution_target(task: Task, explicit_provider: str | None, model: str | None):
    provider = explicit_provider or DEFAULT_EXECUTION_PROVIDER
    if provider not in LAUNCH_PROVIDERS:
        raise ValueError(f"Unsupported managed provider: {provider}")
    return default_execution_target(task.objective, task.route, provider, model)


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
    target,
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
            "provider": target.provider,
            "mode": ONESHOT,
            "budget": options.budget,
            "json_output": options.json_output,
            "model": target.model,
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
    target,
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
    scope_paths = _task_scope(task)
    before_snapshot = snapshot_task_files(paths.workspace_root, scope_paths)
    diff_before = _snapshot_worktree_status(paths)
    launch = launch_task(
        target.provider,
        ONESHOT,
        packet.prompt,
        paths.workspace_root,
        target.model,
        options.json_output,
    )
    finished_at = utc_now()
    after_snapshot = snapshot_task_files(paths.workspace_root, scope_paths)
    artifact_refs = _persist_run_artifacts(paths, task.id, launch.stdout, launch.stderr, options.json_output)
    events = _parse_json_events(launch.stdout) if options.json_output else ()
    implementation_files = changed_files(before_snapshot, after_snapshot)
    diff_guard = _diff_guard(paths, diff_before, scope_paths)
    review_record = None
    check_record = None
    if launch.exit_code == 0 and implementation_files and _diff_guard_passed(diff_guard):
        check_record = _maybe_run_checks(paths, options.checks_enabled)
    run_record = _build_run_record(
        task,
        target.provider,
        target.model,
        options,
        command,
        launch,
        artifact_refs,
        events,
        check_record,
        review_record,
        implementation_files,
        diff_guard,
        started_at,
        finished_at,
    )
    if run_record["status"] == "implemented":
        review_record = _maybe_create_review(
            task,
            paths,
            review_budget,
            options.review_enabled,
            scratchpads,
            context,
            launch.stdout,
        )
        if review_record is not None:
            actions_taken = cast(list[str], run_record["actions_taken"])
            actions_taken.append("Generated review packet.")
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
    packet = review_task(
        task,
        paths,
        scratchpad,
        review_context,
        DEFAULT_EXECUTION_PROVIDER,
        next_required_reviewer(task),
        review_budget,
    )
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
    model: str | None,
    options: RunTaskOptions,
    command: list[str],
    launch,
    artifact_refs: dict[str, str],
    events: tuple[dict[str, object], ...],
    check_record: dict[str, object] | None,
    review_record: dict[str, object] | None,
    implementation_files: tuple[str, ...],
    diff_guard: dict[str, object] | None,
    started_at: str,
    finished_at: str,
) -> dict[str, object]:
    status = _run_status(launch.exit_code, check_record, options.checks_enabled, implementation_files, diff_guard)
    summary = _extract_summary(launch.stdout, launch.stderr, events)
    files_changed = _files_changed(implementation_files, diff_guard)
    open_issues = _open_issues(status, launch.stderr, check_record, diff_guard)
    return {
        "kind": "managed_run",
        "task_id": task.id,
        "provider": provider,
        "mode": ONESHOT,
        "command": command,
        "budget": options.budget,
        "model": model,
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
        "actions_taken": _actions_taken(launch.exit_code, check_record, diff_guard),
        "files_changed": list(files_changed),
        "implementation_status": "verified" if status == "implemented" else "missing",
        "checks_run": _check_names(check_record),
        "open_issues": open_issues,
        "final_decision": _final_decision(status),
        "context_refs": list(artifact_refs.values()),
        "artifacts": artifact_refs,
        "diff_guard": diff_guard,
        "rate_limited": is_rate_limit_text(summary, launch.stdout, launch.stderr, "\n".join(open_issues)),
    }


def _run_status(
    exit_code: int,
    check_record: dict[str, object] | None,
    checks_enabled: bool,
    implementation_files: tuple[str, ...],
    diff_guard: dict[str, object] | None,
) -> str:
    if exit_code != 0:
        return "provider_failed"
    if diff_guard and str(diff_guard.get("status")) != "passed":
        return str(diff_guard.get("status"))
    if not implementation_files:
        return "no_changes"
    if not checks_enabled:
        return "implemented"
    return "implemented" if check_record and check_record.get("status") == "pass" else "checks_failed"


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


def _actions_taken(
    exit_code: int,
    check_record: dict[str, object] | None,
    diff_guard: dict[str, object] | None,
) -> list[str]:
    actions = [f"Provider exited with code {exit_code}."]
    if diff_guard:
        if str(diff_guard.get("status")) == "passed":
            actions.append("Validated git diff scope.")
        else:
            actions.append("Blocked task advancement because git diff scope validation failed.")
    if check_record:
        actions.append("Ran required checks.")
    return actions


def _check_names(check_record: dict[str, object] | None) -> list[str]:
    if not check_record:
        return []
    checks = cast(list[dict[str, object]], check_record.get("checks", []))
    return [str(item["name"]) for item in checks]


def _open_issues(
    status: str,
    stderr: str,
    check_record: dict[str, object] | None,
    diff_guard: dict[str, object] | None,
) -> list[str]:
    if status == "implemented":
        return []
    issues = []
    if status == "no_changes":
        issues.append("No implementation changes were detected in the declared task scope.")
    if status == "preflight_blocked":
        issues.append("Task-scope files already had uncommitted changes before provider launch.")
    if status == "scope_violation" and diff_guard:
        undeclared = cast(list[object], diff_guard.get("undeclared_files", []))
        issues.append("Git diff guard found out-of-scope file changes.")
        issues.extend(f"Out-of-scope change: {item}" for item in undeclared)
    if status == "diff_unavailable":
        issues.append("Git diff guard could not inspect repository state.")
    if stderr.strip():
        issues.append(stderr.strip().splitlines()[-1])
    if check_record and check_record.get("status") != "pass":
        issues.append("Required checks failed.")
    return issues or ["Task remains active until required checks pass."]


def _final_decision(status: str) -> str:
    if status == "implemented":
        return "Implementation completed with verified file changes."
    if status == "checks_failed":
        return "Task remains active until failing checks are resolved."
    if status == "no_changes":
        return "Task remains active because no implementation changes were detected."
    if status == "preflight_blocked":
        return "Task did not launch because task-scope files were already dirty."
    if status == "scope_violation":
        return "Task remains active because git diff guard found out-of-scope changes."
    if status == "diff_unavailable":
        return "Task remains active because git diff guard could not inspect repository state."
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


def _task_scope(task: Task) -> tuple[str, ...]:
    return task.allowed_change_set or task.files


def _dirty_scope_paths(paths: ProjectPaths, scope_paths: tuple[str, ...]) -> tuple[str, ...] | None:
    try:
        return dirty_scope_paths(paths.workspace_root, scope_paths)
    except DiffGuardUnavailableError:
        return None


def _snapshot_worktree_status(paths: ProjectPaths) -> dict[str, str] | None:
    try:
        return snapshot_worktree_status(paths.workspace_root)
    except DiffGuardUnavailableError:
        return None


def _diff_guard(
    paths: ProjectPaths,
    before: dict[str, str] | None,
    scope_paths: tuple[str, ...],
) -> dict[str, object] | None:
    if before is None:
        return {"status": "diff_unavailable", "changed_files": [], "undeclared_files": [], "scope_ok": False}
    try:
        result = evaluate_diff_guard(paths.workspace_root, before, scope_paths)
    except DiffGuardUnavailableError:
        return {"status": "diff_unavailable", "changed_files": [], "undeclared_files": [], "scope_ok": False}
    return result.to_dict()


def _diff_guard_passed(diff_guard: dict[str, object] | None) -> bool:
    if diff_guard is None:
        return False
    return str(diff_guard.get("status")) == "passed"


def _files_changed(
    implementation_files: tuple[str, ...],
    diff_guard: dict[str, object] | None,
) -> tuple[str, ...]:
    if diff_guard:
        changed = cast(list[object], diff_guard.get("changed_files", []))
        if changed:
            return tuple(str(item) for item in changed)
    return implementation_files


def _preflight_blocked_payload(
    task: Task,
    packet: ExecutionPacket,
    target,
    options: RunTaskOptions,
    command: list[str],
    dirty_paths: tuple[str, ...],
) -> dict[str, object]:
    timestamp = utc_now()
    run_record = {
        "kind": "managed_run",
        "task_id": task.id,
        "provider": target.provider,
        "mode": ONESHOT,
        "command": command,
        "budget": options.budget,
        "model": target.model,
        "json_output": options.json_output,
        "resume": options.resume,
        "review_enabled": options.review_enabled,
        "checks_enabled": options.checks_enabled,
        "exit_code": 0,
        "started_at": timestamp,
        "finished_at": timestamp,
        "status": "preflight_blocked",
        "summary": "Managed run blocked because task-scope files already had uncommitted changes.",
        "understanding": f"Objective: {task.objective}",
        "plan": "Execute the prepared packet, persist results, and validate required checks.",
        "actions_taken": ["Blocked before provider launch due to pre-existing task-scope changes."],
        "files_changed": list(dirty_paths),
        "implementation_status": "missing",
        "checks_run": [],
        "open_issues": [f"Dirty task-scope file: {path}" for path in dirty_paths],
        "final_decision": "Task did not launch because task-scope files were already dirty.",
        "context_refs": [],
        "artifacts": {},
        "diff_guard": None,
        "rate_limited": False,
    }
    return {
        "status": "active",
        "task": task.to_dict(),
        "execution": packet.to_dict(),
        "run": run_record,
        "review": None,
        "checks": None,
    }


def _diff_guard_unavailable_payload(
    task: Task,
    packet: ExecutionPacket,
    target,
    options: RunTaskOptions,
    command: list[str],
) -> dict[str, object]:
    timestamp = utc_now()
    run_record = {
        "kind": "managed_run",
        "task_id": task.id,
        "provider": target.provider,
        "mode": ONESHOT,
        "command": command,
        "budget": options.budget,
        "model": target.model,
        "json_output": options.json_output,
        "resume": options.resume,
        "review_enabled": options.review_enabled,
        "checks_enabled": options.checks_enabled,
        "exit_code": 0,
        "started_at": timestamp,
        "finished_at": timestamp,
        "status": "diff_unavailable",
        "summary": "Managed run blocked because git diff guard could not inspect repository state.",
        "understanding": f"Objective: {task.objective}",
        "plan": "Execute the prepared packet, persist results, and validate required checks.",
        "actions_taken": ["Blocked before provider launch because git diff guard was unavailable."],
        "files_changed": [],
        "implementation_status": "missing",
        "checks_run": [],
        "open_issues": ["Git repository state could not be inspected before provider launch."],
        "final_decision": "Task did not launch because git diff guard could not inspect repository state.",
        "context_refs": [],
        "artifacts": {},
        "diff_guard": {"status": "diff_unavailable", "changed_files": [], "undeclared_files": [], "scope_ok": False},
        "rate_limited": False,
    }
    return {
        "status": "active",
        "task": task.to_dict(),
        "execution": packet.to_dict(),
        "run": run_record,
        "review": None,
        "checks": None,
    }
