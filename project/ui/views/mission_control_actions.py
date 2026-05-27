from __future__ import annotations

from typing import Final


DEFAULT_RECOMMENDED_ACTION: Final[tuple[str, str, str]] = (
    "Review trade ideas",
    "Trade review is the next human step.",
    "Review Trade Ideas",
)

ACTION_TEXT_BY_COMMAND: Final[dict[str, tuple[str, str, str]]] = {
    "init-db": (
        "Initialize the database",
        "The schema is not ready yet.",
        "Initialize Database",
    ),
    "sync-market-data": (
        "Sync market data",
        "Assets are missing market rows.",
        "Sync Market Data",
    ),
    "create-dataset-snapshot": (
        "Create a dataset snapshot",
        "Research needs a reproducible snapshot.",
        "Create Snapshot",
    ),
    "data-quality-report": (
        "Review data quality",
        "Inspect the latest data quality report.",
        "Review Data Quality",
    ),
    "run-strategy-research": (
        "Run research",
        "No research run exists yet.",
        "Run Research",
    ),
    "hypothesis-readiness": (
        "Review hypothesis readiness",
        "The workflow is ready for human review.",
        "Review Hypothesis",
    ),
}

DATA_COMMANDS: Final[frozenset[str]] = frozenset(
    {
        "init-db",
        "sync-market-data",
        "create-dataset-snapshot",
        "data-quality-report",
    }
)


def recommended_action_text(command: str) -> tuple[str, str, str]:
    return ACTION_TEXT_BY_COMMAND.get(command, DEFAULT_RECOMMENDED_ACTION)


def target_page(command: str) -> str:
    if command in DATA_COMMANDS:
        return "Data"
    if command == "hypothesis-readiness":
        return "Hypotheses"
    if command == "run-strategy-research":
        return "Research"
    return "Trade Ideas"
