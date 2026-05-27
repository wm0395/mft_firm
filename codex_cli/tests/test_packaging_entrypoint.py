from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parent
IGNORED_PACKAGE_DIRS = (
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "memory",
    "mft_codex_cli.egg-info",
    "runtime",
    "state",
    "tasks",
)


def test_editable_install_exposes_ai_code_command_from_repo_root(tmp_path: Path) -> None:
    checkout_root = _create_checkout(tmp_path)
    install_env = _install_environment()
    _run([sys.executable, "-m", "venv", ".venv"], checkout_root, install_env)
    _run([str(checkout_root / ".venv" / "bin" / "python"), "-m", "pip", "install", "-e", "./codex_cli"], checkout_root, install_env)

    workspace_env = os.environ.copy()
    workspace_env["PATH"] = _path_with_bin(checkout_root / ".venv" / "bin", workspace_env)
    _create_provider_stub(checkout_root / ".venv" / "bin" / "codex")
    _create_provider_stub(checkout_root / ".venv" / "bin" / "opencode")

    help_result = _run(["ai_code", "--help"], checkout_root, workspace_env)
    assert "usage: ai_code" in help_result.stdout

    list_result = _run(["ai_code", "list"], checkout_root, workspace_env)
    assert json.loads(list_result.stdout) == {"status": "ready", "tasks": []}

    run_result = _run(["ai_code", "run", "test bounded task"], checkout_root, workspace_env)
    run_payload = json.loads(run_result.stdout)
    assert run_payload["task"]["id"] == "task_001"

    exec_result = _run(["ai_code", "exec", "task_001"], checkout_root, workspace_env)
    exec_payload = json.loads(exec_result.stdout)
    assert exec_payload["execution"]["task_id"] == "task_001"

    dry_run_result = _run(
        ["ai_code", "execute", "task_001", "--dry-run", "--mode", "oneshot"],
        checkout_root,
        workspace_env,
    )
    dry_run_payload = json.loads(dry_run_result.stdout)
    assert dry_run_payload["launch"]["provider"] == "opencode"
    assert dry_run_payload["launch"]["command"][0] == str(checkout_root / ".venv" / "bin" / "opencode")


def _create_checkout(root: Path) -> Path:
    checkout_root = root / "checkout"
    checkout_root.mkdir()
    shutil.copytree(REPO_ROOT / "docs" / "prompts", checkout_root / "docs" / "prompts")
    shutil.copytree(PACKAGE_ROOT, checkout_root / "codex_cli", ignore=_ignore_package_artifacts)
    (checkout_root / "AGENTS.md").write_text("# Rules\n- keep it bounded\n", encoding="utf-8")
    (checkout_root / "README.md").write_text("# Test checkout\n", encoding="utf-8")
    (checkout_root / "project").mkdir()
    (checkout_root / "project" / "signals.py").write_text("def signal():\n    return 1\n", encoding="utf-8")
    return checkout_root


def _ignore_package_artifacts(directory: str, names: list[str]) -> set[str]:
    ignored = set(IGNORED_PACKAGE_DIRS)
    return {name for name in names if name in ignored}


def _install_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["PIP_NO_INDEX"] = "1"
    return env


def _path_with_bin(bin_dir: Path, env: dict[str, str]) -> str:
    path = env.get("PATH", "")
    return str(bin_dir) if not path else f"{bin_dir}{os.pathsep}{path}"


def _create_provider_stub(path: Path) -> None:
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _run(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result
