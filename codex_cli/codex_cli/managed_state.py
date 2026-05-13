from __future__ import annotations

import json
from typing import cast

from .memory_store import MemoryStore
from .models import ExecutionPacket, Task
from .paths import ProjectPaths
from .scratchpad import ScratchpadStore
from .tasks import TaskStore
from .workflow import REVIEW_APPROVED, REVIEW_CHANGES_REQUESTED


def persist_managed_state(
    task: Task,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
    packet: ExecutionPacket,
    run_record: dict[str, object],
    review_record: dict[str, object] | None,
    check_record: dict[str, object] | None,
) -> Task:
    updated = task.with_packet({"kind": "packet", "source": "run-task", **packet.to_dict()}).with_run(run_record)
    if review_record:
        updated = updated.with_review(review_record).with_review_status("generated")
    if check_record:
        updated = updated.with_checks(check_record)
    updated = _persist_memory(updated, memory, run_record)
    updated = _apply_implementation_transition(updated, run_record)
    tasks.save(updated)
    scratchpads.refresh(updated)
    write_latest_run(tasks.paths, updated.id, run_record, review_record, check_record)
    return updated


def persist_review_state(
    task: Task,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
    review_record: dict[str, object],
) -> Task:
    review_status = str(review_record.get("review_status", review_record["decision"]))
    updated = task.with_review(review_record).with_review_status(review_status)
    updated = _persist_memory(updated, memory, review_record)
    updated = _apply_review_transition(updated, review_record)
    tasks.save(updated)
    scratchpads.refresh(updated)
    write_latest_run(tasks.paths, updated.id, review_record, review_record, None)
    return updated


def write_latest_run(
    paths: ProjectPaths,
    task_id: str,
    run_record: dict[str, object],
    review_record: dict[str, object] | None,
    check_record: dict[str, object] | None,
) -> None:
    latest = {"task_id": task_id, "run": run_record, "review": review_record, "checks": check_record}
    target = paths.run_directory(task_id) / "latest.json"
    target.write_text(json.dumps(latest, indent=2) + "\n", encoding="utf-8")


def _persist_memory(task: Task, memory: MemoryStore, run_record: dict[str, object]) -> Task:
    updated = task.with_memory_ref(
        memory.create_entry("summaries", task, task.objective, str(run_record["summary"]), ("task", "summary")).ref
    )
    for kind, entries in _durable_entries(task, run_record).items():
        for title, body in entries:
            updated = updated.with_memory_ref(memory.create_entry(kind, task, title, body, (kind,)).ref)
    return updated


def _durable_entries(task: Task, run_record: dict[str, object]) -> dict[str, list[tuple[str, str]]]:
    markers = {
        "decisions": ("decision:", "architectural decision:"),
        "patterns": ("pattern:", "reusable pattern:"),
        "bugs": ("bug:", "repeated bug:"),
        "lessons": ("lesson:",),
    }
    issues = [str(item) for item in cast(list[object], run_record.get("open_issues", []))]
    text = "\n".join((str(run_record["summary"]), *issues))
    durable: dict[str, list[tuple[str, str]]] = {kind: [] for kind in markers}
    for kind, values in markers.items():
        for line in text.splitlines():
            lowered = line.lower()
            if any(marker in lowered for marker in values):
                durable[kind].append((f"{task.id} {kind[:-1]}", line.strip()))
    return {kind: values for kind, values in durable.items() if values}


def _apply_implementation_transition(task: Task, run_record: dict[str, object]) -> Task:
    status = str(run_record["status"])
    files_changed = cast(list[object] | tuple[object, ...], run_record.get("files_changed", ()))
    files = tuple(str(item) for item in files_changed)
    implementation_status = str(run_record.get("implementation_status", "missing"))
    updated = task.with_implementation(implementation_status, files)
    if status == "implemented":
        return updated.with_workflow_stage("implemented")
    if status in {"checks_failed", "provider_failed", "no_changes"}:
        return updated
    return updated


def _apply_review_transition(task: Task, review_record: dict[str, object]) -> Task:
    review_status = str(review_record.get("review_status", review_record["decision"]))
    if review_status == REVIEW_APPROVED:
        return task.with_workflow_stage("reviewed")
    if review_status == REVIEW_CHANGES_REQUESTED:
        return task.with_workflow_stage("fix_ready")
    return task


def build_completion_record(task: Task) -> Task:
    record = {"kind": "completion", "status": "completed", "completed": True}
    updated = task.with_completion_record(record)
    return updated.complete()
