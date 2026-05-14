from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from project.data.db import DuckDBAccess


class DataRepositoryBase:
    _db: DuckDBAccess

    def __init__(self, db: DuckDBAccess) -> None:
        self._db = db

    def initialize(self) -> None:
        self._db.initialize_schema()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self._db.transaction():
            yield

    def close(self) -> None:
        self._db.close()
