from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageDefinition:
    title: str
    description: str


PAGES = (
    PageDefinition("Mission Control", "System health, warnings, and workflow handoff."),
    PageDefinition("Data", "Dataset snapshots, data quality, and asset coverage."),
    PageDefinition("Research", "Launch research runs and review strategy dossiers."),
    PageDefinition("Hypotheses", "Browse lifecycle states and hypothesis readiness."),
    PageDefinition("Trade Ideas", "Review, approve, and track trade ideas."),
    PageDefinition("Positions", "Monitor open positions and realized performance."),
    PageDefinition("Charts", "Inspect locally rendered market charts."),
    PageDefinition("Trading", "Review trade ideas, positions, and reports."),
    PageDefinition("Explainability", "Trace signals into decisions and validations."),
    PageDefinition("Reports", "Backtests, performance, and canonical dossiers."),
)


def page_titles() -> tuple[str, ...]:
    return tuple(page.title for page in PAGES)


def page_definition(title: str) -> PageDefinition:
    for page in PAGES:
        if page.title == title:
            return page
    return PAGES[0]
