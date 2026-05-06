from __future__ import annotations


COMPLEXITY_MARKERS = (
    "architecture",
    "multi",
    "multiple",
    "refactor",
    "database",
    "schema",
    "pipeline",
    "system",
    "integrate",
)


def route(description: str) -> str:
    words = description.lower().split()
    if len(words) > 18:
        return "planner"
    if any(marker in description.lower() for marker in COMPLEXITY_MARKERS):
        return "planner"
    return "executor"
