from __future__ import annotations

from project.common.models import Decision


def allocation_weight(decision: Decision, max_weight: float) -> float:
    if max_weight < 0:
        raise ValueError("max_weight cannot be negative")
    if decision.action != "approve":
        return 0.0
    return max_weight
