from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CliError(Exception):
    message: str
    why: str | None = None
    next_action: str | None = None
    command: str | None = None
    exit_code: int = 1

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class CommandOutcome:
    result: object | None = None
    status: str = "ok"
    exit_code: int = 0
    warnings: tuple[str, ...] = ()
