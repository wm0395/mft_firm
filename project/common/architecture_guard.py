from __future__ import annotations


FORBIDDEN_IMPORTS = {
    "project.data": [
        "project.signals",
        "project.hypotheses",
        "project.trade_engine",
        "project.decision",
        "project.portfolio",
    ],
    "project.signals": [
        "project.hypotheses",
        "project.trade_engine",
        "project.decision",
        "project.portfolio",
    ],
    "project.hypotheses": [
        "project.data",
        "project.trade_engine",
        "project.decision",
        "project.portfolio",
    ],
    "project.trade_engine": [
        "project.data",
        "project.signals",
        "project.decision",
        "project.portfolio",
    ],
    "project.decision": [
        "project.data",
        "project.signals",
        "project.hypotheses",
        "project.portfolio",
    ],
    "project.portfolio": [
        "project.data",
        "project.signals",
        "project.hypotheses",
        "project.trade_engine",
    ],
}


def validate_import(module: str, imported: str) -> None:
    forbidden = FORBIDDEN_IMPORTS.get(module, [])
    if imported in forbidden:
        raise RuntimeError(f"Architecture violation: {module} → {imported}")
