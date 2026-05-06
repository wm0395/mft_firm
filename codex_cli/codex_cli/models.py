from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


ACTIVE = "active"
COMPLETED = "completed"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Subtask:
    id: int
    desc: str
    layer: str = ""
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    status: str = "pending"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Subtask":
        return cls(
            id=int(data["id"]),
            desc=str(data["desc"]),
            layer=str(data.get("layer", "")),
            inputs=list(data.get("inputs", [])),
            outputs=list(data.get("outputs", [])),
            files=list(data.get("files", [])),
            status=str(data.get("status", "pending")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "desc": self.desc,
            "layer": self.layer,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "files": self.files,
            "status": self.status,
        }


@dataclass
class Task:
    id: str
    description: str
    status: str = ACTIVE
    subtasks: list[Subtask] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    route: str = "executor"
    review: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        return cls(
            id=str(data["id"]),
            description=str(data["description"]),
            status=str(data.get("status", ACTIVE)),
            subtasks=[Subtask.from_dict(item) for item in data.get("subtasks", [])],
            files=list(data.get("files", [])),
            created_at=str(data.get("created_at", utc_now())),
            updated_at=str(data.get("updated_at", utc_now())),
            route=str(data.get("route", "executor")),
            review=data.get("review"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "subtasks": [subtask.to_dict() for subtask in self.subtasks],
            "files": self.files,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "route": self.route,
            "review": self.review,
        }

    def touch(self) -> None:
        self.updated_at = utc_now()
