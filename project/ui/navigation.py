from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageDefinition:
    title: str
    description: str


PAGES = (
    PageDefinition("Mission Control", "See system health and pick the next action."),
    PageDefinition("Data", "Check freshness and create reproducible snapshots."),
    PageDefinition("Research", "Launch and inspect research runs."),
    PageDefinition("Hypotheses", "Review lifecycle state and readiness blockers."),
    PageDefinition("Trade Ideas", "Decide on the open trade queue."),
    PageDefinition("Positions", "Inspect open and closed positions."),
    PageDefinition("Explainability", "Trace signals from evaluation to decision."),
    PageDefinition("Reports", "Review backtests, performance, and rejections."),
)


def page_titles() -> tuple[str, ...]:
    return tuple(page.title for page in PAGES)


def page_definition(title: str) -> PageDefinition:
    for page in PAGES:
        if page.title == title:
            return page
    return PAGES[0]
