from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType

import pytest

from project.cli import main
from project.data.db import DuckDBAccess
from project.data.market_server_loader import (
    MARKET_SERVER_RELATION,
    _build_query,
    _normalize_symbols,
    sync_market_data,
)
from project.data.repository import DataRepository


@dataclass
class FakeResult:
    rows: list[tuple[object, ...]]

    def fetchall(self) -> list[tuple[object, ...]]:
        return list(self.rows)

    def fetchone(self) -> tuple[object, ...] | None:
        return self.rows[0] if self.rows else None


class FakeMarketServerConnection:
    def __init__(
        self, rows: list[tuple[object, ...]], relation_exists: bool = True
    ) -> None:
        self.rows = rows
        self.relation_exists = relation_exists
        self.closed = False
        self.statements: list[tuple[str, tuple[object, ...]]] = []

    def execute(
        self, statement: str, params: tuple[object, ...] | list[object] | None = None
    ) -> FakeResult:
        normalized = " ".join(statement.lower().split())
        parameters = tuple(params or ())
        self.statements.append((normalized, parameters))
        if "information_schema.tables" in normalized:
            return FakeResult([(1,)] if self.relation_exists else [])
        if f"from {MARKET_SERVER_RELATION}" in normalized:
            return FakeResult(list(self.rows))
        raise AssertionError(f"unexpected sql: {statement}")

    def close(self) -> None:
        self.closed = True


def test_sync_market_data_requires_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _repository(tmp_path)
    monkeypatch.delenv("MARKET_DB_URL", raising=False)

    with pytest.raises(RuntimeError, match="MARKET_DB_URL"):
        sync_market_data(repository, ("AAPL",))

    repository.close()


def test_build_query_normalizes_symbols() -> None:
    symbols = _normalize_symbols(("aapl", "AAPL", "msft"))
    statement, parameters = _build_query(symbols, "1d")

    assert symbols == ("AAPL", "MSFT")
    assert "from market_raw.ohlcv_deduplicated" in statement
    assert "upper(symbol) in (%s, %s)" in statement
    assert parameters == ("1d", "AAPL", "MSFT")


def test_sync_market_data_reports_missing_relation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path)
    connection = FakeMarketServerConnection([], relation_exists=False)
    monkeypatch.setenv("MARKET_DB_URL", "postgresql://example")
    monkeypatch.setattr(
        "project.data.market_server_loader._connect_market_server",
        lambda env: connection,
    )

    with pytest.raises(RuntimeError, match="market_raw\\.ohlcv_deduplicated"):
        sync_market_data(repository, ("AAPL",))

    assert connection.closed
    repository.close()


def test_sync_market_data_reports_connection_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path)
    fake_psycopg = ModuleType("psycopg")

    def connect(_: str) -> None:
        raise OSError("boom")

    fake_psycopg.connect = connect  # type: ignore[attr-defined]
    monkeypatch.setenv("MARKET_DB_URL", "postgresql://example")
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)

    with pytest.raises(RuntimeError, match="failed to connect to Postgres"):
        sync_market_data(repository, ("AAPL",))

    repository.close()


def test_sync_market_data_reports_no_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path)
    connection = FakeMarketServerConnection([])
    monkeypatch.setenv("MARKET_DB_URL", "postgresql://example")
    monkeypatch.setattr(
        "project.data.market_server_loader._connect_market_server",
        lambda env: connection,
    )

    with pytest.raises(ValueError, match="returned no rows"):
        sync_market_data(repository, ("AAPL",), resolution="1d")

    assert connection.closed
    repository.close()


def test_sync_market_data_rejects_invalid_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path)
    rows = [
        (
            "AAPL",
            "NASDAQ",
            datetime(2026, 5, 1, 5, 30, 15, tzinfo=timezone(timedelta(hours=-5))),
            100.0,
            99.0,
            98.0,
            100.0,
            1000.0,
            "yahoo",
            "1d",
        )
    ]
    connection = FakeMarketServerConnection(rows)
    monkeypatch.setenv("MARKET_DB_URL", "postgresql://example")
    monkeypatch.setattr(
        "project.data.market_server_loader._connect_market_server",
        lambda env: connection,
    )

    with pytest.raises(ValueError, match="validation failed"):
        sync_market_data(repository, ("AAPL",))

    assert connection.closed
    assert repository.list_assets() == ()
    assert repository.read_raw_values("asset:AAPL", "price") == ()
    repository.close()


def test_sync_market_data_command_ingests_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"
    rows = [
        (
            "AAPL",
            "NASDAQ",
            datetime(2026, 5, 1, 5, 30, 15, tzinfo=timezone(timedelta(hours=-5))),
            100.0,
            105.0,
            99.0,
            104.0,
            1000.0,
            "yahoo",
            "1d",
        ),
        (
            "AAPL",
            "NASDAQ",
            datetime(2026, 5, 2, 8, 0, tzinfo=timezone(timedelta(hours=2))),
            106.0,
            109.0,
            104.0,
            108.0,
            1100.0,
            "yahoo",
            "1d",
        ),
        (
            "MSFT",
            "NASDAQ",
            datetime(2026, 5, 1, 0, 15, tzinfo=UTC),
            200.0,
            202.0,
            199.0,
            201.0,
            1500.0,
            "yahoo",
            "1d",
        ),
    ]
    connection = FakeMarketServerConnection(rows)
    monkeypatch.setenv("MARKET_DB_URL", "postgresql://example")
    monkeypatch.setattr(
        "project.data.market_server_loader._connect_market_server",
        lambda env: connection,
    )

    exit_code = main(["init-db", "--database", str(db_path)])
    capsys.readouterr()
    assert exit_code == 0

    exit_code = main(
        [
            "sync-market-data",
            "--symbol",
            "aapl",
            "--symbol",
            "msft",
            "--resolution",
            "1d",
            "--database",
            str(db_path),
        ]
    )
    payload = capsys.readouterr().out
    repository = DataRepository(DuckDBAccess(db_path))
    try:
        assert exit_code == 0
        result = json.loads(payload)
        assert result["status"] == "ok"
        assert result["command"] == "sync-market-data"
        assert result["result"]["source"] == "postgres"
        assert result["result"]["source_relation"] == MARKET_SERVER_RELATION
        assert result["result"]["symbols"] == ["AAPL", "MSFT"]
        assert result["result"]["rows_loaded"] == {"AAPL": 2, "MSFT": 1}
        assert result["result"]["resolution"] == "1d"
        assert (
            result["result"]["latest_timestamps"]["AAPL"] == "2026-05-02T06:00:00+00:00"
        )
        assert len(repository.list_assets()) == 2
        market_rows = repository.get_market_data("AAPL", None, None)
        assert len(market_rows) == 2
        assert market_rows[0][0] == datetime(2026, 5, 1, 10, 30, 15)
        assert market_rows[-1][0] == datetime(2026, 5, 2, 6, 0)
        assert len(repository.get_market_data("MSFT", None, None)) == 1
        assert (
            repository.read_raw_values("asset:AAPL", "price")[-1].timestamp
            == "2026-05-02T06:00:00+00:00"
        )
        assert repository.read_raw_values("asset:AAPL", "price")[-1].value == {
            "close": 108.0
        }
        assert connection.closed
    finally:
        repository.close()


def _repository(tmp_path: Path) -> DataRepository:
    repository = DataRepository(DuckDBAccess(tmp_path / "mft.duckdb"))
    repository.initialize()
    return repository
