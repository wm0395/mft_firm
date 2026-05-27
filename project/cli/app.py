from __future__ import annotations

from pathlib import Path

import click
from project.cli.app_groups import register_commands
from project.cli.app_runtime import common_options, runtime_context
from project.cli.formatting import render_intro


@click.group(
    invoke_without_command=True,
    help=(
        "MFT investment workflow CLI for setup, data, research, "
        "hypotheses, ideas, explainability, and reports."
    ),
)
@common_options
@click.pass_context
def app(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    ctx.obj = {
        "database": database,
        "json_mode": json_mode,
        "output_format": output_format,
        "plain": plain,
    }
    if ctx.invoked_subcommand is None:
        runtime = runtime_context(ctx, database, json_mode, output_format, plain)
        render_intro(runtime.console)
        ctx.exit(0)


register_commands(app)


if __name__ == "__main__":
    app()
