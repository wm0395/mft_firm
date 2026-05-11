from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from .architecture import check_architecture


REQUIRED_COMMANDS = (
    ("pytest", (sys.executable, "-m", "pytest")),
    ("ruff", (sys.executable, "-m", "ruff", "check", ".")),
    ("typing", (sys.executable, "-m", "mypy")),
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    command: tuple[str, ...]
    status: str
    returncode: int | None
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "command": list(self.command),
            "status": self.status,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


def run_required_checks(root: Path | None = None) -> dict[str, object]:
    working_dir = root or Path.cwd()
    results = [_run_check(name, command, working_dir) for name, command in REQUIRED_COMMANDS]
    architecture = check_architecture(working_dir)
    checks = [result.to_dict() for result in results]
    architecture_checks = cast(list[dict[str, object]], architecture["checks"])
    architecture_status = cast(str, architecture["status"])
    checks.extend(architecture_checks)
    status = "pass" if _all_passed(results, architecture_status) else "fail"
    return {"status": status, "checks": checks}


def _run_check(name: str, command: tuple[str, ...], working_dir: Path) -> CheckResult:
    try:
        result = subprocess.run(
            command,
            cwd=working_dir,
            check=False,
            capture_output=True,
            text=True,
            env=_build_env(working_dir),
        )
    except FileNotFoundError as error:
        return CheckResult(name, command, "fail", None, "", str(error))
    status = "pass" if result.returncode == 0 else "fail"
    return CheckResult(name, command, status, result.returncode, result.stdout, result.stderr)


def _build_env(working_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    root = str(working_dir)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = root if not existing else f"{root}{os.pathsep}{existing}"
    return env


def _all_passed(results: list[CheckResult], architecture_status: str) -> bool:
    return all(result.status == "pass" for result in results) and architecture_status == "pass"
