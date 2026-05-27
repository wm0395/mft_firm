from __future__ import annotations

import click

from project.cli.app_groups.core import (
    data,
    hypothesis,
    research,
    setup,
)
from project.cli.app_groups.misc import (
    bootstrap_cmd,
    explain,
    examples,
    guide,
    ideas,
    next_cmd,
    report,
    status_cmd,
)
from project.cli.app_groups.operations import (
    alpha101_status_cmd,
    data_source_quality_report_cmd,
    data_source_status_cmd,
    ingest_source_sample_cmd,
    list_data_sources_cmd,
    multi_asset_status_cmd,
    research_control_room_cmd,
    show_data_source_cmd,
    validate_data_source_cmd,
)


def register_commands(app: click.Group) -> None:
    app.add_command(status_cmd)
    app.add_command(next_cmd)
    app.add_command(setup)
    app.add_command(data)
    app.add_command(research)
    app.add_command(hypothesis)
    app.add_command(ideas)
    app.add_command(explain)
    app.add_command(report)
    app.add_command(guide)
    app.add_command(examples)
    app.add_command(bootstrap_cmd)
    app.add_command(research_control_room_cmd)
    app.add_command(alpha101_status_cmd)
    app.add_command(data_source_status_cmd)
    app.add_command(multi_asset_status_cmd)
    app.add_command(list_data_sources_cmd)
    app.add_command(show_data_source_cmd)
    app.add_command(validate_data_source_cmd)
    app.add_command(ingest_source_sample_cmd)
    app.add_command(data_source_quality_report_cmd)
