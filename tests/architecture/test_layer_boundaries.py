from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path("project")
LAYER_ORDER = (
    "data",
    "signals",
    "hypotheses",
    "trade_engine",
    "decision",
    "portfolio",
)
FORBIDDEN_IMPORTS = {
    "hypotheses": ("project.data",),
    "signals": ("project.hypotheses", "project.trade_engine", "project.decision", "project.portfolio"),
    "data": (
        "project.signals",
        "project.hypotheses",
        "project.trade_engine",
        "project.decision",
        "project.portfolio",
    ),
}


def test_required_architecture_layers_exist() -> None:
    for layer in (*LAYER_ORDER, "common"):
        path = PROJECT_ROOT / layer
        assert path.exists(), f"Missing architecture layer: {path}"
        assert path.is_dir(), f"Architecture layer is not a directory: {path}"


def test_no_hypothesis_access_to_data() -> None:
    for file in (PROJECT_ROOT / "hypotheses").rglob("*.py"):
        content = file.read_text(encoding="utf-8")
        assert "project.data" not in content, f"{file} illegally imports data layer"


def test_no_forbidden_layer_imports() -> None:
    violations = []
    for layer, forbidden_imports in FORBIDDEN_IMPORTS.items():
        for file in (PROJECT_ROOT / layer).rglob("*.py"):
            imports = _imports(file)
            for forbidden_import in forbidden_imports:
                if any(imported == forbidden_import or imported.startswith(f"{forbidden_import}.") for imported in imports):
                    violations.append(f"{file} illegally imports {forbidden_import}")

    assert not violations, "\n".join(violations)


def test_no_cross_layer_dependency() -> None:
    for later_index, layer in enumerate(LAYER_ORDER):
        for earlier_layer in LAYER_ORDER[:later_index]:
            if _is_allowed_dependency(layer, earlier_layer):
                continue
            assert not depends_on(layer, earlier_layer), f"{layer} illegally depends on {earlier_layer}"


def depends_on(layer: str, dependency: str) -> bool:
    dependency_package = _package_name(dependency)
    for file in (PROJECT_ROOT / layer).rglob("*.py"):
        imports = _imports(file)
        if any(imported == dependency_package or imported.startswith(f"{dependency_package}.") for imported in imports):
            return True
    return False


def _imports(file: Path) -> set[str]:
    tree = ast.parse(file.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def _is_allowed_dependency(layer: str, dependency: str) -> bool:
    return {
        "signals": {"data"},
        "hypotheses": {"signals"},
        "trade_engine": {"hypotheses"},
        "decision": {"trade_engine"},
        "portfolio": {"decision"},
    }.get(layer, set()) == {dependency}


def _package_name(layer: str) -> str:
    return f"project.{layer}"
