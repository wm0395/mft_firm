from __future__ import annotations

from pathlib import Path
from os import fspath
from typing import Callable

import click

from project.cli.commands.data import quality, snapshot_create, sync
from project.cli.commands.explain import signal as explain_signal
from project.cli.commands.explain import trade as explain_trade
from project.cli.commands.explain import lineage as explain_lineage
from project.cli.commands.hypothesis import check, list_hypotheses, promote, validate
from project.cli.commands.ideas import list_ideas, review
from project.cli.commands.report import backtests, dossier, performance, rejected
from project.cli.commands.research import run as research_run
from project.cli.commands.setup import bootstrap, init
from project.cli.commands.status import next_action as run_next_action
from project.cli.commands.status import status as run_status
from project.cli.context import (
    CLIContext,
    build_context,
    default_database_path,
    resolve_output_mode,
)
from project.cli.errors import CliError, CommandOutcome
from project.cli.formatting import emit, render_intro


def _common_options(func: Callable) -> Callable:
    options = [
        click.option("--database", type=click.Path(path_type=str), default=None),
        click.option("--json", "json_mode", is_flag=True, default=False, help="Emit JSON output."),
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


def _runtime_context(
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
    return build_context(_coerce_path(selected_database), selected_output)


def _coerce_path(value: Path | str | bytes) -> Path:
    raw = fspath(value)
    if isinstance(raw, bytes):
        raw = raw.decode()
    return Path(raw)


def _invoke(
    ctx: click.Context,
    command: str,
    runner: Callable[[CLIContext], CommandOutcome],
    *,
    database: Path | None = None,
    json_mode: bool = False,
    output_format: str | None = None,
    plain: bool = False,
) -> None:
    runtime = _runtime_context(ctx, database, json_mode, output_format, plain)
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


@click.group(
    invoke_without_command=True,
    help=(
        "MFT investment workflow CLI for setup, data, research, "
        "hypotheses, ideas, explainability, and reports."
    ),
)
@_common_options
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
        runtime = _runtime_context(ctx, database, json_mode, output_format, plain)
        render_intro(runtime.console)
        ctx.exit(0)


@app.command("status")
@_common_options
@click.option("--checks", is_flag=True, default=False, help="Show detailed health checks.")
@click.pass_context
def status_cmd(
    ctx: click.Context,
    checks: bool,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "status",
        lambda runtime: run_status(runtime, checks),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@app.command("next")
@_common_options
@click.pass_context
def next_cmd(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "next",
        run_next_action,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@app.group()
@_common_options
@click.pass_context
def setup(
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


@setup.command("init")
@_common_options
@click.pass_context
def setup_init(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "setup-init",
        init,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@setup.command("bootstrap")
@_common_options
@click.pass_context
def setup_bootstrap(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "bootstrap",
        bootstrap,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@app.group()
@_common_options
@click.pass_context
def data(
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


@data.command("sync")
@click.argument("symbols", nargs=-1)
@click.option("--resolution", default="1d", show_default=True)
@click.option("--market-db-url-env", default="MARKET_DB_URL", show_default=True)
@_common_options
@click.pass_context
def data_sync(
    ctx: click.Context,
    symbols: tuple[str, ...],
    resolution: str,
    market_db_url_env: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "data-sync",
        lambda runtime: sync(runtime, symbols, resolution, market_db_url_env),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@data.command("quality")
@click.argument("symbols", nargs=-1)
@click.option("--resolution", default="1d", show_default=True)
@click.option("--max-staleness-days", type=int, default=None)
@click.option("--strict", is_flag=True, default=False)
@_common_options
@click.pass_context
def data_quality(
    ctx: click.Context,
    symbols: tuple[str, ...],
    resolution: str,
    max_staleness_days: int | None,
    strict: bool,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "data-quality",
        lambda runtime: quality(runtime, symbols, resolution, max_staleness_days, strict),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@data.group()
def snapshot() -> None:
    return None


@snapshot.command("create")
@click.argument("symbols", nargs=-1)
@click.option("--market", required=True)
@click.option("--from", "data_start", required=True)
@click.option("--to", "data_end", required=True)
@click.option("--resolution", default="1d", show_default=True)
@click.option("--description", default=None)
@_common_options
@click.pass_context
def data_snapshot_create(
    ctx: click.Context,
    symbols: tuple[str, ...],
    market: str,
    data_start: str,
    data_end: str,
    resolution: str,
    description: str | None,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "data-snapshot-create",
        lambda runtime: snapshot_create(
            runtime, symbols, market, data_start, data_end, resolution, description
        ),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@app.group()
@_common_options
@click.pass_context
def research(
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


@research.command("run")
@click.argument("hypothesis_id")
@click.argument("symbol")
@click.option("--snapshot", default="latest", show_default=True)
@click.option("--include-testing", is_flag=True, default=False)
@click.option("--include-draft", is_flag=True, default=False)
@_common_options
@click.pass_context
def research_run_command(
    ctx: click.Context,
    hypothesis_id: str,
    symbol: str,
    snapshot: str,
    include_testing: bool,
    include_draft: bool,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "research-run",
        lambda runtime: research_run(
            runtime, hypothesis_id, symbol, snapshot, include_testing, include_draft
        ),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@app.group()
@_common_options
@click.pass_context
def hypothesis(
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


@hypothesis.command("list")
@_common_options
@click.pass_context
def hypothesis_list_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "hypothesis-list",
        list_hypotheses,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@hypothesis.command("check")
@click.argument("hypothesis_id")
@_common_options
@click.pass_context
def hypothesis_check_command(
    ctx: click.Context,
    hypothesis_id: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "hypothesis-check",
        lambda runtime: check(runtime, hypothesis_id),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@hypothesis.command("validate")
@click.argument("hypothesis_id")
@_common_options
@click.pass_context
def hypothesis_validate_command(
    ctx: click.Context,
    hypothesis_id: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "hypothesis-validate",
        lambda runtime: validate(runtime, hypothesis_id),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@hypothesis.command("promote")
@click.argument("hypothesis_id")
@click.option("--to", "to_status", required=True)
@click.option("--force", is_flag=True, default=False)
@_common_options
@click.pass_context
def hypothesis_promote_command(
    ctx: click.Context,
    hypothesis_id: str,
    to_status: str,
    force: bool,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "hypothesis-promote",
        lambda runtime: promote(runtime, hypothesis_id, to_status, force),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@app.group()
@_common_options
@click.pass_context
def ideas(
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


@ideas.command("review")
@_common_options
@click.pass_context
def ideas_review_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "ideas-review",
        review,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@ideas.command("list")
@_common_options
@click.pass_context
def ideas_list_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "ideas-list",
        list_ideas,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@app.group()
@_common_options
@click.pass_context
def explain(
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


@explain.command("lineage")
@click.option("--hypothesis-id", default=None)
@click.option("--signal-type", default=None)
@_common_options
@click.pass_context
def explain_lineage_command(
    ctx: click.Context,
    hypothesis_id: str | None,
    signal_type: str | None,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "explain-lineage",
        lambda runtime: explain_lineage(runtime, hypothesis_id, signal_type),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@explain.command("signal")
@click.argument("asset_symbol")
@_common_options
@click.pass_context
def explain_signal_command(
    ctx: click.Context,
    asset_symbol: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "explain-signal",
        lambda runtime: explain_signal(runtime, asset_symbol),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@explain.command("trade")
@click.argument("hypothesis_id")
@_common_options
@click.pass_context
def explain_trade_command(
    ctx: click.Context,
    hypothesis_id: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "explain-trade",
        lambda runtime: explain_trade(runtime, hypothesis_id),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@app.group()
@_common_options
@click.pass_context
def report(
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


@report.command("backtests")
@_common_options
@click.pass_context
def report_backtests_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "report-backtests",
        backtests,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@report.command("performance")
@_common_options
@click.pass_context
def report_performance_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "report-performance",
        performance,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@report.command("rejected")
@_common_options
@click.pass_context
def report_rejected_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "report-rejected",
        rejected,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@report.command("dossier")
@click.argument("hypothesis_id")
@_common_options
@click.pass_context
def report_dossier_command(
    ctx: click.Context,
    hypothesis_id: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "report-dossier",
        lambda runtime: dossier(runtime, hypothesis_id),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@app.command("guide")
@_common_options
@click.pass_context
def guide(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    runtime = _runtime_context(ctx, database, json_mode, output_format, plain)
    emit(runtime, "guide", {"items": []}, status="ok")
    ctx.exit(0)


@app.command("examples")
@_common_options
@click.pass_context
def examples(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    runtime = _runtime_context(ctx, database, json_mode, output_format, plain)
    emit(runtime, "examples", {"items": []}, status="ok")
    ctx.exit(0)


@app.command("bootstrap")
@_common_options
@click.pass_context
def bootstrap_cmd(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _invoke(
        ctx,
        "bootstrap",
        bootstrap,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


if __name__ == "__main__":
    app()
