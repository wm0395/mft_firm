from __future__ import annotations

import json
from pathlib import Path

from codex_cli.managed_state import persist_review_state
from codex_cli.memory_store import MemoryStore
from codex_cli.models import Task
from codex_cli.paths import ProjectPaths
from codex_cli.prompts import build_review_packet
from codex_cli.review_runner import RunReviewOptions, _review_record
from codex_cli.scratchpad import ScratchpadStore
from codex_cli.tasks import TaskStore
from codex_cli.workflow import can_complete


def test_review_packet_includes_persona_prompt(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_contract_files(tmp_path)
    paths = ProjectPaths()
    packet = build_review_packet(_task(), paths, "scratchpad", ("ctx",), "codex", "architecture_reviewer", 900)
    block_names = [block.name for block in packet.prompt_blocks]
    assert "reviewer_persona" in block_names
    assert "architecture_reviewer" in packet.prompt


def test_review_packet_includes_latest_check_results(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_contract_files(tmp_path)
    paths = ProjectPaths()
    task = Task(
        **{
            **_task().to_dict(),
            "check_history": (
                {
                    "kind": "checks",
                    "status": "pass",
                    "checks": (
                        {"name": "pytest", "status": "pass"},
                        {"name": "ruff", "status": "pass"},
                    ),
                },
            ),
        }
    )
    packet = build_review_packet(task, paths, "scratchpad", ("ctx",), "codex", "test_failure_reviewer", 900)
    block_map = {block.name: block.content for block in packet.prompt_blocks}
    assert "check_results" in block_map
    assert "Latest Managed Checks:" in block_map["check_results"]
    assert "- pytest: pass" in block_map["check_results"]


def test_review_record_parses_strict_json() -> None:
    record = _review_record(
        _task(),
        0,
        json.dumps(
            {
                "decision": "approve",
                "reviewer": "architecture_reviewer",
                "violations": [],
                "required_fixes": [],
                "evidence": [{"file": "project/data/loader.py", "reason": "Stayed within the data layer."}],
            }
        ),
        "",
        RunReviewOptions(provider="codex", budget=900, model=None, json_output=False, persona="architecture_reviewer"),
        ["codex"],
        "2026-05-12T00:00:00+00:00",
        "2026-05-12T00:00:01+00:00",
        "architecture_reviewer",
    )
    assert record["decision"] == "approve"
    assert record["review_status"] == "approved"
    assert record["reviewer"] == "architecture_reviewer"


def test_review_record_parses_jsonl_agent_message() -> None:
    record = _review_record(
        _task(),
        0,
        "\n".join(
            (
                json.dumps({"type": "thread.started"}),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "item_0",
                            "type": "agent_message",
                            "text": json.dumps(
                                {
                                    "decision": "approve",
                                    "reviewer": "architecture_reviewer",
                                    "violations": [],
                                    "required_fixes": [],
                                    "evidence": [
                                        {
                                            "file": "project/signals/__init__.py",
                                            "reason": "Change stayed within scope.",
                                        }
                                    ],
                                }
                            ),
                        },
                    }
                ),
            )
        ),
        "",
        RunReviewOptions(provider="codex", budget=900, model=None, json_output=True, persona="architecture_reviewer"),
        ["codex"],
        "2026-05-12T00:00:00+00:00",
        "2026-05-12T00:00:01+00:00",
        "architecture_reviewer",
    )
    assert record["decision"] == "approve"
    assert record["review_status"] == "approved"
    assert record["reviewer"] == "architecture_reviewer"


