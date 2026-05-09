from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class LineageNode:
    node_id: str
    name: str
    type: str  # e.g., "raw_data", "transformation", "signal"
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)
    dependencies: tuple[str, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class SignalLineage:
    signal_id: str
    lineage_path: tuple[LineageNode, ...]
    final_value: float
