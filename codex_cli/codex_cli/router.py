from __future__ import annotations


ARCHITECTURE_MARKERS = ("architecture", "refactor", "layer", "contract", "drift")
BULK_MARKERS = ("generate tests", "bulk", "mass", "sweep", "repetitive")
REVIEW_MARKERS = ("audit", "review", "debug", "investigate", "design")


def route(objective: str) -> str:
    text = objective.lower()
    if len(text.split()) > 18 or _contains(text, ARCHITECTURE_MARKERS):
        return "planner"
    return "executor"


def recommend_provider(objective: str, route_name: str) -> str:
    text = objective.lower()
    if _contains(text, BULK_MARKERS) or _contains(text, REVIEW_MARKERS) or route_name in {"planner", "executor"}:
        return "opencode"
    return "codex"


def _contains(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)
