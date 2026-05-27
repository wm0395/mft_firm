from __future__ import annotations

from pathlib import Path

import click

from project.cli.app_runtime import common_options, invoke
from project.cli.commands.data import quality, snapshot_create, sync
from project.cli.commands.hypothesis import check, list_hypotheses, promote, validate
from project.cli.commands.research import run as research_run
from project.cli.commands.setup import bootstrap, init


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


@click.group("setup")
@common_options
@click.pass_context
def setup(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _set_context(ctx, database, json_mode, output_format, plain)


@click.command("init")
@common_options
@click.pass_context
def setup_init(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "setup-init",
        init,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("bootstrap")
@common_options
@click.pass_context
def setup_bootstrap(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "bootstrap",
        bootstrap,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


setup.add_command(setup_init)
setup.add_command(setup_bootstrap)


@click.group("data")
@common_options
@click.pass_context
def data(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _set_context(ctx, database, json_mode, output_format, plain)


@click.command("sync")
@click.argument("symbols", nargs=-1)
@click.option("--resolution", default="1d", show_default=True)
@click.option("--market-db-url-env", default="MARKET_DB_URL", show_default=True)
@common_options
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
    invoke(
        ctx,
        "data-sync",
        lambda runtime: sync(runtime, symbols, resolution, market_db_url_env),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("quality")
@click.argument("symbols", nargs=-1)
@click.option("--resolution", default="1d", show_default=True)
@click.option("--max-staleness-days", type=int, default=None)
@click.option("--strict", is_flag=True, default=False)
@common_options
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
    invoke(
        ctx,
        "data-quality",
        lambda runtime: quality(runtime, symbols, resolution, max_staleness_days, strict),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.group("snapshot")
def snapshot() -> None:
    return None


@click.command("create")
@click.argument("symbols", nargs=-1)
@click.option("--market", required=True)
@click.option("--from", "data_start", required=True)
@click.option("--to", "data_end", required=True)
@click.option("--resolution", default="1d", show_default=True)
@click.option("--description", default=None)
@common_options
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
    invoke(
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


snapshot.add_command(data_snapshot_create)
data.add_command(data_sync)
data.add_command(data_quality)
data.add_command(snapshot)


@click.group("research")
@common_options
@click.pass_context
def research(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _set_context(ctx, database, json_mode, output_format, plain)


@click.command("run")
@click.argument("hypothesis_id")
@click.argument("symbol")
@click.option("--snapshot", default="latest", show_default=True)
@click.option("--include-testing", is_flag=True, default=False)
@click.option("--include-draft", is_flag=True, default=False)
@common_options
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
    invoke(
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


research.add_command(research_run_command)


@click.group("hypothesis")
@common_options
@click.pass_context
def hypothesis(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    _set_context(ctx, database, json_mode, output_format, plain)


@click.command("list")
@common_options
@click.pass_context
def hypothesis_list_command(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "hypothesis-list",
        list_hypotheses,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("check")
@click.argument("hypothesis_id")
@common_options
@click.pass_context
def hypothesis_check_command(
    ctx: click.Context,
    hypothesis_id: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "hypothesis-check",
        lambda runtime: check(runtime, hypothesis_id),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("validate")
@click.argument("hypothesis_id")
@common_options
@click.pass_context
def hypothesis_validate_command(
    ctx: click.Context,
    hypothesis_id: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "hypothesis-validate",
        lambda runtime: validate(runtime, hypothesis_id),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("promote")
@click.argument("hypothesis_id")
@click.option("--to", "to_status", required=True)
@click.option("--force", is_flag=True, default=False)
@common_options
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
    invoke(
        ctx,
        "hypothesis-promote",
        lambda runtime: promote(runtime, hypothesis_id, to_status, force),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


hypothesis.add_command(hypothesis_list_command)
hypothesis.add_command(hypothesis_check_command)
hypothesis.add_command(hypothesis_validate_command)
hypothesis.add_command(hypothesis_promote_command)
