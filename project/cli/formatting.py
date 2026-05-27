from __future__ import annotations

from project.cli.context import CLIContext
from project.cli.errors import CliError
from project.cli.formatting_core import _emit_json, _render_error, _render_plain
from project.cli.formatting_human import _render_human
from project.cli.formatting_text import render_examples, render_guide, render_intro

__all__ = ["emit", "render_examples", "render_guide", "render_intro"]


def emit(
    context: CLIContext,
    command: str,
    result: object | None,
    *,
    status: str = "ok",
    warnings: tuple[str, ...] = (),
    error: CliError | str | None = None,
) -> None:
    if context.output_mode == "json":
        _emit_json(command, result, status, warnings, error)
        return
    if error is not None:
        _render_error(context.console, command, error)
        return
    if context.output_mode == "plain":
        _render_plain(context.console, command, result, status)
        return
    _render_human(context.console, command, result, status, warnings)
