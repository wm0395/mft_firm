from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from typing import Any


ACTIVE = "active"
COMPLETED = "completed"


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Subtask:
    id: int
    objective: str
    layer: str = ""
    files: tuple[str, ...] = ()
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    status: str = "pending"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Subtask":
        objective = str(data.get("objective") or data.get("desc") or "")
        return cls(
            id=int(data["id"]),
            objective=objective,
            layer=str(data.get("layer", "")),
            files=tuple(data.get("files", ())),
            inputs=tuple(data.get("inputs", ())),
            outputs=tuple(data.get("outputs", ())),
            status=str(data.get("status", "pending")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Task:
    id: str
    objective: str
    files: tuple[str, ...]
    constraints: tuple[str, ...]
    done_conditions: tuple[str, ...]
    queue_position: int | None = None
    status: str = ACTIVE
    route: str = "executor"
    recommended_provider: str = "codex"
    subtasks: tuple[Subtask, ...] = ()
    review_status: str = "pending"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    packet_history: tuple[dict[str, Any], ...] = ()
    run_history: tuple[dict[str, Any], ...] = ()
    review_history: tuple[dict[str, Any], ...] = ()
    check_history: tuple[dict[str, Any], ...] = ()
    completion_history: tuple[dict[str, Any], ...] = ()
    memory_refs: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        objective = str(data.get("objective") or data.get("description") or "")
        return cls(
            id=str(data["id"]),
            objective=objective,
            files=tuple(data.get("files", ())),
            constraints=tuple(data.get("constraints", ())),
            done_conditions=tuple(data.get("done_conditions", ())),
            queue_position=_queue_position(data.get("queue_position")),
            status=str(data.get("status", ACTIVE)),
            route=str(data.get("route", "executor")),
            recommended_provider=str(data.get("recommended_provider", "codex")),
            subtasks=tuple(Subtask.from_dict(item) for item in data.get("subtasks", ())),
            review_status=str(data.get("review_status", "pending")),
            created_at=str(data.get("created_at", utc_now())),
            updated_at=str(data.get("updated_at", utc_now())),
            packet_history=tuple(data.get("packet_history", ())),
            run_history=tuple(data.get("run_history", ())),
            review_history=tuple(data.get("review_history", ())),
            check_history=tuple(data.get("check_history", ())),
            completion_history=tuple(data.get("completion_history", ())),
            memory_refs=tuple(data.get("memory_refs", ())),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "subtasks": [subtask.to_dict() for subtask in self.subtasks],
        }

    def touch(self) -> "Task":
        return replace(self, updated_at=utc_now())

    def with_subtasks(self, subtasks: tuple[Subtask, ...]) -> "Task":
        return replace(self, subtasks=subtasks, updated_at=utc_now())

    def with_review_status(self, review_status: str) -> "Task":
        return replace(self, review_status=review_status, updated_at=utc_now())

    def with_packet(self, packet: dict[str, Any]) -> "Task":
        record = packet if "kind" in packet else {"kind": "packet", **packet}
        return replace(
            self,
            packet_history=(*self.packet_history, record),
            updated_at=utc_now(),
        )

    def with_launch(self, launch: dict[str, Any]) -> "Task":
        record = launch if "kind" in launch else {"kind": "launch", **launch}
        return replace(
            self,
            packet_history=(*self.packet_history, record),
            updated_at=utc_now(),
        )

    def with_run(self, run: dict[str, Any]) -> "Task":
        return replace(
            self,
            run_history=(*self.run_history, run),
            updated_at=utc_now(),
        )

    def with_review(self, review: dict[str, Any]) -> "Task":
        return replace(
            self,
            review_history=(*self.review_history, review),
            updated_at=utc_now(),
        )

    def with_checks(self, checks: dict[str, Any]) -> "Task":
        return replace(
            self,
            check_history=(*self.check_history, checks),
            updated_at=utc_now(),
        )

    def with_completion_record(self, record: dict[str, Any]) -> "Task":
        return replace(
            self,
            completion_history=(*self.completion_history, record),
            updated_at=utc_now(),
        )

    def with_memory_ref(self, memory_ref: str) -> "Task":
        return replace(
            self,
            memory_refs=(*self.memory_refs, memory_ref),
            updated_at=utc_now(),
        )

    def complete(self) -> "Task":
        return replace(self, status=COMPLETED, updated_at=utc_now())


def _queue_position(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


@dataclass(frozen=True)
class PacketBlock:
    name: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "content": self.content}


@dataclass(frozen=True)
class ExecutionPacket:
    task_id: str
    provider: str
    role: str
    budget: int
    prompt: str
    prompt_blocks: tuple[PacketBlock, ...]
    retrieved_context: tuple[str, ...]
    token_estimate: int
    command_hint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "provider": self.provider,
            "role": self.role,
            "budget": self.budget,
            "prompt": self.prompt,
            "prompt_blocks": [block.to_dict() for block in self.prompt_blocks],
            "retrieved_context": list(self.retrieved_context),
            "token_estimate": self.token_estimate,
            "command_hint": self.command_hint,
        }


@dataclass(frozen=True)
class ReviewPacket:
    task_id: str
    provider: str
    persona: str
    budget: int
    prompt: str
    prompt_blocks: tuple[PacketBlock, ...]
    retrieved_context: tuple[str, ...]
    token_estimate: int
    command_hint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "provider": self.provider,
            "persona": self.persona,
            "budget": self.budget,
            "prompt": self.prompt,
            "prompt_blocks": [block.to_dict() for block in self.prompt_blocks],
            "retrieved_context": list(self.retrieved_context),
            "token_estimate": self.token_estimate,
            "command_hint": self.command_hint,
        }


@dataclass(frozen=True)
class MemoryEntry:
    kind: str
    title: str
    body: str
    tags: tuple[str, ...]
    source_task_id: str
    ref: str = ""
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IndexEntry:
    path: str
    sha256: str
    symbols: tuple[str, ...]
    summary: str
    tags: tuple[str, ...]
    mtime: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TokenLedgerEntry:
    kind: str
    source: str
    provider: str
    content_hash: str
    tokenizer: str
    token_count: int
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
