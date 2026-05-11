from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from layer_linter.contract import Contract, ContractParseError, contract_from_yaml  # type: ignore[import-untyped]
from layer_linter.dependencies import DependencyGraph  # type: ignore[import-untyped]
from layer_linter.module import SafeFilenameModule  # type: ignore[import-untyped]

from .paths import ProjectPaths


MAX_RETRIES = 3
VENV_BIN = Path(sys.executable).parent
ARCHITECTURE_COMMANDS = (
    ("architecture-tests", ("pytest", "tests/architecture/")),
)
LAYER_LINT_NAME = "layer-lint"
LAYER_LINT_COMMAND = (str(VENV_BIN / "layer-lint"), "project")
CONTRACT_MARKERS = (
    "data → signals → hypotheses → trade_engine → decision",
    "no upward imports",
    "no layer skipping",
    "no db access outside project/data/",
)


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: list[str]
    status: str
    returncode: int | None
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "command": self.command,
            "status": self.status,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


def check_architecture(root: Path | None = None) -> dict[str, object]:
    working_dir = root or Path.cwd()
    results = [_run_layer_lint(working_dir)]
    results.extend(_run_command(name, command, working_dir) for name, command in ARCHITECTURE_COMMANDS)
    status = "pass" if all(result.status in {"pass", "skipped"} for result in results) else "fail"
    return {"status": status, "checks": [result.to_dict() for result in results]}


def detect_drift(paths: ProjectPaths) -> dict[str, object]:
    prompt_files = sorted((paths.package_root / "prompts").glob("*.txt"))
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in prompt_files)
    violations = _contract_violations(combined)
    violations.extend(_pattern_violations(paths))
    return {"drift_score": max(0, 100 - (len(violations) * 18)), "violations": violations}


def self_heal(task_id: str, run_executor, architecture_passes, diagnose, fix) -> dict[str, object]:
    attempts = []
    for attempt in range(1, MAX_RETRIES + 1):
        execution_result = run_executor()
        architecture_result = architecture_passes()
        record = {"attempt": attempt, "execution": execution_result, "architecture": architecture_result}
        if architecture_result.get("status") == "pass":
            attempts.append(record)
            return {"task_id": task_id, "status": "pass", "attempts": attempts}
        diagnosis = diagnose()
        record["diagnosis"] = diagnosis
        record["fix"] = fix(diagnosis)
        attempts.append(record)
    return {"task_id": task_id, "status": "escalate", "attempts": attempts}


def _contract_violations(combined: str) -> list[dict[str, str]]:
    violations = []
    for marker in CONTRACT_MARKERS:
        if marker not in combined:
            violations.append({"type": "missing_contract_marker", "detail": marker})
    return violations


def _pattern_violations(paths: ProjectPaths) -> list[dict[str, str]]:
    if not paths.violation_patterns.exists():
        return [{"type": "missing_violation_library", "detail": str(paths.violation_patterns)}]
    patterns = json.loads(paths.violation_patterns.read_text(encoding="utf-8"))
    violations = []
    for key in ("signal_leakage", "layer_violation", "hidden_coupling", "premature_abstraction"):
        if key not in patterns:
            violations.append({"type": "missing_violation_pattern", "detail": key})
    return violations


def _run_command(name: str, command: tuple[str, ...], working_dir: Path) -> CommandResult:
    if name == "architecture-tests" and not (working_dir / "tests" / "architecture").exists():
        return CommandResult(name, list(command), "skipped", None, "", "tests/architecture/ does not exist")
    try:
        resolved = _resolve_command(command, working_dir)
        result = subprocess.run(
            resolved,
            cwd=working_dir,
            check=False,
            capture_output=True,
            text=True,
            env=_build_env(working_dir),
        )
    except FileNotFoundError as error:
        return CommandResult(name, list(command), "fail", None, "", str(error))
    status = "pass" if result.returncode == 0 else "fail"
    return CommandResult(name, list(resolved), status, result.returncode, result.stdout, result.stderr)


