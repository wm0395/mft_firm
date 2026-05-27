from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .launch_policy import opencode_config_json


LAUNCH_PROVIDERS = ("codex", "opencode")
INTERACTIVE = "interactive"
ONESHOT = "oneshot"


@dataclass(frozen=True)
class LaunchResult:
    provider: str
    mode: str
    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    json_output: bool
    model: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "mode": self.mode,
            "command": list(self.command),
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "json_output": self.json_output,
            "model": self.model,
        }


def launch_task(
    provider: str,
    mode: str,
    prompt: str,
    workspace: Path,
    model: str | None,
    json_output: bool,
) -> LaunchResult:
    _validate_launch(provider, mode, json_output)
    command = build_launch_command(provider, mode, prompt, workspace, model, json_output)
    env = _build_env(workspace, provider)
    if mode == INTERACTIVE:
        interactive_result: subprocess.CompletedProcess[str] = subprocess.run(command, check=False, env=env, text=True)
        return LaunchResult(provider, mode, tuple(command), interactive_result.returncode, "", "", json_output, model)
    oneshot_result: subprocess.CompletedProcess[str] = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    return LaunchResult(
        provider,
        mode,
        tuple(command),
        oneshot_result.returncode,
        oneshot_result.stdout,
        oneshot_result.stderr,
        json_output,
        model,
    )


def build_launch_command(
    provider: str,
    mode: str,
    prompt: str,
    workspace: Path,
    model: str | None,
    json_output: bool,
) -> list[str]:
    executable = _resolve_binary(provider)
    workspace_text = str(workspace)
    if provider == "codex":
        return _codex_command(executable, mode, prompt, workspace_text, model, json_output)
    return _opencode_command(executable, mode, prompt, workspace_text, model, json_output)


def _validate_launch(provider: str, mode: str, json_output: bool) -> None:
    if provider not in LAUNCH_PROVIDERS:
        raise ValueError(f"Unsupported launch provider: {provider}")
    if mode not in {INTERACTIVE, ONESHOT}:
        raise ValueError(f"Unsupported launch mode: {mode}")
    if json_output and mode != ONESHOT:
        raise ValueError("--json is only supported in oneshot mode")
    if mode == INTERACTIVE and not sys.stdin.isatty():
        raise ValueError("Interactive mode requires a TTY; use --mode oneshot instead")


def _resolve_binary(provider: str) -> str:
    resolved = shutil.which(provider)
    if resolved is None:
        raise FileNotFoundError(f"Required provider binary not found: {provider}")
    return resolved


def _codex_command(
    executable: str,
    mode: str,
    prompt: str,
    workspace: str,
    model: str | None,
    json_output: bool,
) -> list[str]:
    if mode == INTERACTIVE:
        command = [executable, "--sandbox", "workspace-write", "-C", workspace]
        if model:
            command.extend(["-m", model])
        command.append(prompt)
        return command
    command = [executable, "exec", "--sandbox", "workspace-write", "-C", workspace]
    if model:
        command.extend(["-m", model])
    if json_output:
        command.append("--json")
    command.append(prompt)
    return command


def _opencode_command(
    executable: str,
    mode: str,
    prompt: str,
    workspace: str,
    model: str | None,
    json_output: bool,
) -> list[str]:
    if mode == INTERACTIVE:
        command = [executable, "--dir", workspace, "--prompt", prompt]
    else:
        command = [executable, "run", "--dir", workspace]
        if json_output:
            command.extend(["--format", "json"])
        command.append(prompt)
    if model:
        command.extend(["--model", model])
    return command


def _build_env(workspace: Path, provider: str = "codex") -> dict[str, str]:
    env = os.environ.copy()
    root = str(workspace)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = root if not existing else f"{root}{os.pathsep}{existing}"
    env.update(_provider_runtime_env(workspace, provider))
    return env


def _provider_runtime_env(workspace: Path, provider: str) -> dict[str, str]:
    runtime_root = workspace / "codex_cli" / "runtime" / provider
    if provider == "opencode":
        return _opencode_runtime_env(runtime_root)
    return _codex_runtime_env(runtime_root)


def _codex_runtime_env(runtime_root: Path) -> dict[str, str]:
    home = runtime_root / "home"
    config_home = runtime_root / "xdg" / "config"
    data_home = runtime_root / "xdg" / "data"
    state_home = runtime_root / "xdg" / "state"
    cache_home = runtime_root / "xdg" / "cache"
    codex_home = home / ".codex"
    temp_home = runtime_root / "tmp"
    mypy_cache = runtime_root / "mypy_cache"
    for path in (home, config_home, data_home, state_home, cache_home, codex_home, temp_home, mypy_cache):
        path.mkdir(parents=True, exist_ok=True)
    return {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(config_home),
        "XDG_DATA_HOME": str(data_home),
        "XDG_STATE_HOME": str(state_home),
        "XDG_CACHE_HOME": str(cache_home),
        "CODEX_HOME": str(codex_home),
        "TMPDIR": str(temp_home),
        "TMP": str(temp_home),
        "TEMP": str(temp_home),
        "MYPY_CACHE_DIR": str(mypy_cache),
    }


def _opencode_runtime_env(runtime_root: Path) -> dict[str, str]:
    home = runtime_root / "home"
    config_home = runtime_root / "xdg" / "config"
    data_home = runtime_root / "xdg" / "data"
    state_home = runtime_root / "xdg" / "state"
    cache_home = runtime_root / "xdg" / "cache"
    temp_home = runtime_root / "tmp"
    mypy_cache = runtime_root / "mypy_cache"
    config_path = config_home / "opencode.json"
    for path in (home, config_home, data_home, state_home, cache_home, temp_home, mypy_cache):
        path.mkdir(parents=True, exist_ok=True)
    config_path.write_text(opencode_config_json(), encoding="utf-8")
    return {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(config_home),
        "XDG_DATA_HOME": str(data_home),
        "XDG_STATE_HOME": str(state_home),
        "XDG_CACHE_HOME": str(cache_home),
        "OPENCODE_CONFIG": str(config_path),
        "TMPDIR": str(temp_home),
        "TMP": str(temp_home),
        "TEMP": str(temp_home),
        "MYPY_CACHE_DIR": str(mypy_cache),
    }
