from __future__ import annotations

import json

from codex_cli.cli import main


def test_list_sorts_tasks_by_queue_position_before_task_id(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    active = tmp_path / "codex_cli" / "tasks" / "active"
    active.mkdir(parents=True)
    task_002 = {
        "id": "task_002",
        "objective": "second by id but first in queue",
        "queue_position": 1,
        "status": "active",
        "files": [],
        "constraints": [],
        "done_conditions": [],
        "created_at": "2026-05-05T17:13:32+00:00",
        "updated_at": "2026-05-05T17:13:32+00:00",
    }
    task_001 = {
        "id": "task_001",
        "objective": "first by id but later in queue",
        "queue_position": 2,
        "status": "active",
        "files": [],
        "constraints": [],
        "done_conditions": [],
        "created_at": "2026-05-05T17:13:32+00:00",
        "updated_at": "2026-05-05T17:13:32+00:00",
    }
    (active / "task_001.json").write_text(json.dumps(task_001), encoding="utf-8")
    (active / "task_002.json").write_text(json.dumps(task_002), encoding="utf-8")

    assert main(["list"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert [task["id"] for task in output["tasks"]] == ["task_002", "task_001"]
