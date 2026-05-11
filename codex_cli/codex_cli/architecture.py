from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .paths import ProjectPaths


MAX_RETRIES = 3
VENV_BIN = Path(sys.executable).parent
ARCHITECTURE_COMMANDS = (
    ("layer-lint", (str(VENV_BIN / "layer-lint"), "project")),
    ("architecture-tests", ("pytest", "tests/architecture/")),
)
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
    results = [_run_command(name, command, working_dir) for name, command in ARCHITECTURE_COMMANDS]
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


def _resolve_command(command: tuple[str, ...], working_dir: Path) -> tuple[str, ...]:
    local = working_dir / ".env" / "bin" / command[0]
    return (str(local), *command[1:]) if local.exists() else command


def _build_env(working_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    root = str(working_dir)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = root if not existing else f"{root}{os.pathsep}{existing}"
    return env
