from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol, runtime_checkable

from market_collector.core.schemas import MarketCollectorConfig, OffloadConfig
from market_collector.offload.ingester import OffloadObject


class OffloadError(RuntimeError):
    pass


@runtime_checkable
class OffloadBackend(Protocol):
    def ensure_schema(self) -> None:
        ...

    def ingest_blob(self, blob: OffloadObject) -> int:
        ...

    def register_catalog_object(self, blob: OffloadObject) -> None:
        ...

    def close(self) -> None:
        ...


def open_duckdb_backend(database_path: Path) -> OffloadBackend:
    from market_collector.offload.duckdb_backend import open_duckdb_backend as _open

    return _open(database_path)


def open_postgres_backend(database_url: str) -> OffloadBackend:
    from market_collector.offload.postgres_backend import open_postgres_backend as _open

    return _open(database_url)


def select_backend(
    config: OffloadConfig | MarketCollectorConfig,
    environ: Mapping[str, str] | None = None,
) -> OffloadBackend:
    offload = config.offload if isinstance(config, MarketCollectorConfig) else config
    env = os.environ if environ is None else environ
    if offload.backend == "duckdb":
        if not offload.db_path:
            raise OffloadError("db_path is required when backend='duckdb'")
        return open_duckdb_backend(Path(offload.db_path).expanduser())
    if offload.backend == "postgres":
        database_url = env.get(offload.database_url_env)
        if not database_url:
            raise OffloadError(
                f"environment variable {offload.database_url_env} is required when backend='postgres'"
            )
        return open_postgres_backend(database_url)
    raise OffloadError(f"unsupported offload backend: {offload.backend}")
