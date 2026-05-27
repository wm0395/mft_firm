from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path("project")
DUCKDB_IMPORT = ("project.data.db", "DuckDBAccess")
STREAMLIT_HELPER = Path("project/ui/_streamlit.py")
STREAMLIT_CACHE_NAMES = {"_streamlit", "_option_menu"}


def test_ui_and_cli_modules_do_not_import_duckdbaccess_directly() -> None:
    violations = []
    for file in _ui_and_cli_files():
        for imported in _direct_imports(file):
            if imported == DUCKDB_IMPORT:
                violations.append(f"{file} imports {imported[1]} from {imported[0]}")
    assert not violations, "\n".join(violations)


def test_streamlit_helper_has_no_module_level_cache_variables() -> None:
    violations = []
    tree = ast.parse(STREAMLIT_HELPER.read_text(encoding="utf-8"))
    for node in tree.body:
        for target in _module_level_targets(node):
            if target in STREAMLIT_CACHE_NAMES:
                violations.append(f"{STREAMLIT_HELPER} defines module-level cache {target}")
    assert not violations, "\n".join(violations)


def _ui_and_cli_files() -> tuple[Path, ...]:
    files = list(Path("project").glob("cli*.py"))
    files.extend(Path("project/cli").rglob("*.py"))
    files.extend(Path("project/ui").rglob("*.py"))
    return tuple(sorted(files))


def _direct_imports(file: Path) -> set[tuple[str, str]]:
    tree = ast.parse(file.read_text(encoding="utf-8"))
    imports: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imports.add((node.module, alias.name))
    return imports


def _module_level_targets(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Assign):
        return {
            target.id
            for target in node.targets
            if isinstance(target, ast.Name)
        }
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return {node.target.id}
    return set()
