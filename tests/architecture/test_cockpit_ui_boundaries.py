from __future__ import annotations

import ast
from pathlib import Path


PAGE_FILES = (
    Path("project/ui/pages/mission_control.py"),
    Path("project/ui/pages/data.py"),
    Path("project/ui/pages/research.py"),
)
FORBIDDEN_PREFIXES = (
    "project.data",
    "project.signals",
    "project.hypotheses",
    "project.trade_engine",
    "project.decision",
    "project.portfolio",
)


def test_cockpit_pages_avoid_lower_layer_imports() -> None:
    violations = []
    for file in PAGE_FILES:
        for imported in _project_imports(file):
            if imported.startswith(FORBIDDEN_PREFIXES):
                violations.append(f"{file} imports {imported}")
    assert not violations, "\n".join(violations)


def _project_imports(file: Path) -> tuple[str, ...]:
    tree = ast.parse(file.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return tuple(sorted(name for name in imported if name.startswith("project.")))
