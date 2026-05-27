from __future__ import annotations

import ast
from pathlib import Path


EXCLUDED_FILES = {
    Path("project/cli/formatting.py"),
    Path("project/cli/commands/data_sources.py"),
    Path("project/cli/commands/hypothesis.py"),
    Path("project/cli/commands/research.py"),
    Path("project/cli/commands/status.py"),
}


def test_cli_surface_contract_limits() -> None:
    violations = []
    for file in _cli_surface_files():
        violations.extend(_file_violations(file))
    assert not violations, "\n".join(violations)


def _cli_surface_files() -> tuple[Path, ...]:
    files = {
        *Path("project/cli").glob("*.py"),
        *Path("project/cli").rglob("*.py"),
    }
    return tuple(
        sorted(
            path
            for path in files
            if "__pycache__" not in path.parts and path not in EXCLUDED_FILES
        )
    )


def _file_violations(file: Path) -> list[str]:
    text = file.read_text(encoding="utf-8")
    tree = ast.parse(text)
    violations = []
    if len(text.splitlines()) > 400:
        violations.append(f"{file} exceeds the 400 line limit")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.end_lineno is None:
                continue
            size = node.end_lineno - node.lineno + 1
            if size > 40:
                violations.append(f"{file}:{node.lineno} {node.name} exceeds 40 lines")
    return violations
