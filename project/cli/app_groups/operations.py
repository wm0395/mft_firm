from __future__ import annotations

from pathlib import Path

import click

from project.cli.app_runtime import common_options, invoke
from project.cli.commands.control_room import (
    alpha101_status,
    data_source_status,
    multi_asset_status,
    research_control_room,
)
from project.cli.commands.data_sources import (
    data_source_quality_report,
    ingest_source_sample,
    list_data_sources,
    show_data_source,
    validate_data_source,
)


@click.command("research-control-room")
@common_options
@click.pass_context
def research_control_room_cmd(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "research-control-room",
        research_control_room,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("alpha101-status")
@common_options
@click.pass_context
def alpha101_status_cmd(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "alpha101-status",
        alpha101_status,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("data-source-status")
@common_options
@click.pass_context
def data_source_status_cmd(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "data-source-status",
        data_source_status,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("multi-asset-status")
@common_options
@click.pass_context
def multi_asset_status_cmd(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "multi-asset-status",
        multi_asset_status,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("list-data-sources")
@common_options
@click.pass_context
def list_data_sources_cmd(
    ctx: click.Context,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "list-data-sources",
        list_data_sources,
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("show-data-source")
@click.argument("source_id")
@common_options
@click.pass_context
def show_data_source_cmd(
    ctx: click.Context,
    source_id: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "show-data-source",
        lambda runtime: show_data_source(runtime, source_id),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("validate-data-source")
@click.argument("source_id")
@common_options
@click.pass_context
def validate_data_source_cmd(
    ctx: click.Context,
    source_id: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "validate-data-source",
        lambda runtime: validate_data_source(runtime, source_id),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("ingest-source-sample")
@click.argument("source_id")
@click.option("--asset-class", "asset_class", required=True)
@common_options
@click.pass_context
def ingest_source_sample_cmd(
    ctx: click.Context,
    source_id: str,
    asset_class: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "ingest-source-sample",
        lambda runtime: ingest_source_sample(runtime, source_id, asset_class),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )


@click.command("data-source-quality-report")
@click.argument("source_id")
@common_options
@click.pass_context
def data_source_quality_report_cmd(
    ctx: click.Context,
    source_id: str,
    database: Path | None,
    json_mode: bool,
    output_format: str | None,
    plain: bool,
) -> None:
    invoke(
        ctx,
        "data-source-quality-report",
        lambda runtime: data_source_quality_report(runtime, source_id),
        database=database,
        json_mode=json_mode,
        output_format=output_format,
        plain=plain,
    )
