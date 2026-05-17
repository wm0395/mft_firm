from __future__ import annotations

from pathlib import Path
import json

import pytest

from project.cli import main
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
import project.cli_research as cli_research


def test_research_lifecycle_read_only_command_skips_schema_bootstrap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    repository.close()

    def fail_initialize_schema(self) -> None:
        raise AssertionError("read-only research command must not bootstrap schema")

    monkeypatch.setattr(DuckDBAccess, "initialize_schema", fail_initialize_schema)
    monkeypatch.setattr(
        DataRepository,
        "list_research_projects",
        lambda self: [{"research_project_id": "research_project:example"}],
        raising=False,
    )

    exit_code = main(["list-research-projects", "--database", str(db_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "list-research-projects"
    assert payload["status"] == "ok"
    assert payload["result"][0]["research_project_id"] == "research_project:example"


def test_research_lifecycle_commands_emit_envelopes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "mft.duckdb"
    main(["init-db", "--database", str(db_path)])
    capsys.readouterr()

    _patch_research_api(monkeypatch)

    exit_code = main(
        [
            "create-research-project",
            "research_project:example",
            "--name",
            "example-project",
            "--description",
            "example",
            "--dataset-snapshot-id",
            "dataset_snapshot:example",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "create-research-project"
    assert payload["result"]["research_project_id"] == "research_project:example"

    exit_code = main(
        [
            "show-research-project",
            "research_project:example",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["result"]["research_project_id"] == "research_project:example"

    exit_code = main(
        [
            "run-parameter-research",
            "research_project:example",
            "--parameters-json",
            '{"lookback": 14}',
            "--parameter",
            "threshold=0.3",
            "--include-testing",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["result"]["parameter_count"] == 2
    assert payload["result"]["include_testing"] is True

    exit_code = main(
        ["list-research-runs", "--research-project-id", "research_project:example", "--database", str(db_path)]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["result"][0]["research_project_id"] == "research_project:example"

    exit_code = main(
        [
            "show-research-run",
            "research_run:1",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["result"]["research_run_id"] == "research_run:1"

    exit_code = main(
        [
            "compare-research-runs",
            "research_run:1",
            "research_run:2",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["result"]["research_run_ids"] == ["research_run:1", "research_run:2"]

    exit_code = main(
        [
            "export-research-pack",
            "research_project:example",
            "--output-dir",
            str(tmp_path / "export"),
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["result"]["output_dir"].endswith("export")

    exit_code = main(
        [
            "promote-strategy-candidate",
            "strategy_candidate:example",
            "--to",
            "testing",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["result"]["strategy_candidate_id"] == "strategy_candidate:example"


def test_research_lifecycle_workflow_config_runs_strategy_grids(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "mft.duckdb"
    main(["init-db", "--database", str(db_path)])
    capsys.readouterr()

    workflow_dir = tmp_path / "workflow"
    workflow_dir.mkdir()
    (workflow_dir / "grid-a.yaml").write_text(
        "{"
        '"strategy_family": "momentum_continuation",'
        '"asset_symbol": "NIFTY",'
        '"start_date": "2026-04-20",'
        '"end_date": "2026-05-14",'
        '"parameter_grid": {'
        '"lookback_bars": [3],'
        '"entry_threshold": [0.005],'
        '"exit_threshold": [0.0],'
        '"holding_bars": [2]'
        "}"
        "}",
        encoding="utf-8",
    )
    (workflow_dir / "run.yaml").write_text(
        "{"
        '"research_project_id": "research_project:example",'
        '"dataset_snapshot_id": "dataset_snapshot:example",'
        '"export_dir": "reports/research",'
        '"strategy_grids": ["grid-a.yaml"]'
        "}",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        cli_research,
        "run_research_batch",
        lambda repository, configs, output_dir: type(
            "Batch",
            (),
            {
                "output_dir": output_dir,
                "results": tuple(
                    type(
                        "Run",
                        (),
                        {
                            "config": config,
                            "config_hash": "abc123",
                            "artifact_manifest": type(
                                "Manifest",
                                (),
                                {
                                    "config_hash": "abc123",
                                    "manifest_path": str(output_dir / "manifest.json"),
                                },
                            )(),
                            "best_evaluation": None,
                        },
                    )()
                    for config in configs
                ),
            },
        )(),
    )

    exit_code = main(
        [
            "run-parameter-research",
            "--research-run-config",
            str(workflow_dir / "run.yaml"),
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["result"]["strategy_grid_count"] == 1
    assert payload["result"]["runs"][0]["strategy_family"] == "momentum_continuation"


def _patch_research_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        DataRepository,
        "create_research_project",
        lambda self, **kwargs: {
            "research_project_id": kwargs.get(
                "research_project_id", "research_project:auto"
            ),
            "name": kwargs["name"],
            "description": kwargs["description"],
            "dataset_snapshot_id": kwargs.get("dataset_snapshot_id"),
        },
        raising=False,
    )
    monkeypatch.setattr(
        DataRepository,
        "show_research_project",
        lambda self, **kwargs: {
            "research_project_id": kwargs["research_project_id"],
            "status": "draft",
        },
        raising=False,
    )
    monkeypatch.setattr(
        DataRepository,
        "run_parameter_research",
        lambda self, **kwargs: {
            "research_project_id": kwargs.get("research_project_id"),
            "parameter_count": len(kwargs["parameters"]),
            "include_testing": kwargs["include_testing"],
            "include_draft": kwargs["include_draft"],
        },
        raising=False,
    )
    monkeypatch.setattr(
        DataRepository,
        "list_research_runs",
        lambda self, **kwargs: [
            {
                "research_run_id": "research_run:1",
                "research_project_id": kwargs.get("research_project_id"),
            }
        ],
        raising=False,
    )
    monkeypatch.setattr(
        DataRepository,
        "show_research_run",
        lambda self, **kwargs: {"research_run_id": kwargs["research_run_id"]},
        raising=False,
    )
    monkeypatch.setattr(
        DataRepository,
        "compare_research_runs",
        lambda self, **kwargs: {
            "research_run_ids": list(kwargs["research_run_ids"]),
            "delta_count": len(kwargs["research_run_ids"]) - 1,
        },
        raising=False,
    )
    monkeypatch.setattr(
        DataRepository,
        "export_research_pack",
        lambda self, **kwargs: {
            "research_project_id": kwargs["research_project_id"],
            "output_dir": kwargs["output_dir"],
            "files": ["project.json", "run.json"],
        },
        raising=False,
    )
    monkeypatch.setattr(
        DataRepository,
        "promote_strategy_candidate",
        lambda self, **kwargs: {
            "strategy_candidate_id": kwargs["strategy_candidate_id"],
            "to_status": kwargs["to_status"],
            "force": kwargs["force"],
        },
        raising=False,
    )