def test_malformed_review_output_blocks_completion(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_contract_files(tmp_path)
    _, tasks, scratchpads, memory = _stores()
    task = _task()
    tasks.save(task)
    scratchpads.create(task)
    record = _review_record(
        task,
        0,
        "Review Decision: approve",
        "",
        RunReviewOptions(provider="codex", budget=900, model=None, json_output=False, persona="architecture_reviewer"),
        ["codex"],
        "2026-05-12T00:00:00+00:00",
        "2026-05-12T00:00:01+00:00",
        "architecture_reviewer",
    )
    updated = persist_review_state(task, tasks, scratchpads, memory, record)
    assert updated.review_status == "review_failed"
    assert updated.workflow_stage == "implemented"
    assert not can_complete(updated)


def test_changes_requested_moves_task_to_fix_ready(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_contract_files(tmp_path)
    _, tasks, scratchpads, memory = _stores()
    task = _task()
    tasks.save(task)
    scratchpads.create(task)
    record = {
        "kind": "review_run",
        "task_id": task.id,
        "provider": "codex",
        "command": ["codex"],
        "budget": 900,
        "model": None,
        "json_output": False,
        "started_at": "2026-05-12T00:00:00+00:00",
        "finished_at": "2026-05-12T00:00:01+00:00",
        "exit_code": 0,
        "decision": "changes_requested",
        "review_status": "changes_requested",
        "reviewer": "architecture_reviewer",
        "violations": [{"file": "project/replay/engine.py", "rule": "No DB access outside project/data", "evidence": "ReplayEngine accesses repository._db directly."}],
        "required_fixes": ["Move the query into DataRepository."],
        "evidence": [],
        "summary": "Move the query into DataRepository.",
        "stdout": "",
        "stderr": "",
    }
    updated = persist_review_state(task, tasks, scratchpads, memory, record)
    assert updated.review_status == "changes_requested"
    assert updated.workflow_stage == "fix_ready"
    assert not can_complete(updated)


def test_approve_allows_completion_when_implementation_is_verified(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_contract_files(tmp_path)
    _, tasks, scratchpads, memory = _stores()
    task = _task()
    tasks.save(task)
    scratchpads.create(task)
    record = {
        "kind": "review_run",
        "task_id": task.id,
        "provider": "codex",
        "command": ["codex"],
        "budget": 900,
        "model": None,
        "json_output": False,
        "started_at": "2026-05-12T00:00:00+00:00",
        "finished_at": "2026-05-12T00:00:01+00:00",
        "exit_code": 0,
        "decision": "approve",
        "review_status": "approved",
        "reviewer": "architecture_reviewer",
        "violations": [],
        "required_fixes": [],
        "evidence": [{"file": "project/data/loader.py", "reason": "Change stayed inside scope."}],
        "summary": "architecture_reviewer approved the implementation.",
        "stdout": "",
        "stderr": "",
    }
    updated = persist_review_state(task, tasks, scratchpads, memory, record)
    assert updated.review_status == "approved"
    assert updated.workflow_stage == "reviewed"
    assert can_complete(updated)


def test_completion_requires_all_declared_reviewers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_contract_files(tmp_path)
    _, tasks, scratchpads, memory = _stores()
    task = _task().with_review_status("pending")
    task = Task(
        **{
            **task.to_dict(),
            "required_reviewers": ("architecture_reviewer", "determinism_auditor"),
            "review_history": (),
        }
    )
    tasks.save(task)
    scratchpads.create(task)
    architecture_record = {
        "kind": "review_run",
        "task_id": task.id,
        "provider": "codex",
        "command": ["codex"],
        "budget": 900,
        "model": None,
        "json_output": False,
        "started_at": "2026-05-12T00:00:00+00:00",
        "finished_at": "2026-05-12T00:00:01+00:00",
        "exit_code": 0,
        "decision": "approve",
        "review_status": "approved",
        "reviewer": "architecture_reviewer",
        "violations": [],
        "required_fixes": [],
        "evidence": [{"file": "project/data/loader.py", "reason": "Stayed inside scope."}],
        "summary": "architecture_reviewer approved the implementation.",
        "stdout": "",
        "stderr": "",
    }
    updated = persist_review_state(task, tasks, scratchpads, memory, architecture_record)
    assert updated.workflow_stage == "reviewed"
    assert not can_complete(updated)


def test_reviewer_prompt_files_are_not_empty(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_contract_files(tmp_path)
    names = (
        "architecture_reviewer.md",
        "complexity_reviewer.md",
        "determinism_auditor.md",
        "financial_logic_auditor.md",
        "test_failure_reviewer.md",
    )
    for name in names:
        text = (tmp_path / "agents" / "prompts" / name).read_text(encoding="utf-8")
        assert text.strip()


def _stores() -> tuple[ProjectPaths, TaskStore, ScratchpadStore, MemoryStore]:
    paths = ProjectPaths()
    return paths, TaskStore(paths), ScratchpadStore(paths), MemoryStore(paths)


def _task() -> Task:
    return Task(
        id="task_001",
        objective="Make review decisions enforceable.",
        files=("codex_cli/review_runner.py",),
        constraints=("No upward imports",),
        done_conditions=("review output is strict JSON",),
        required_reviewers=("architecture_reviewer",),
        workflow_stage="implemented",
        implementation_status="verified",
        implementation_files=("codex_cli/review_runner.py",),
        run_history=(
            {
                "kind": "managed_run",
                "status": "implemented",
                "diff_guard": {
                    "status": "passed",
                    "changed_files": ["codex_cli/review_runner.py"],
                    "undeclared_files": [],
                    "scope_ok": True,
                },
            },
        ),
    )


def _write_contract_files(root: Path) -> None:
    (root / "AGENTS.md").write_text((Path(__file__).resolve().parents[2] / "AGENTS.md").read_text(encoding="utf-8"), encoding="utf-8")
    prompts_dir = root / "agents" / "prompts"
    prompts_dir.mkdir(parents=True)
    source_dir = Path(__file__).resolve().parents[2] / "agents" / "prompts"
    for name in (
        "architecture_reviewer.md",
        "complexity_reviewer.md",
        "determinism_auditor.md",
        "financial_logic_auditor.md",
        "test_failure_reviewer.md",
    ):
        (prompts_dir / name).write_text((source_dir / name).read_text(encoding="utf-8"), encoding="utf-8")
