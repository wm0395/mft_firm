from __future__ import annotations

from typing import Any

from project.cli.commands.status import build_next_payload, build_status_payload
from project.cli.context import CLIContext, open_repository
from project.cli.errors import CommandOutcome


def init(context: CLIContext) -> CommandOutcome:
    with open_repository(context.database, read_only=False) as repository:
        repository.initialize()
    return CommandOutcome(
        {"schema": "initialized", "database": str(context.database)},
        status="ok",
    )


def bootstrap(context: CLIContext) -> CommandOutcome:
    setup = init(context)
    status_payload = build_status_payload(context.database)
    next_payload = build_next_payload(context.database)
    payload: dict[str, Any] = {
        "setup_status": setup.status,
        "system_status": status_payload["status"],
        "next_action": next_payload["next_action"],
        "next_command": next_payload["next_command"],
    }
    return CommandOutcome(payload, status=str(status_payload["status"]))
