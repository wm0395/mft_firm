from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StatusCardView:
    label: str
    value: str
    state: str
    detail: str


@dataclass(frozen=True)
class WorkflowStepView:
    label: str
    state: str
    detail: str

