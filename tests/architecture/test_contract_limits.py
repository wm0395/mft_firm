from __future__ import annotations

import ast
from pathlib import Path


LIMITED_FILES = (
    Path("project/cli.py"),
    Path("project/cli_parsers.py"),
    Path("project/cli_support.py"),
    Path("project/cli_utils.py"),
    Path("project/cli_readonly.py"),
    Path("project/research_batch.py"),
    Path("project/research_validation.py"),
    Path("project/strategy_dossier.py"),
    Path("project/data/db.py"),
    Path("project/data/repository.py"),
    Path("project/data/yfinance_loader.py"),
    Path("project/data/market_collector_loader.py"),
)


def test_production_surface_contract_limits() -> None:
    violations = []
    for file in _limited_files():
        violations.extend(_file_violations(file))
    assert not violations, "\n".join(violations)


def _limited_files() -> tuple[Path, ...]:
    files = list(LIMITED_FILES)
    files.extend(sorted(Path("project/data").glob("repository_*.py")))
    return tuple(files)


def _file_violations(file: Path) -> list[str]:
    text = file.read_text(encoding="utf-8")
    tree = ast.parse(text)
    violations = []
    if len(text.splitlines()) > 400:
        violations.append(f"{file} exceeds the 400 line limit")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.end_lineno is not None:
            size = node.end_lineno - node.lineno + 1
            if size > 40:
                violations.append(f"{file}:{node.lineno} {node.name} exceeds 40 lines")
        elif isinstance(node, ast.ClassDef):
            methods = sum(isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) for child in node.body)
            if methods > 8:
                violations.append(f"{file}:{node.lineno} {node.name} exceeds 8 methods")
    return violations
