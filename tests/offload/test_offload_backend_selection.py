from __future__ import annotations

from pathlib import Path

import pytest

from market_collector.core.schemas import MarketCollectorConfig, OffloadConfig
from market_collector.offload.backend import OffloadError, select_backend
from market_collector.offload.duckdb_backend import DuckDBOffloadBackend


def test_default_backend_remains_duckdb(tmp_path: Path) -> None:
    config = MarketCollectorConfig(offload=OffloadConfig(db_path=str(tmp_path / "market.duckdb")))

    backend = select_backend(config.offload)

    assert isinstance(backend, DuckDBOffloadBackend)
    backend.close()


def test_postgres_backend_requires_env_var() -> None:
    config = OffloadConfig(backend="postgres")

    with pytest.raises(OffloadError, match="MARKET_DB_URL"):
        select_backend(config, environ={})
