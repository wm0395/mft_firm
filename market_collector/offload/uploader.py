from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from typing import Literal

from market_collector.core.schemas import MarketCollectorConfig, OffloadConfig
from market_collector.offload.backend import OffloadBackend, select_backend
from market_collector.offload.ingester import OffloadObject


@dataclass(frozen=True)
class OffloadEvent:
    event_type: Literal["upload_started", "upload_completed", "upload_failed"]
    object_id: str
    message: str = ""


def run_offload(
    config: OffloadConfig | MarketCollectorConfig,
    objects: Sequence[OffloadObject],
    environ: Mapping[str, str] | None = None,
) -> tuple[OffloadEvent, ...]:
    backend: OffloadBackend | None = None
    events: list[OffloadEvent] = []
    try:
        backend = select_backend(config, environ)
        backend.ensure_schema()
        for blob in objects:
            events.append(OffloadEvent("upload_started", blob.object_id))
            try:
                backend.ingest_blob(blob)
                backend.register_catalog_object(blob)
            except Exception as error:
                events.append(OffloadEvent("upload_failed", blob.object_id, str(error)))
                raise
            events.append(OffloadEvent("upload_completed", blob.object_id))
    finally:
        if backend is not None:
            backend.close()
    return tuple(events)
