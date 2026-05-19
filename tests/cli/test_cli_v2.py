from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from click.testing import CliRunner

from project.cli import app
from project.common.models import Asset
from project.data.db import DuckDBAccess
from project.data.ingestion import build_raw_price_point
from project.data.repository import DataRepository


def test_root_command_prints_guidance(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, [], catch_exceptions=False)

    assert result.exit_code == 0
    assert "MFT Investment System" in result.output
    assert "mft status" in result.output
    assert "mft next" in result.output


def test_status_next_and_json_mode(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    _seed_market_data(repository, asset)
    repository.close()

    status = CliRunner().invoke(
        app,
        ["status", "--database", str(tmp_path / "mft.duckdb")],
        catch_exceptions=False,
    )
    assert status.exit_code == 0
    assert "MFT System Status" in status.output
    assert "Snapshots" in status.output
    assert "mft data snapshot create AAPL" in status.output

    next_result = CliRunner().invoke(
        app,
        ["next", "--database", str(tmp_path / "mft.duckdb")],
        catch_exceptions=False,
    )
    assert next_result.exit_code == 0
    assert "Create dataset snapshot" in next_result.output
    assert "mft data snapshot create AAPL" in next_result.output

    json_result = CliRunner().invoke(
        app,
        ["status", "--json", "--database", str(tmp_path / "mft.duckdb")],
        catch_exceptions=False,
    )
    payload = json.loads(json_result.output)
    assert payload["command"] == "status"
    assert payload["status"] == "warn"
    assert payload["result"]["assets"] == 1
    assert payload["result"]["snapshots"] == 0


def test_data_quality_and_hypothesis_list(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    _seed_market_data(repository, asset)
    repository.close()

    quality = CliRunner().invoke(
        app,
        ["data", "quality", "AAPL", "--database", str(tmp_path / "mft.duckdb")],
        catch_exceptions=False,
    )
    assert quality.exit_code == 0
    assert "Data Quality: OK" in quality.output
    assert "mft data snapshot create AAPL" in quality.output

    hypotheses = CliRunner().invoke(
        app,
        ["hypothesis", "list", "--database", str(tmp_path / "mft.duckdb")],
        catch_exceptions=False,
    )
    assert hypotheses.exit_code == 0
    assert "hypothesis:rsi_mean_reversion" in hypotheses.output
    assert "Hypotheses" in hypotheses.output


def test_research_run_guides_when_snapshot_is_missing(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    _seed_market_data(repository, asset)
    repository.close()

    result = CliRunner().invoke(
        app,
        [
            "research",
            "run",
            "hypothesis:rsi_mean_reversion",
            "AAPL",
            "--snapshot",
            "latest",
            "--database",
            str(tmp_path / "mft.duckdb"),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert "No dataset snapshot found." in result.output
    assert "mft data snapshot create AAPL" in result.output


def _repository(tmp_path: Path) -> DataRepository:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    return repository


def _seed_market_data(repository: DataRepository, asset: Asset) -> None:
    base = datetime(2026, 4, 26, tzinfo=UTC)
    for index in range(20):
        timestamp = base + timedelta(days=index)
        close = 100.0 + float(index)
        repository.ingest_market_data(
            asset.symbol,
            timestamp,
            close,
            close + 1.0,
            close - 1.0,
            close,
            1000.0 + float(index),
        )
        repository.ingest_raw(
            build_raw_price_point(asset.asset_id, timestamp.isoformat(), close, "csv:fixture")
        )
