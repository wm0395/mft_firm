from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from project.data.schema import SCHEMA_SQL


class DuckDBAccess:
    def __init__(
        self,
        database_path: str | Path = "project_mft.duckdb",
        read_only: bool = False,
    ) -> None:
        try:
            import duckdb
        except ImportError as error:
            raise RuntimeError("DuckDB is required for the data layer. Install duckdb in .env.") from error

        self._connection = duckdb.connect(str(database_path), read_only=read_only)

    def initialize_schema(self) -> None:
        for statement in SCHEMA_SQL:
            self._connection.execute(statement)

    def execute(self, statement: str, parameters: Iterable[Any] = ()) -> None:
        self._connection.execute(statement, list(parameters))

    def fetch_all(self, statement: str, parameters: Iterable[Any] = ()) -> list[tuple[Any, ...]]:
        return list(self._connection.execute(statement, list(parameters)).fetchall())

    @contextmanager
    def transaction(self) -> Iterator[None]:
        self._connection.execute("begin")
        try:
            yield
        except Exception:
            self._connection.execute("rollback")
            raise
        else:
            self._connection.execute("commit")

    def close(self) -> None:
        self._connection.close()
