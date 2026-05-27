from __future__ import annotations

from collections.abc import Callable
from os import fspath
from pathlib import Path

import click

from project.cli.context import (
    CLIContext,
    build_context,
    default_database_path,
    resolve_output_mode,
)
from project.cli.errors import CliError, CommandOutcome
from project.cli.formatting import emit


def common_options(func: Callable) -> Callable:
    options = [
        click.option("--database", type=click.Path(path_type=str), default=None),
        click.option(
            "--json", "json_mode", is_flag=True, default=False, help="Emit JSON output."
        ),
        click.option(
            "--format",
            "output_format",
            type=click.Choice(["human", "json", "plain"]),
            default=None,
            help="Select the output format.",
        ),
        click.option("--plain", is_flag=True, default=False, help="Emit plain text output."),
    ]
    for option in reversed(options):
        func = option(func)
    return func


def runtime_context(
    ctx: click.Context,
    database: Path | str | bytes | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> CLIContext:
    defaults = ctx.obj if isinstance(ctx.obj, dict) else {}
    selected_database = database or defaults.get("database") or default_database_path()
    selected_output = resolve_output_mode(
        output_format if output_format is not None else defaults.get("output_format"),
        json_mode or bool(defaults.get("json_mode")),
        plain or bool(defaults.get("plain")),
    )
    return build_context(coerce_path(selected_database), selected_output)


def coerce_path(value: Path | str | bytes) -> Path:
    raw = fspath(value)
    if isinstance(raw, bytes):
        raw = raw.decode()
    return Path(raw)


def invoke(
    ctx: click.Context,
    command: str,
    runner: Callable[[CLIContext], CommandOutcome],
    *,
    database: Path | None = None,
    json_mode: bool = False,
    output_format: str | None = None,
    plain: bool = False,
) -> None:
    runtime = runtime_context(ctx, database, json_mode, output_format, plain)
    try:
        outcome = runner(runtime)
    except CliError as error:
        emit(runtime, command, None, status="fail", error=error)
        ctx.exit(error.exit_code)
    except Exception as error:
        emit(runtime, command, None, status="fail", error=CliError(str(error)))
        ctx.exit(1)
    emit(
        runtime,
        command,
        outcome.result,
        status=outcome.status,
        warnings=outcome.warnings,
    )
    ctx.exit(outcome.exit_code)
