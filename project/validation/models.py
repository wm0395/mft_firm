from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    reasons: list[str]
    metrics: dict[str, Any]
    validated_at: str  # ISO 8601 string

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")