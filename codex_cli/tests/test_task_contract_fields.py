from __future__ import annotations

import json

from codex_cli.cli import main


def test_run_creates_task_with_contract_fields(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Rules\n- bounded\n", encoding="utf-8")
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / "signals.py").write_text("def signal():\n    return 1\n", encoding="utf-8")

    assert main(["run", "implement signal registry"]) == 0

    output = json.loads(capsys.readouterr().out)
    task = output["task"]
    assert task["risk_level"] == "medium"
    assert task["allowed_change_set"] == ["project/signals"]
    assert task["required_checks"] == [
        "pytest passes",
        "ruff passes",
        "typing passes",
        "no architecture violations",
    ]
    assert task["required_reviewers"] == [
        "architecture_reviewer",
        "complexity_reviewer",
        "determinism_auditor",
        "financial_logic_auditor",
        "test_failure_reviewer",
    ]


def test_list_preserves_explicit_contract_fields(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    active = tmp_path / "codex_cli" / "tasks" / "active"
    active.mkdir(parents=True)
    task = {
        "id": "task_001",
        "objective": "task with explicit contract fields",
        "files": ["project/data/repository.py"],
        "constraints": ["Stay within scope"],
        "done_conditions": ["pytest passes"],
        "risk_level": "critical",
        "allowed_change_set": ["project/data/repository.py", "tests/test_replay.py"],
        "required_checks": ["python -m pytest", "python -m mypy"],
        "required_reviewers": ["architecture_reviewer", "determinism_auditor"],
        "created_at": "2026-05-12T00:00:00+00:00",
        "updated_at": "2026-05-12T00:00:00+00:00",
    }
    (active / "task_001.json").write_text(json.dumps(task), encoding="utf-8")

    assert main(["list"]) == 0

    output = json.loads(capsys.readouterr().out)
    listed = output["tasks"][0]
    assert listed["risk_level"] == "critical"
    assert listed["allowed_change_set"] == ["project/data/repository.py", "tests/test_replay.py"]
    assert listed["required_checks"] == ["python -m pytest", "python -m mypy"]
    assert listed["required_reviewers"] == ["architecture_reviewer", "determinism_auditor"]
