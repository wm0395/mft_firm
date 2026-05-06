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
    "data → signals → hypotheses → trade → decision → portfolio",
    "no cross-layer access",
    "no shared mutable state",
    "reproducible outputs only",
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
    passed = all(result.status in {"pass", "skipped"} for result in results)
    return {
        "status": "pass" if passed else "fail",
        "checks": [result.to_dict() for result in results],
    }


def detect_drift(paths: ProjectPaths) -> dict[str, object]:
    violations: list[dict[str, str]] = []

    prompt_files = sorted((paths.package_root / "prompts").glob("*.txt"))
    combined_prompts = "\n".join(path.read_text(encoding="utf-8").lower() for path in prompt_files)

    for marker in CONTRACT_MARKERS:
        if marker not in combined_prompts:
            violations.append(
                {
                    "type": "missing_contract_marker",
                    "detail": marker,
                }
            )

    if not paths.violation_patterns.exists():
        violations.append(
            {
                "type": "missing_violation_library",
                "detail": str(paths.violation_patterns),
            }
        )
    else:
        patterns = json.loads(paths.violation_patterns.read_text(encoding="utf-8"))
        for key in (
            "signal_leakage",
            "layer_violation",
            "hidden_coupling",
            "premature_abstraction",
            "data_mutation_violation",
        ):
            if key not in patterns:
                violations.append(
                    {
                        "type": "missing_violation_pattern",
                        "detail": key,
                    }
                )

    drift_score = max(0, 100 - (len(violations) * 18))
    return {
        "drift_score": drift_score,
        "violations": violations,
    }


def self_heal(task_id: str, run_executor, architecture_passes, diagnose, fix) -> dict[str, object]:
    attempts = []
    for attempt in range(1, MAX_RETRIES + 1):
        execution_result = run_executor()
        architecture_result = architecture_passes()
        attempts.append(
            {
                "attempt": attempt,
                "execution": execution_result,
                "architecture": architecture_result,
            }
        )
        if architecture_result.get("status") == "pass":
            return {
                "task_id": task_id,
                "status": "pass",
                "attempts": attempts,
            }

        diagnosis = diagnose()
        fix_result = fix(diagnosis)
        attempts[-1]["diagnosis"] = diagnosis
        attempts[-1]["fix"] = fix_result

    return {
        "task_id": task_id,
        "status": "escalate",
        "attempts": attempts,
    }


def _run_command(name: str, command: tuple[str, ...], working_dir: Path) -> CommandResult:
    if name == "architecture-tests" and not (working_dir / "tests" / "architecture").exists():
        return CommandResult(
            name=name,
            command=list(command),
            status="skipped",
            returncode=None,
            stdout="",
            stderr="tests/architecture/ does not exist",
        )

    try:
        resolved_command = _resolve_command(command, working_dir)
        result = subprocess.run(
            resolved_command,
            cwd=working_dir,
            check=False,
            capture_output=True,
            text=True,
            env=_build_env(working_dir),
        )
    except FileNotFoundError as error:
        return CommandResult(
            name=name,
            command=list(command),
            status="fail",
            returncode=None,
            stdout="",
            stderr=str(error),
        )

    return CommandResult(
        name=name,
        command=list(resolved_command),
        status="pass" if result.returncode == 0 else "fail",
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _resolve_command(command: tuple[str, ...], working_dir: Path) -> tuple[str, ...]:
    local_command = working_dir / ".env" / "bin" / command[0]
    if local_command.exists():
        return (str(local_command), *command[1:])
    return command


def _build_env(working_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    root = str(working_dir)
    env["PYTHONPATH"] = root if not existing else f"{root}{os.pathsep}{existing}"
    return env
