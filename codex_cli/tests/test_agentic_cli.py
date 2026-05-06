from __future__ import annotations

import json
from pathlib import Path

from codex_cli.architecture import self_heal
from codex_cli.cli import main
from codex_cli.diagnosis import diagnose_task
from codex_cli.models import Task
from codex_cli.paths import ProjectPaths
from codex_cli.prompts import build_prompt


def test_run_creates_task_scratchpad_and_review(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")

    assert main(["run", "build prompt builder"]) == 0

    task_path = tmp_path / "codex_cli" / "tasks" / "active" / "task_001.json"
    scratchpad_path = tmp_path / "codex_cli" / "memory" / "scratchpads" / "task_001.md"

    task = json.loads(task_path.read_text(encoding="utf-8"))
    scratchpad = scratchpad_path.read_text(encoding="utf-8")

    assert task["description"] == "build prompt builder"
    assert task["route"] == "executor"
    assert task["review"]["verdict"] == "accept"
    assert "# Task: build prompt builder" in scratchpad


def test_complex_task_routes_to_planner(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["run", "build multi module architecture pipeline"]) == 0

    task = json.loads((tmp_path / "codex_cli" / "tasks" / "active" / "task_001.json").read_text(encoding="utf-8"))
    assert task["route"] == "planner"
    assert task["subtasks"][0]["desc"] == "build multi module architecture pipeline"


def test_complete_moves_task_to_completed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["run", "small task"]) == 0

    assert main(["complete", "task_001"]) == 0

    assert not (tmp_path / "codex_cli" / "tasks" / "active" / "task_001.json").exists()
    assert (tmp_path / "codex_cli" / "tasks" / "completed" / "task_001.json").exists()


def test_executor_prompt_uses_system_and_executor_templates() -> None:
    task = Task(id="task_123", description="build signal registry")

    prompt = build_prompt(
        task,
        scratchpad="# Task: build signal registry\n",
        agents_rules="# Rules\n- No direct DB writes outside data layer\n",
    )

    assert "You are an execution agent for the MFT system." in prompt
    assert "data → signals → hypotheses → trade → decision → portfolio" in prompt
    assert "KNOWN FAILURE PATTERNS:" in prompt
    assert "Goal:\nImplement subtask with correct architecture." in prompt
    assert "Subtask:" in prompt
    assert "AGENTS.md Rules:" in prompt
    assert "No direct DB writes outside data layer" in prompt


def test_diagnose_matches_known_violation_pattern(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = ProjectPaths()
    paths.ensure()
    task = Task(
        id="task_123",
        description="fix hypothesis imports data",
        review={"architecture_violations": ["hypothesis imports data"]},
    )

    diagnosis = diagnose_task(task, paths)

    assert diagnosis["violations"][0]["violation"] == "signal_leakage"
    assert diagnosis["violations"][0]["fix"] == "move logic to signal layer"


def test_check_drift_command_reports_score(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["check", "drift"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["drift_score"] == 100
    assert output["violations"] == []


def test_fix_command_builds_architecture_only_prompt(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["run", "fix hypothesis imports data"]) == 0
    capsys.readouterr()

    assert main(["fix", "task_001"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "ready"
    assert "Fix architecture violations ONLY." in output["prompt"]


def test_self_heal_loop_runs_executor_before_architecture_check() -> None:
    calls = []

    def run_executor() -> dict[str, object]:
        calls.append("executor")
        return {"status": "ready"}

    def architecture_passes() -> dict[str, object]:
        calls.append("architecture")
        return {"status": "pass"}

    def diagnose() -> dict[str, object]:
        calls.append("diagnose")
        return {}

    def fix(diagnosis: dict[str, object]) -> dict[str, object]:
        calls.append("fix")
        return diagnosis

    result = self_heal("task_001", run_executor, architecture_passes, diagnose, fix)

    assert result["status"] == "pass"
    assert calls == ["executor", "architecture"]
