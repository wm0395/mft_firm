from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from market_collector.offload.backend import OffloadError
from market_collector.offload.ingester import (
    OhlcvRow,
    OffloadObject,
    catalog_object_insert_sql,
    catalog_object_values,
    close_if_supported,
    collector_node_insert_sql,
    collector_node_values,
    commit_if_supported,
    ensure_duckdb_schema,
    ingest_object_insert_sql,
    ingest_object_values,
    ohlcv_insert_sql,
    ohlcv_values,
    read_ohlcv_rows,
)


@dataclass
class DuckDBOffloadBackend:
    connection: Any
    database_path: Path

    @classmethod
    def open(cls, database_path: Path) -> "DuckDBOffloadBackend":
        return cls(duckdb.connect(str(database_path)), database_path)

    def ensure_schema(self) -> None:
        ensure_duckdb_schema(self.connection)

    def ingest_blob(self, blob: OffloadObject) -> int:
        self.ensure_schema()
        rows = self._read_rows(blob)
        self.connection.execute(collector_node_insert_sql("?"), collector_node_values(blob))
        self.connection.execute(ingest_object_insert_sql("?"), ingest_object_values(blob, len(rows)))
        for row in rows:
            self.connection.execute(ohlcv_insert_sql("?"), ohlcv_values(blob, row))
        commit_if_supported(self.connection)
        return len(rows)

    def register_catalog_object(self, blob: OffloadObject) -> None:
        self.ensure_schema()
        self.connection.execute(catalog_object_insert_sql("?"), catalog_object_values(blob))
        commit_if_supported(self.connection)

    def close(self) -> None:
        close_if_supported(self.connection)

    def _read_rows(self, blob: OffloadObject) -> tuple[OhlcvRow, ...]:
        try:
            return read_ohlcv_rows(blob.blob_path)
        except Exception as error:
            raise OffloadError(f"failed to offload blob {blob.object_id}: {error}") from error


def open_duckdb_backend(database_path: Path) -> DuckDBOffloadBackend:
    return DuckDBOffloadBackend.open(database_path)
