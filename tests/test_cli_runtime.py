from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from project.cli import main
from project.common.models import TradeIdea
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository


def _run_help(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *command],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def test_project_main_script_help() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = _run_help(["project/main.py", "--help"], repo_root)

    assert result.returncode == 0
    assert "usage: mft" in result.stdout.lower()
    assert "commands:" in result.stdout.lower()
    assert "status" in result.stdout


def test_project_main_module_help() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = _run_help(["-m", "project.cli", "--help"], repo_root)

    assert result.returncode == 0
    assert "usage: mft" in result.stdout.lower()
    assert "setup" in result.stdout


def test_read_only_command_skips_schema_bootstrap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    repository.persist_trade_idea(
        TradeIdea(
            trade_id="trade:1",
            asset_id=asset.asset_id,
            hypothesis_id="hypothesis:test",
            version=1,
            direction="long",
            confidence=1.0,
            signals_snapshot={},
        )
    )
    repository.close()

    def fail_initialize_schema(self) -> None:
        raise AssertionError("read-only command must not bootstrap schema")

    monkeypatch.setattr(DuckDBAccess, "initialize_schema", fail_initialize_schema)
    exit_code = main(["show-trade-idea", "trade:1", "--database", str(db_path)])
    capsys.readouterr()

    assert exit_code == 0


def test_init_db_bootstraps_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "mft.duckdb"

    exit_code = main(["init-db", "--database", str(db_path)])

    assert exit_code == 0
    db = DuckDBAccess(db_path)
    try:
        assert {row[0] for row in db.fetch_all("show tables")} >= {
            "assets",
            "raw_data",
            "raw_market_data",
        }
    finally:
        db.close()