def _run_layer_lint(working_dir: Path) -> CommandResult:
    try:
        package = _resolve_package("project", working_dir)
        contracts = _load_contracts(working_dir / "layers.yml", "project")
        graph = DependencyGraph(package=package)
        broken = _broken_contracts(contracts, graph)
    except (ContractParseError, FileNotFoundError, RuntimeError, ValueError) as error:
        return CommandResult(LAYER_LINT_NAME, list(LAYER_LINT_COMMAND), "fail", None, "", str(error))
    stdout = _layer_lint_stdout(graph, contracts)
    stderr = _layer_lint_stderr(broken)
    status = "pass" if not broken else "fail"
    returncode = 0 if status == "pass" else 1
    return CommandResult(LAYER_LINT_NAME, list(LAYER_LINT_COMMAND), status, returncode, stdout, stderr)


def _resolve_package(package_name: str, working_dir: Path) -> SafeFilenameModule:
    if str(working_dir) not in sys.path:
        sys.path.insert(0, str(working_dir))
    package_spec = importlib.util.find_spec(package_name)
    if package_spec is None or package_spec.origin is None:
        raise ValueError(f"Could not find package '{package_name}' in {working_dir}.")
    return SafeFilenameModule(name=package_name, filename=package_spec.origin)


def _load_contracts(path: Path, package_name: str) -> list[Contract]:
    if not path.exists():
        raise FileNotFoundError(f"Missing layer contract: {path}")
    data = _parse_contract_yaml(path)
    return [contract_from_yaml(key, value, package_name) for key, value in data.items()]


def _parse_contract_yaml(path: Path) -> dict[str, dict[str, list[str]]]:
    contracts: dict[str, dict[str, list[str]]] = {}
    current_contract = ""
    current_section = ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        current_contract, current_section = _parse_contract_line(raw_line, contracts, current_contract, current_section)
    if not contracts:
        raise ContractParseError(f"Could not parse {path}.")
    return contracts


def _parse_contract_line(
    raw_line: str,
    contracts: dict[str, dict[str, list[str]]],
    current_contract: str,
    current_section: str,
) -> tuple[str, str]:
    if not raw_line.strip() or raw_line.lstrip().startswith("#"):
        return current_contract, current_section
    indent = len(raw_line) - len(raw_line.lstrip(" "))
    stripped = raw_line.strip()
    if indent == 0 and stripped.endswith(":"):
        contracts[stripped[:-1]] = {}
        return stripped[:-1], ""
    if indent == 2 and stripped.endswith(":") and current_contract:
        contracts[current_contract][stripped[:-1]] = []
        return current_contract, stripped[:-1]
    if indent == 4 and stripped.startswith("- ") and current_contract and current_section:
        contracts[current_contract][current_section].append(stripped[2:].strip())
        return current_contract, current_section
    raise ContractParseError(f"Could not parse {raw_line!r}.")


def _broken_contracts(contracts: list[Contract], graph: DependencyGraph) -> list[Contract]:
    broken: list[Contract] = []
    for contract in contracts:
        contract.check_dependencies(graph)
        if not contract.is_kept:
            broken.append(contract)
    return broken


def _layer_lint_stdout(graph: DependencyGraph, contracts: list[Contract]) -> str:
    kept = sum(1 for contract in contracts if contract.is_kept)
    broken = len(contracts) - kept
    lines = [
        "Layer Linter",
        f"Analyzed {graph.module_count} files, {graph.dependency_count} dependencies.",
        f"Contracts: {kept} kept, {broken} broken.",
    ]
    return "\n".join(lines) + "\n"


def _layer_lint_stderr(contracts: list[Contract]) -> str:
    lines: list[str] = []
    for contract in contracts:
        for path in contract.illegal_dependencies:
            lines.append(f"{path[0]} imports {path[-1]}")
    return "\n".join(lines) + ("\n" if lines else "")


def _resolve_command(command: tuple[str, ...], working_dir: Path) -> tuple[str, ...]:
    local = working_dir / ".env" / "bin" / command[0]
    return (str(local), *command[1:]) if local.exists() else command


def _build_env(working_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    root = str(working_dir)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = root if not existing else f"{root}{os.pathsep}{existing}"
    return env
