from __future__ import annotations

import json
import subprocess
from pathlib import Path

from codex_cli.cli import main
from codex_cli.launcher import LaunchResult, ONESHOT


def _prepare_task(tmp_path: Path, monkeypatch, objective: str = "implement signal registry") -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n- bounded\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(
        "codex_cli/\n.pytest_cache/\n.mypy_cache/\n.ruff_cache/\n__pycache__/\n*.pyc\n",
        encoding="utf-8",
    )
    (tmp_path / "project" / "signals").mkdir(parents=True)
    (tmp_path / "project" / "signals" / "__init__.py").write_text("def signal():\n    return 1\n", encoding="utf-8")
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "tests@example.com")
    _git(tmp_path, "config", "user.name", "Tests")
    _git(tmp_path, "add", "AGENTS.md", ".gitignore", "project/signals/__init__.py")
    _git(tmp_path, "commit", "-m", "initial")
    assert main(["run", objective]) == 0
    task_path = tmp_path / "codex_cli" / "tasks" / "active" / "task_001.json"
    task = json.loads(task_path.read_text(encoding="utf-8"))
    task["required_reviewers"] = ["architecture_reviewer"]
    task_path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")


def _patch_checks(monkeypatch, status: str = "pass") -> None:
    checks = [{"name": "pytest", "status": status, "command": ["pytest"], "returncode": 0, "stdout": "", "stderr": ""}]
    monkeypatch.setattr("codex_cli.managed_runner.run_required_checks", lambda root: {"status": status, "checks": checks})


def _patch_impl_provider(monkeypatch, results: list[LaunchResult]) -> None:
    monkeypatch.setattr("codex_cli.managed_runner.build_launch_command", lambda *args: ["/usr/bin/provider", "run"])
    launches = iter(results)
    counter = {"value": 1}

    def _launch(provider, mode, prompt, workspace, model, json_output):
        result = next(launches)
        if result.exit_code == 0:
            counter["value"] += 1
            target = workspace / "project" / "signals" / "__init__.py"
            target.write_text(f"def signal():\n    return {counter['value']}\n", encoding="utf-8")
        return result

    monkeypatch.setattr("codex_cli.managed_runner.launch_task", _launch)


def _patch_review_provider(monkeypatch, results: list[LaunchResult]) -> None:
    monkeypatch.setattr("codex_cli.review_runner.build_launch_command", lambda *args: ["/usr/bin/reviewer", "run"])
    launches = iter(results)
    monkeypatch.setattr("codex_cli.review_runner.launch_task", lambda *args: next(launches))


def _approve_review() -> str:
    return json.dumps(
        {
            "decision": "approve",
            "reviewer": "architecture_reviewer",
            "violations": [],
            "required_fixes": [],
            "evidence": [{"file": "project/signals/__init__.py", "reason": "Change stayed within scope."}],
        }
    )


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def test_run_queue_blocks_second_task_when_first_leaves_overlapping_scope_dirty(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    assert main(["run", "implement another signal registry"]) == 0
    capsys.readouterr()
    _patch_checks(monkeypatch, "pass")
    _patch_impl_provider(
        monkeypatch,
        [
            LaunchResult("codex", ONESHOT, ("/usr/bin/provider", "run"), 0, "Implemented project/signals.py\n", "", False, None),
            LaunchResult("codex", ONESHOT, ("/usr/bin/provider", "run"), 0, "Implemented project/signals.py\n", "", False, None),
        ],
    )
    _patch_review_provider(
        monkeypatch,
        [
            LaunchResult("codex", ONESHOT, ("/usr/bin/reviewer", "run"), 0, _approve_review(), "", False, None),
            LaunchResult("codex", ONESHOT, ("/usr/bin/reviewer", "run"), 0, _approve_review(), "", False, None),
        ],
    )

    assert main(["run-queue"]) == 1

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "stopped"
    assert output["processed_tasks"] == 1
    assert output["cooldowns"] == 0
    assert [entry["task_id"] for entry in output["history"] if entry["step"] == "complete"] == ["task_001"]
    assert output["history"][-1]["task_id"] == "task_002"
    assert output["history"][-1]["status"] == "preflight_blocked"
    assert output["stop_reason"] == "preflight_blocked"


def test_run_queue_cools_down_and_retries_codex_limit(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    _patch_checks(monkeypatch, "pass")
    _patch_impl_provider(
        monkeypatch,
        [
            LaunchResult("codex", ONESHOT, ("/usr/bin/provider", "run"), 1, "", "Usage limit reached. Try again in 5h\n", False, None),
            LaunchResult("codex", ONESHOT, ("/usr/bin/provider", "run"), 0, "Implemented project/signals.py\n", "", False, None),
        ],
    )
    _patch_review_provider(
        monkeypatch,
        [LaunchResult("codex", ONESHOT, ("/usr/bin/reviewer", "run"), 0, _approve_review(), "", False, None)],
    )
    sleeps: list[int] = []
    monkeypatch.setattr("codex_cli.queue_runner.time.sleep", lambda seconds: sleeps.append(seconds))

    assert main(["run-queue", "--cooldown-hours", "5"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "completed"
    assert output["processed_tasks"] == 1
    assert output["cooldowns"] == 0
    assert output["switches"] == 1
    assert sleeps == []
    assert output["history"][0]["status"] == "switch"
    assert output["history"][0]["to_model"] == "anthropic/claude-sonnet-4.5"


def test_run_queue_cools_down_on_codex_429_error(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    _patch_checks(monkeypatch, "pass")
    _patch_impl_provider(
        monkeypatch,
        [
            LaunchResult("codex", ONESHOT, ("/usr/bin/provider", "run"), 1, "", "HTTP 429 from provider\n", False, None),
            LaunchResult("codex", ONESHOT, ("/usr/bin/provider", "run"), 0, "Implemented project/signals.py\n", "", False, None),
        ],
    )
    _patch_review_provider(
        monkeypatch,
        [LaunchResult("codex", ONESHOT, ("/usr/bin/reviewer", "run"), 0, _approve_review(), "", False, None)],
    )
    sleeps: list[int] = []
    monkeypatch.setattr("codex_cli.queue_runner.time.sleep", lambda seconds: sleeps.append(seconds))

    assert main(["run-queue", "--cooldown-hours", "5"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "completed"
    assert output["cooldowns"] == 0
    assert output["switches"] == 1
    assert sleeps == []
    assert output["history"][0]["status"] == "switch"
    assert output["history"][0]["to_model"] == "anthropic/claude-sonnet-4.5"


def test_run_queue_stops_on_non_limit_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_task(tmp_path, monkeypatch)
    capsys.readouterr()
    _patch_checks(monkeypatch, "pass")
    _patch_impl_provider(
        monkeypatch,
        [LaunchResult("codex", ONESHOT, ("/usr/bin/provider", "run"), 7, "", "boom\n", False, None)],
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
