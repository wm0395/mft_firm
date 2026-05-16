"""Offload backends and uploader entry points."""

from market_collector.offload.backend import OffloadError, select_backend
from market_collector.offload.duckdb_backend import DuckDBOffloadBackend
from market_collector.offload.ingester import OffloadObject, OhlcvRow
from market_collector.offload.postgres_backend import PostgresOffloadBackend
from market_collector.offload.uploader import OffloadEvent, run_offload

__all__ = [
    "DuckDBOffloadBackend",
    "OffloadError",
    "OffloadEvent",
    "OffloadObject",
    "OhlcvRow",
    "PostgresOffloadBackend",
    "run_offload",
    "select_backend",
]
