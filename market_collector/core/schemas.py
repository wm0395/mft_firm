from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


OffloadBackendName = Literal["duckdb", "postgres"]


@dataclass(frozen=True)
class OffloadConfig:
    backend: OffloadBackendName = "duckdb"
    db_path: str | None = None
    database_url_env: str = "MARKET_DB_URL"
    retry_interval_sec: int = 300
    max_retry_attempts: int = 10
    batch_size: int = 1_000
    auto_cleanup_after_offload: bool = False


@dataclass(frozen=True)
class MarketCollectorConfig:
    offload: OffloadConfig = field(default_factory=OffloadConfig)
