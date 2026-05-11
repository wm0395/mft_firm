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


def _patch_checks(monkeypatch, status: str = "pass") -> None:
    checks = [{"name": "pytest", "status": status, "command": ["pytest"], "returncode": 0, "stdout": "", "stderr": ""}]
    monkeypatch.setattr("codex_cli.managed_runner.run_required_checks", lambda root: {"status": status, "checks": checks})


def test_run_queue_completes_active_tasks_in_order(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    assert main(["run", "implement another signal registry"]) == 0
    capsys.readouterr()
    _patch_checks(monkeypatch, "pass")
    monkeypatch.setattr("codex_cli.managed_runner.build_launch_command", lambda *args: ["/usr/bin/provider", "run"])
    monkeypatch.setattr(
        "codex_cli.managed_runner.launch_task",
        lambda provider, mode, prompt, workspace, model, json_output: LaunchResult(
            provider,
            mode,
            ("/usr/bin/provider", "run"),
            0,
            "Implemented project/signals.py\n",
            "",
            json_output,
            model,
        ),
    )

    assert main(["run-queue"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "completed"
    assert output["processed_tasks"] == 2
    assert output["cooldowns"] == 0
    assert [entry["task_id"] for entry in output["history"]] == ["task_001", "task_002"]


def test_run_queue_cools_down_and_retries_codex_limit(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    _patch_checks(monkeypatch, "pass")
    monkeypatch.setattr("codex_cli.managed_runner.build_launch_command", lambda *args: ["/usr/bin/provider", "run"])
    launches = iter(
        (
            LaunchResult("codex", ONESHOT, ("/usr/bin/provider", "run"), 1, "", "Usage limit reached. Try again in 5h\n", False, None),
            LaunchResult("codex", ONESHOT, ("/usr/bin/provider", "run"), 0, "Implemented project/signals.py\n", "", False, None),
        )
    )
    monkeypatch.setattr("codex_cli.managed_runner.launch_task", lambda *args: next(launches))
    sleeps: list[int] = []
    monkeypatch.setattr("codex_cli.queue_runner.time.sleep", lambda seconds: sleeps.append(seconds))

    assert main(["run-queue", "--cooldown-hours", "5"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "completed"
    assert output["processed_tasks"] == 1
    assert output["cooldowns"] == 1
    assert sleeps == [18000]
    assert output["history"][1]["status"] == "cooldown"


def test_run_queue_cools_down_on_codex_429_error(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    _patch_checks(monkeypatch, "pass")
    monkeypatch.setattr("codex_cli.managed_runner.build_launch_command", lambda *args: ["/usr/bin/provider", "run"])
    launches = iter(
        (
            LaunchResult("codex", ONESHOT, ("/usr/bin/provider", "run"), 1, "", "HTTP 429 from provider\n", False, None),
            LaunchResult("codex", ONESHOT, ("/usr/bin/provider", "run"), 0, "Implemented project/signals.py\n", "", False, None),
        )
    )
    monkeypatch.setattr("codex_cli.managed_runner.launch_task", lambda *args: next(launches))
    sleeps: list[int] = []
    monkeypatch.setattr("codex_cli.queue_runner.time.sleep", lambda seconds: sleeps.append(seconds))

    assert main(["run-queue", "--cooldown-hours", "5"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "completed"
    assert output["cooldowns"] == 1
    assert sleeps == [18000]
    assert output["history"][1]["status"] == "cooldown"


def test_run_queue_stops_on_non_limit_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    _patch_checks(monkeypatch, "pass")
    monkeypatch.setattr("codex_cli.managed_runner.build_launch_command", lambda *args: ["/usr/bin/provider", "run"])
    monkeypatch.setattr(
        "codex_cli.managed_runner.launch_task",
        lambda provider, mode, prompt, workspace, model, json_output: LaunchResult(
            provider,
            mode,
            ("/usr/bin/provider", "run"),
            7,
            "",
            "boom\n",
            json_output,
            model,
        ),
    )

    assert main(["run-queue"]) == 1

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "stopped"
    assert output["processed_tasks"] == 0
    assert output["cooldowns"] == 0
    assert output["stop_reason"] == "provider_failed"


def test_run_queue_rejects_non_positive_cooldown(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()

    assert main(["run-queue", "--cooldown-hours", "0"]) == 2

    assert "cooldown hours must be positive" in capsys.readouterr().err
