from __future__ import annotations

from pathlib import Path

import click

from project.cli.app_runtime import common_options, invoke, runtime_context
from project.cli.commands.explain import lineage as explain_lineage
from project.cli.commands.explain import signal as explain_signal
from project.cli.commands.explain import trade as explain_trade
from project.cli.commands.ideas import list_ideas, review
from project.cli.commands.report import backtests, dossier, performance, rejected
from project.cli.commands.setup import bootstrap as setup_bootstrap
from project.cli.commands.status import next_action as run_next_action
from project.cli.commands.status import status as run_status
from project.cli.formatting import emit


def _set_context(
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


@click.command("status")
@click.option("--checks", is_flag=True, default=False, help="Show detailed health checks.")
@common_options
@click.pass_context
def status_cmd(
    ctx: click.Context,
    checks: bool,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "status",
        lambda runtime: run_status(runtime, checks),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("next")
@common_options
@click.pass_context
def next_cmd(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "next",
        run_next_action,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.group("ideas")
@common_options
@click.pass_context
def ideas(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _set_context(ctx, database, json_mode, output_format, plain)


@click.command("review")
@common_options
@click.pass_context
def ideas_review_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "ideas-review",
        review,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("list")
@common_options
@click.pass_context
def ideas_list_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "ideas-list",
        list_ideas,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


ideas.add_command(ideas_review_command)
ideas.add_command(ideas_list_command)


@click.group("explain")
@common_options
@click.pass_context
def explain(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _set_context(ctx, database, json_mode, output_format, plain)


@click.command("lineage")
@click.option("--hypothesis-id", default=None)
@click.option("--signal-type", default=None)
@common_options
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
    invoke(
        ctx,
        "explain-lineage",
        lambda runtime: explain_lineage(runtime, hypothesis_id, signal_type),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("signal")
@click.argument("asset_symbol")
@common_options
@click.pass_context
def explain_signal_command(
    ctx: click.Context,
    asset_symbol: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "explain-signal",
        lambda runtime: explain_signal(runtime, asset_symbol),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("trade")
@click.argument("hypothesis_id")
@common_options
@click.pass_context
def explain_trade_command(
    ctx: click.Context,
    hypothesis_id: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "explain-trade",
        lambda runtime: explain_trade(runtime, hypothesis_id),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


explain.add_command(explain_lineage_command)
explain.add_command(explain_signal_command)
explain.add_command(explain_trade_command)


@click.group("report")
@common_options
@click.pass_context
def report(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _set_context(ctx, database, json_mode, output_format, plain)


@click.command("backtests")
@common_options
@click.pass_context
def report_backtests_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "report-backtests",
        backtests,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("performance")
@common_options
@click.pass_context
def report_performance_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "report-performance",
        performance,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("rejected")
@common_options
@click.pass_context
def report_rejected_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "report-rejected",
        rejected,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("dossier")
@click.argument("hypothesis_id")
@common_options
@click.pass_context
def report_dossier_command(
    ctx: click.Context,
    hypothesis_id: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "report-dossier",
        lambda runtime: dossier(runtime, hypothesis_id),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


report.add_command(report_backtests_command)
report.add_command(report_performance_command)
report.add_command(report_rejected_command)
report.add_command(report_dossier_command)


@click.command("guide")
@common_options
@click.pass_context
def guide(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    runtime = runtime_context(ctx, database, json_mode, output_format, plain)
    emit(runtime, "guide", {"items": []}, status="ok")
    ctx.exit(0)


@click.command("examples")
@common_options
@click.pass_context
def examples(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    runtime = runtime_context(ctx, database, json_mode, output_format, plain)
    emit(runtime, "examples", {"items": []}, status="ok")
    ctx.exit(0)


@click.command("bootstrap")
@common_options
@click.pass_context
def bootstrap_cmd(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "bootstrap",
        setup_bootstrap,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )
