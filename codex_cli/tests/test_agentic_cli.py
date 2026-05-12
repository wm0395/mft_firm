from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess

from codex_cli.architecture import self_heal
from codex_cli.cache import build_index, cache_status, retrieve_context
from codex_cli.cli import main
from codex_cli.diagnosis import diagnose_task
from codex_cli.models import Task
from codex_cli.paths import ProjectPaths
from codex_cli.prompts import build_execution_packet
from codex_cli.router import recommend_provider, route


def test_run_creates_structured_task_packets_and_memory(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n- keep it bounded\n", encoding="utf-8")
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / "signals.py").write_text("def signal():\n    return 1\n", encoding="utf-8")

    assert main(["run", "implement signal registry"]) == 0

    output = json.loads(capsys.readouterr().out)
    task = output["task"]
    assert task["objective"] == "implement signal registry"
    assert task["constraints"][0] == "No upward imports"
    assert task["done_conditions"][-1] == "no architecture violations"
    assert output["execution"]["provider"] == "codex"
    assert output["review"]["provider"] == "gemini"
    assert output["memory"]["summary"]["kind"] == "summaries"


def test_plan_routes_complex_work_to_planner(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")

    assert main(["plan", "refactor architecture drift in signal pipeline"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["task"]["route"] == "planner"
    assert output["plan"]["subtasks"][0]["objective"] == "refactor architecture drift in signal pipeline"
    assert output["task"]["recommended_provider"] == "gemini"


def test_exec_builds_provider_specific_packet(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
    assert main(["run", "implement signal registry"]) == 0
    capsys.readouterr()

    assert main(["exec", "task_001", "--provider", "opencode", "--budget", "200"]) == 0

    output = json.loads(capsys.readouterr().out)
    execution = output["execution"]
    assert execution["provider"] == "opencode"
    assert execution["budget"] == 200
    assert "trade_engine" in execution["prompt"]


def test_execute_dry_run_builds_codex_oneshot_command(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
    assert main(["run", "implement signal registry"]) == 0
    capsys.readouterr()

    assert main(["execute", "task_001", "--mode", "oneshot", "--json", "--dry-run"]) == 0

    output = json.loads(capsys.readouterr().out)
    command = output["launch"]["command"]
    assert command[:3] == ["/usr/bin/codex", "exec", "-C"]
    assert "--json" in command
    assert output["launch"]["provider"] == "codex"


def test_execute_dry_run_builds_opencode_interactive_command(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
    assert main(["run", "generate tests for many files"]) == 0
    capsys.readouterr()

    assert main(["execute", "task_001", "--provider", "opencode", "--dry-run", "--mode", "interactive"]) == 0

    output = json.loads(capsys.readouterr().out)
    command = output["launch"]["command"]
    assert command[:3] == ["/usr/bin/opencode", "--dir", str(tmp_path)]
    assert "--prompt" in command


def test_execute_rejects_gemini_launch(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
    assert main(["plan", "review architecture drift"]) == 0
    capsys.readouterr()

    assert main(["execute", "task_001"]) == 2
    assert "Unsupported launch provider: gemini" in capsys.readouterr().err


def test_execute_rejects_json_in_interactive_mode(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
    assert main(["run", "implement signal registry"]) == 0
    capsys.readouterr()

    assert main(["execute", "task_001", "--json"]) == 2
    assert "--json is only supported in oneshot mode" in capsys.readouterr().err


def test_execute_oneshot_records_launch_result(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
    assert main(["run", "implement signal registry"]) == 0
    capsys.readouterr()

    def fake_run(command, check, capture_output=False, text=False, env=None):
        return CompletedProcess(command, 0, stdout="ok\n" if capture_output else None, stderr="")

    monkeypatch.setattr("codex_cli.launcher.subprocess.run", fake_run)
    monkeypatch.setattr("codex_cli.launcher.shutil.which", lambda name: f"/usr/bin/{name}")

    assert main(["execute", "task_001", "--mode", "oneshot", "--json"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["launch"]["exit_code"] == 0
    assert output["launch"]["stdout"] == "ok\n"
    task = json.loads((tmp_path / "codex_cli" / "tasks" / "active" / "task_001.json").read_text(encoding="utf-8"))
    assert task["status"] == "active"
    assert task["packet_history"][-1]["kind"] == "launch"
    assert task["packet_history"][-1]["provider"] == "codex"


def test_execute_oneshot_returns_nonzero_and_records_attempt(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
    assert main(["run", "implement signal registry"]) == 0
    capsys.readouterr()

    def fake_run(command, check, capture_output=False, text=False, env=None):
        return CompletedProcess(command, 7, stdout="", stderr="boom\n")

    monkeypatch.setattr("codex_cli.launcher.subprocess.run", fake_run)
    monkeypatch.setattr("codex_cli.launcher.shutil.which", lambda name: f"/usr/bin/{name}")

    assert main(["execute", "task_001", "--mode", "oneshot"]) == 7

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "failed"
    assert output["launch"]["exit_code"] == 7
    task = json.loads((tmp_path / "codex_cli" / "tasks" / "active" / "task_001.json").read_text(encoding="utf-8"))
    assert task["packet_history"][-1]["exit_code"] == 7


def test_cache_build_and_status(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / "decision.py").write_text("class Decision:\n    pass\n", encoding="utf-8")

    assert main(["cache", "build"]) == 0
    build_output = json.loads(capsys.readouterr().out)
    assert build_output["cache"]["entries"] >= 1

    assert main(["cache", "status"]) == 0
    status_output = json.loads(capsys.readouterr().out)
    assert status_output["cache"]["index_entries"] >= 1


def test_check_drift_uses_current_contract(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["check", "drift"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["checks"]["drift_score"] == 100
    assert output["checks"]["violations"] == []


def test_diagnose_matches_known_violation_pattern(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = ProjectPaths()
    paths.ensure()
    task = Task(
        id="task_123",
        objective="fix hypothesis imports data",
        files=(),
        constraints=(),
        done_conditions=(),
    )

    diagnosis = diagnose_task(task, paths)

    assert diagnosis["violations"][0]["violation"] == "signal_leakage"
    assert diagnosis["violations"][0]["fix"] == "move logic to signal layer"


def test_router_recommends_provider_by_work_type() -> None:
    assert route("small signal fix") == "executor"
    assert route("architecture refactor for imports") == "planner"
    assert recommend_provider("generate tests for many files", "executor") == "opencode"
    assert recommend_provider("design review for signal logic", "planner") == "gemini"


def test_build_index_and_retrieve_context(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = ProjectPaths()
    paths.ensure()
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / "signals.py").write_text("def build_signal():\n    return 1\n", encoding="utf-8")
    build_index(paths)

    context = retrieve_context(paths, "build signal")
    assert "project/signals.py" in context
    assert cache_status(paths)["index_entries"] >= 1


def test_execution_packet_trims_context_when_budget_is_small(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n- bounded\n", encoding="utf-8")
    paths = ProjectPaths()
    paths.ensure()
    task = Task(
        id="task_001",
        objective="implement signal registry",
        files=("project/signals.py",),
        constraints=("No upward imports",),
        done_conditions=("pytest passes",),
    )

    packet = build_execution_packet(
        task,
        paths,
        "scratchpad " * 50,
        ("project/signals.py", "docs/planning/codex cli.md"),
        "codex",
        20,
    )

    names = [block["name"] for block in packet.to_dict()["prompt_blocks"]]
    assert "system_rules" in names
    assert "retrieved_context" not in names


def test_execution_packet_requests_direct_implementation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n- bounded\n", encoding="utf-8")
    paths = ProjectPaths()
    paths.ensure()
    task = Task(
        id="task_001",
        objective="implement signal registry",
        files=("project/signals.py",),
        constraints=("No upward imports",),
        done_conditions=("pytest passes",),
    )

    packet = build_execution_packet(
        task,
        paths,
        "# Task\n",
        ("project/signals.py",),
        "codex",
        400,
    )

    assert "Implement the assigned task by editing the declared files" in packet.prompt
    assert "Prepare an implementation packet" not in packet.prompt


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


def test_list_accepts_legacy_task_schema(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    active = tmp_path / "codex_cli" / "tasks" / "active"
    active.mkdir(parents=True)
    legacy_task = {
        "id": "task_001",
        "description": "legacy task",
        "status": "active",
        "subtasks": [{"id": 1, "desc": "legacy subtask"}],
        "files": [],
        "created_at": "2026-05-05T17:13:32+00:00",
        "updated_at": "2026-05-05T17:13:32+00:00",
        "route": "planner",
    }
    (active / "task_001.json").write_text(json.dumps(legacy_task), encoding="utf-8")

    assert main(["list"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["tasks"][0]["objective"] == "legacy task"
    assert output["tasks"][0]["subtasks"][0]["objective"] == "legacy subtask"
