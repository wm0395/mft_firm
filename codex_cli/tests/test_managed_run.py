from __future__ import annotations

import json
from pathlib import Path

from codex_cli.cli import main
from codex_cli.launcher import LaunchResult, ONESHOT


def _prepare_task(tmp_path: Path, monkeypatch, objective: str = "implement signal registry") -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n- bounded\n", encoding="utf-8")
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / "signals.py").write_text("def signal():\n    return 1\n", encoding="utf-8")
    assert main(["run", objective]) == 0


def _patch_provider(monkeypatch, stdout: str, stderr: str = "", exit_code: int = 0) -> None:
    monkeypatch.setattr("codex_cli.managed_runner.build_launch_command", lambda *args: ["/usr/bin/provider", "run"])
    monkeypatch.setattr(
        "codex_cli.managed_runner.launch_task",
        lambda provider, mode, prompt, workspace, model, json_output: LaunchResult(
            provider,
            mode,
            ("/usr/bin/provider", "run"),
            exit_code,
            stdout,
            stderr,
            json_output,
            model,
        ),
    )


def _patch_checks(monkeypatch, status: str = "pass") -> None:
    checks = [{"name": "pytest", "status": status, "command": ["pytest"], "returncode": 0, "stdout": "", "stderr": ""}]
    if status == "fail":
        checks[0]["returncode"] = 1
        checks[0]["stderr"] = "failed\n"
    monkeypatch.setattr("codex_cli.managed_runner.run_required_checks", lambda root: {"status": status, "checks": checks})


def test_run_task_completes_codex_task_after_green_checks(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    _patch_provider(monkeypatch, '{"summary":"Implemented project/signals.py"}\n', "")
    _patch_checks(monkeypatch, "pass")

    assert main(["run-task", "task_001", "--json"]) == 0

    output = json.loads(capsys.readouterr().out)
    task = output["task"]
    assert output["status"] == "completed"
    assert task["status"] == "completed"
    assert task["run_history"][-1]["provider"] == "codex"
    assert task["check_history"][-1]["status"] == "pass"
    latest = json.loads((tmp_path / "codex_cli" / "memory" / "runs" / "task_001" / "latest.json").read_text(encoding="utf-8"))
    assert latest["run"]["status"] == "completed"


def test_run_task_completes_opencode_task_with_default_provider(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch, "generate tests for many files")
    capsys.readouterr()
    _patch_provider(monkeypatch, "Updated project/signals.py\n")
    _patch_checks(monkeypatch, "pass")

    assert main(["run-task", "task_001"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["task"]["run_history"][-1]["provider"] == "opencode"
    assert output["task"]["status"] == "completed"


def test_run_task_persists_stdout_stderr_and_events(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    stdout = '{"summary":"Implemented project/signals.py"}\n{"message":"Done"}\n'
    _patch_provider(monkeypatch, stdout, "warn\n")
    _patch_checks(monkeypatch, "pass")

    assert main(["run-task", "task_001", "--json"]) == 0

    capsys.readouterr()
    run_dir = tmp_path / "codex_cli" / "memory" / "runs" / "task_001"
    assert (run_dir / "stdout.txt").read_text(encoding="utf-8") == stdout
    assert (run_dir / "stderr.txt").read_text(encoding="utf-8") == "warn\n"
    events = (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(events[0])["summary"] == "Implemented project/signals.py"


def test_run_task_updates_scratchpad_after_managed_run(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    _patch_provider(monkeypatch, "Implemented project/signals.py\n")
    _patch_checks(monkeypatch, "pass")

    assert main(["run-task", "task_001"]) == 0

    capsys.readouterr()
    scratchpad = (tmp_path / "codex_cli" / "memory" / "scratchpads" / "task_001.md").read_text(encoding="utf-8")
    assert "## Execution History" in scratchpad
    assert "Implemented project/signals.py" in scratchpad
    assert "Task Status: completed" in scratchpad


def test_run_task_keeps_task_active_on_provider_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    _patch_provider(monkeypatch, "", "boom\n", exit_code=7)
    _patch_checks(monkeypatch, "pass")

    assert main(["run-task", "task_001"]) == 7

    output = json.loads(capsys.readouterr().out)
    assert output["task"]["status"] == "active"
    assert output["checks"] is None
    assert output["task"]["run_history"][-1]["status"] == "provider_failed"


def test_run_task_keeps_task_active_when_checks_fail(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    _patch_provider(monkeypatch, "Implemented project/signals.py\n")
    _patch_checks(monkeypatch, "fail")

    assert main(["run-task", "task_001"]) == 1

    output = json.loads(capsys.readouterr().out)
    assert output["task"]["status"] == "active"
    assert output["checks"]["status"] == "fail"
    assert output["task"]["run_history"][-1]["status"] == "checks_failed"


def test_run_task_resume_includes_prior_memory_and_last_run_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    _patch_provider(monkeypatch, "First summary line\n")
    _patch_checks(monkeypatch, "pass")
    assert main(["run-task", "task_001", "--no-checks"]) == 0
    capsys.readouterr()

    _patch_provider(monkeypatch, "Second summary line\n")
    _patch_checks(monkeypatch, "pass")
    assert main(["run-task", "task_001", "--resume", "--no-checks"]) == 0

    output = json.loads(capsys.readouterr().out)
    context = output["execution"]["retrieved_context"]
    assert any("Recent Run Summary" in item for item in context)
    assert any("Memory Ref:" in item for item in context)


def test_run_task_creates_durable_memory_only_for_qualifying_markers(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    stdout = "DECISION: keep signal logic isolated\nPATTERN: explicit packet persistence\n"
    _patch_provider(monkeypatch, stdout)
    _patch_checks(monkeypatch, "pass")

    assert main(["run-task", "task_001"]) == 0

    capsys.readouterr()
    decisions = list((tmp_path / "codex_cli" / "memory" / "decisions").glob("*.json"))
    patterns = list((tmp_path / "codex_cli" / "memory" / "patterns").glob("*.json"))
    bugs = list((tmp_path / "codex_cli" / "memory" / "bugs").glob("*.json"))
    summaries = list((tmp_path / "codex_cli" / "memory" / "summaries").glob("*.json"))
    assert len(decisions) == 1
    assert len(patterns) == 1
    assert bugs == []
    assert summaries


def test_run_task_dry_run_lists_managed_steps_and_command(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    monkeypatch.setattr("codex_cli.managed_runner.build_launch_command", lambda *args: ["/usr/bin/provider", "run"])

    assert main(["run-task", "task_001", "--dry-run"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["managed_steps"][0] == "prepare task context"
    assert output["launch"]["mode"] == ONESHOT
    assert output["launch"]["command"] == ["/usr/bin/provider", "run"]
