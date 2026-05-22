from __future__ import annotations

from pathlib import Path
from typing import Any

from project.cli.context import CLIContext
from project.cli.errors import CommandOutcome
from project.research.control_room import materialize_reports


def research_control_room(context: CLIContext) -> CommandOutcome:
    payloads = _materialize()
    payload = {
        "report": payloads["research_control_room"],
        "reports_written": _report_paths(),
    }
    return CommandOutcome(payload, status="ok")


def alpha101_status(context: CLIContext) -> CommandOutcome:
    payloads = _materialize()
    return CommandOutcome({"report": payloads["alpha101_status"]}, status="ok")


def data_source_status(context: CLIContext) -> CommandOutcome:
    payloads = _materialize()
    return CommandOutcome({"report": payloads["data_source_status"]}, status="ok")


def multi_asset_status(context: CLIContext) -> CommandOutcome:
    payloads = _materialize()
    return CommandOutcome({"report": payloads["multi_asset_status"]}, status="ok")


def _materialize() -> dict[str, dict[str, Any]]:
    return materialize_reports(_repo_root())


def _report_paths() -> tuple[str, ...]:
    return tuple(
        str(_repo_root() / "research" / "reports" / filename)
        for filename in (
            "research_control_room.md",
            "alpha101_status.md",
            "data_source_status.md",
            "multi_asset_status.md",
            "weekly_review.md",
        )
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
