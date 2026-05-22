from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from project.cli import main
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository


def _run_cli_and_load_payload(
    capsys: pytest.CaptureFixture[str], args: list[str]
) -> tuple[int, dict[str, Any]]:
    exit_code = main(args)
    payload = json.loads(capsys.readouterr().out)
    return exit_code, payload


def _assert_hypothesis_registry_initial_state(
    db_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code, payload = _run_cli_and_load_payload(
        capsys, ["list-hypotheses", "--database", str(db_path)]
    )
    assert exit_code == 0
    assert payload["command"] == "list-hypotheses"
    assert any(
        item["hypothesis_id"] == "hypothesis:rsi_mean_reversion"
        for item in payload["result"]
    )

    exit_code, payload = _run_cli_and_load_payload(
        capsys,
        ["show-hypothesis", "hypothesis:rsi_mean_reversion", "--database", str(db_path)],
    )
    assert exit_code == 0
    assert payload["command"] == "show-hypothesis"
    assert payload["result"]["hypothesis_id"] == "hypothesis:rsi_mean_reversion"
    assert payload["result"]["status"] == "active"

    exit_code, payload = _run_cli_and_load_payload(
        capsys,
        [
            "validate-hypothesis",
            "hypothesis:rsi_mean_reversion",
            "--database",
            str(db_path),
        ],
    )
    assert exit_code == 0
    assert payload["command"] == "validate-hypothesis"
    assert payload["result"]["valid"] is True


def _assert_hypothesis_registry_state_changes(
    db_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code, payload = _run_cli_and_load_payload(
        capsys,
        [
            "hypothesis-readiness",
            "hypothesis:rsi_mean_reversion",
            "--database",
            str(db_path),
        ],
    )
    assert exit_code == 0
    assert payload["command"] == "hypothesis-readiness"
    assert payload["status"] in {"warn", "ok"}
    assert payload["result"]["hypothesis_id"] == "hypothesis:rsi_mean_reversion"
    assert payload["result"]["readiness"] in {"ready", "not_ready"}
    assert payload["result"]["signal_registration_status"]

    exit_code, payload = _run_cli_and_load_payload(
        capsys,
        [
            "promote-hypothesis",
            "hypothesis:rsi_mean_reversion",
            "--to",
            "deprecated",
            "--database",
            str(db_path),
        ],
    )
    assert exit_code == 0
    assert payload["result"]["previous_status"] == "active"
    assert payload["result"]["new_status"] == "deprecated"

    exit_code, payload = _run_cli_and_load_payload(
        capsys, ["show-hypothesis", "hypothesis:rsi_mean_reversion", "--database", str(db_path)]
    )
    assert exit_code == 0
    assert payload["result"]["status"] == "deprecated"


def test_hypothesis_registry_cli_commands(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"

    exit_code = main(["init-db", "--database", str(db_path)])
    capsys.readouterr()
    assert exit_code == 0

    _assert_hypothesis_registry_initial_state(db_path, capsys)
    _assert_hypothesis_registry_state_changes(db_path, capsys)


def test_operator_commands_emit_envelopes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    repository.close()

    exit_code = main(["doctor", "--database", str(db_path)])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "doctor"
    assert payload["status"] in {"fail", "warn"}
    assert any(
        check["check"] == "schema_initialized" for check in payload["result"]["checks"]
    )

    exit_code = main(["workflow-status", "--database", str(db_path)])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "workflow-status"
    assert payload["result"]["next_recommended_command"] == "sync-market-data"

    exit_code = main(["next-steps", "--database", str(db_path)])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "next-steps"
    assert payload["result"]["steps"][0]["command"] == "init-db"
