from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess
from typing import cast

import pytest

from codex_cli.architecture import self_heal
from codex_cli.cache import build_index, cache_status, retrieve_context
from codex_cli.cli import main
from codex_cli.diagnosis import diagnose_task
from codex_cli.launcher import _build_env, build_launch_command
from codex_cli.models import Task
from codex_cli.paths import ProjectPaths
from codex_cli.prompts import build_execution_packet
from codex_cli.router import recommend_provider, route


def test_module_entrypoint_supports_python_dash_m_cli() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "codex_cli.cli", "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    assert "usage: ai_code" in result.stdout


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
    assert task["required_reviewers"] == [
        "architecture_reviewer",
        "complexity_reviewer",
        "determinism_auditor",
        "financial_logic_auditor",
        "test_failure_reviewer",
    ]
    assert output["execution"]["provider"] == "opencode"
    assert output["review"]["provider"] == "opencode"
    assert output["memory"]["summary"]["kind"] == "summaries"


def test_plan_routes_complex_work_to_planner(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")

    assert main(["plan", "refactor architecture drift in signal pipeline"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["task"]["route"] == "planner"
    assert output["plan"]["subtasks"][0]["objective"] == "refactor architecture drift in signal pipeline"
    assert output["task"]["recommended_provider"] == "opencode"


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


def test_execute_dry_run_builds_opencode_oneshot_command(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
    assert main(["run", "implement signal registry"]) == 0
    capsys.readouterr()

    assert main(["execute", "task_001", "--mode", "oneshot", "--json", "--dry-run"]) == 0

    output = json.loads(capsys.readouterr().out)
    command = output["launch"]["command"]
    assert command[:4] == ["/usr/bin/opencode", "run", "--dir", str(tmp_path)]
    assert "--format" in command
    assert "--json" not in command
    assert "--model" in command
    assert output["launch"]["provider"] == "opencode"
    assert output["launch"]["model"] == "google/gemini-2.5-pro"


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
    assert "--model" in command
    assert "openai/gpt-5.1-codex" in command


def test_execute_rejects_gemini_launch(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
    assert main(["plan", "review architecture drift"]) == 0
    capsys.readouterr()

    with pytest.raises(SystemExit) as excinfo:
        main(["execute", "task_001", "--provider", "gemini"])
    assert excinfo.value.code == 2
    assert "invalid choice: 'gemini'" in capsys.readouterr().err


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
    assert output["launch"]["model"] == "google/gemini-2.5-pro"
    task = json.loads((tmp_path / "codex_cli" / "tasks" / "active" / "task_001.json").read_text(encoding="utf-8"))
    assert task["status"] == "active"
    assert task["packet_history"][-1]["kind"] == "launch"
    assert task["packet_history"][-1]["provider"] == "opencode"
    assert task["packet_history"][-1]["model"] == "google/gemini-2.5-pro"


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
    violations = cast(list[dict[str, object]], diagnosis["violations"])

    assert violations[0]["violation"] == "signal_leakage"
    assert violations[0]["fix"] == "move logic to signal layer"


def test_router_recommends_provider_by_work_type() -> None:
    assert route("small signal fix") == "executor"
    assert route("architecture refactor for imports") == "planner"
    assert recommend_provider("generate tests for many files", "executor") == "opencode"
    assert recommend_provider("design review for signal logic", "planner") == "opencode"


def test_build_index_and_retrieve_context(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = ProjectPaths()
    paths.ensure()
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / "signals.py").write_text("def build_signal():\n    return 1\n", encoding="utf-8")
    runtime_note = tmp_path / "codex_cli" / "runtime" / "codex" / "home" / ".codex" / "note.txt"
    runtime_note.parent.mkdir(parents=True)
    runtime_note.write_text("runtime artifact\n", encoding="utf-8")
    build_index(paths)

    context = retrieve_context(paths, "build signal")
    status = cache_status(paths)
    assert "project/signals.py" in context
    assert cast(int, status["index_entries"]) >= 1
    assert not any("runtime" in path for path in context)
    assert paths.cache == tmp_path / "codex_cli" / "state" / "cache"


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


def test_launcher_build_env_uses_workspace_local_codex_runtime(tmp_path: Path) -> None:
    env = _build_env(tmp_path, "codex")
    runtime_root = tmp_path / "codex_cli" / "runtime" / "codex"

    assert env["HOME"] == str(runtime_root / "home")
    assert env["XDG_CONFIG_HOME"] == str(runtime_root / "xdg" / "config")
    assert env["XDG_DATA_HOME"] == str(runtime_root / "xdg" / "data")
    assert env["XDG_STATE_HOME"] == str(runtime_root / "xdg" / "state")
    assert env["XDG_CACHE_HOME"] == str(runtime_root / "xdg" / "cache")
    assert env["CODEX_HOME"] == str(runtime_root / "home" / ".codex")
    assert env["TMPDIR"] == str(runtime_root / "tmp")
    assert env["TMP"] == str(runtime_root / "tmp")
    assert env["TEMP"] == str(runtime_root / "tmp")
    assert env["MYPY_CACHE_DIR"] == str(runtime_root / "mypy_cache")
    assert (runtime_root / "home").is_dir()
    assert (runtime_root / "home" / ".codex").is_dir()
    assert (runtime_root / "tmp").is_dir()
    assert (runtime_root / "mypy_cache").is_dir()


def test_launcher_build_env_uses_workspace_local_opencode_runtime(tmp_path: Path) -> None:
    env = _build_env(tmp_path, "opencode")
    runtime_root = tmp_path / "codex_cli" / "runtime" / "opencode"
    config_path = runtime_root / "xdg" / "config" / "opencode.json"

    assert env["HOME"] == str(runtime_root / "home")
    assert env["XDG_CONFIG_HOME"] == str(runtime_root / "xdg" / "config")
    assert env["XDG_DATA_HOME"] == str(runtime_root / "xdg" / "data")
    assert env["XDG_STATE_HOME"] == str(runtime_root / "xdg" / "state")
    assert env["XDG_CACHE_HOME"] == str(runtime_root / "xdg" / "cache")
    assert env["OPENCODE_CONFIG"] == str(config_path)
    assert env["TMPDIR"] == str(runtime_root / "tmp")
    assert env["MYPY_CACHE_DIR"] == str(runtime_root / "mypy_cache")
    assert config_path.read_text(encoding="utf-8").count("google/gemini-2.5-pro") >= 1
    assert (runtime_root / "home").is_dir()
    assert config_path.is_file()


def test_build_launch_command_sets_codex_workspace_write_sandbox(tmp_path: Path) -> None:
    command = build_launch_command("codex", "oneshot", "prompt", tmp_path, None, True)

    assert command[:5] == ["/usr/bin/codex", "exec", "--sandbox", "workspace-write", "-C"]


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
