from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import is_dataclass
from pprint import pformat
from typing import Any

from rich import box
from rich.panel import Panel
from rich.pretty import Pretty

from project.cli.errors import CliError


def _emit_json(
    command: str,
    result: object | None,
    status: str,
    warnings: tuple[str, ...],
    error: CliError | str | None,
) -> None:
    payload = {
        "command": command,
        "status": "error" if error is not None else status,
        "result": None if error is not None else _jsonable(result),
        "warnings": list(warnings),
        "error": None if error is None else str(error),
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def _render_plain(
    console: Any,
    command: str,
    result: object | None,
    status: str,
) -> None:
    console.print(f"{_title(command)}: {status.upper()}")
    if result is None:
        return
    if isinstance(result, Mapping):
        for key, value in result.items():
            console.print(f"{key}: {_scalar(value)}")
        return
    if isinstance(result, Sequence) and not isinstance(result, (str, bytes)):
        for item in result:
            console.print(f"- {_scalar(item)}")
        return
    console.print(_scalar(result))


def _render_error(console: Any, command: str, error: CliError | str) -> None:
    console.print(Panel.fit("", title=f"{_title(command)}: Failed", box=box.SIMPLE))
    if isinstance(error, CliError):
        console.print("Problem:")
        console.print(error.message)
        if error.why:
            console.print()
            console.print("Why it matters:")
            console.print(error.why)
        if error.next_action:
            console.print()
            console.print("Next:")
            console.print(error.next_action)
        if error.command:
            console.print()
            console.print("Run:")
            console.print(error.command)
        return
    console.print("Problem:")
    console.print(str(error))


def _render_generic(
    console: Any,
    command: str,
    result: object | None,
    status: str,
    warnings: tuple[str, ...],
) -> None:
    title = f"{_title(command)}: {status.upper()}"
    body = Pretty(_jsonable(result), expand_all=False)
    console.print(Panel(body, title=title, box=box.SIMPLE))
    if warnings:
        console.print()
        console.print("Warnings:")
        for warning in warnings:
            console.print(f"- {warning}")


def _mapping(result: object | None) -> Mapping[str, Any]:
    if result is None:
        return {}
    if isinstance(result, Mapping):
        return result
    if is_dataclass(result):
        return json.loads(json.dumps(result, default=str))
    return {"value": result}


def _jsonable(result: object | None) -> object | None:
    if result is None:
        return None
    if isinstance(result, Mapping):
        return {key: _jsonable(value) for key, value in result.items()}
    if isinstance(result, Sequence) and not isinstance(result, (str, bytes)):
        return [_jsonable(item) for item in result]
    if is_dataclass(result):
        return _jsonable(result.__dict__)
    return result


def _status_text(status: object, message: object) -> str:
    if str(status) == "ok":
        return "OK"
    if message:
        return f"Warning: {message}"
    return "Warning"


def _scalar(value: object) -> str:
    if isinstance(value, Mapping):
        return pformat(dict(value))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return ", ".join(_scalar(item) for item in value)
    return str(value)


def _title(command: str) -> str:
    return command.replace("-", " ").title()

