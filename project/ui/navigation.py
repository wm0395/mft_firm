from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageDefinition:
    title: str
    description: str


PAGES = (
    PageDefinition("Mission Control", "System health and the next recommended action."),
    PageDefinition("Data", "Data readiness, freshness, and dataset snapshots."),
    PageDefinition("Research", "Research projects, runs, and strategy candidates."),
    PageDefinition("Hypotheses", "Lifecycle board and hypothesis readiness."),
    PageDefinition("Trade Ideas", "Review queue for human decision making."),
    PageDefinition("Explainability", "Signal lineage and validation trace."),
    PageDefinition("Reports", "Weekly review, backtests, and performance."),
)


def page_titles() -> tuple[str, ...]:
    return tuple(page.title for page in PAGES)


def page_definition(title: str) -> PageDefinition:
    for page in PAGES:
        if page.title == title:
            return page
    return PAGES[0]
