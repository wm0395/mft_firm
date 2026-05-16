from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

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
    ingest_object_insert_sql,
    ingest_object_values,
    ohlcv_insert_sql,
    ohlcv_values,
    read_ohlcv_rows,
)


REQUIRED_TABLES = ("collector_nodes", "ingest_objects", "catalog_objects", "ohlcv")
SCHEMA_NAME = "market_raw"


@dataclass
class PostgresOffloadBackend:
    connection: Any
    database_url: str

    @classmethod
    def open(cls, database_url: str) -> "PostgresOffloadBackend":
        try:
            psycopg = importlib.import_module("psycopg")
        except ImportError as error:
            raise OffloadError("psycopg[binary] is required for postgres offload") from error
        return cls(psycopg.connect(database_url), database_url)

    def ensure_schema(self) -> None:
        missing = self._missing_schema_objects()
        if missing:
            raise OffloadError(f"missing market_raw schema/tables: {', '.join(missing)}")

    def ingest_blob(self, blob: OffloadObject) -> int:
        self.ensure_schema()
        rows = self._read_rows(blob)
        try:
            self.connection.execute(collector_node_insert_sql("%s"), collector_node_values(blob))
            self.connection.execute(ingest_object_insert_sql("%s"), ingest_object_values(blob, len(rows)))
            for row in rows:
                self.connection.execute(ohlcv_insert_sql("%s"), ohlcv_values(blob, row))
        except Exception as error:
            raise OffloadError(f"failed to offload blob {blob.object_id}: {error}") from error
        commit_if_supported(self.connection)
        return len(rows)

    def register_catalog_object(self, blob: OffloadObject) -> None:
        self.ensure_schema()
        try:
            self.connection.execute(catalog_object_insert_sql("%s"), catalog_object_values(blob))
        except Exception as error:
            raise OffloadError(f"failed to register catalog object {blob.object_id}: {error}") from error
        commit_if_supported(self.connection)

    def close(self) -> None:
        close_if_supported(self.connection)

    def _read_rows(self, blob: OffloadObject) -> tuple[OhlcvRow, ...]:
        try:
            return read_ohlcv_rows(blob.blob_path)
        except Exception as error:
            raise OffloadError(f"failed to read parquet blob {blob.blob_path}: {error}") from error

    def _missing_schema_objects(self) -> tuple[str, ...]:
        if not self._schema_exists():
            return (f"{SCHEMA_NAME} schema", *self._required_table_names())
        missing: list[str] = []
        for table_name in REQUIRED_TABLES:
            if self._table_exists(table_name):
                continue
            missing.append(f"{SCHEMA_NAME}.{table_name}")
        return tuple(missing)

    def _schema_exists(self) -> bool:
        row = self.connection.execute(
            "select 1 from information_schema.schemata where schema_name = %s",
            (SCHEMA_NAME,),
        ).fetchone()
        return row is not None

    def _table_exists(self, table_name: str) -> bool:
        row = self.connection.execute(
            """
            select 1
            from information_schema.tables
            where table_schema = %s and table_name = %s
            """,
            (SCHEMA_NAME, table_name),
        ).fetchone()
        return row is not None

    def _required_table_names(self) -> tuple[str, ...]:
        return tuple(f"{SCHEMA_NAME}.{table}" for table in REQUIRED_TABLES)


def open_postgres_backend(database_url: str) -> PostgresOffloadBackend:
    return PostgresOffloadBackend.open(database_url)
