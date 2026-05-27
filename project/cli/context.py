from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal, cast

from rich.console import Console

from project.data.repository import DataRepository, build_repository


OutputMode = Literal["human", "json", "plain"]


@dataclass(frozen=True)
class CLIContext:
    database: Path
    output_mode: OutputMode
    console: Console


def default_database_path() -> Path:
    return Path("project_mft.duckdb")


def resolve_output_mode(
    output_format: str | None,
    json_mode: bool,
    plain: bool,
) -> OutputMode:
    if output_format is not None:
        return cast(OutputMode, output_format)
    if json_mode:
        return "json"
    if plain:
        return "plain"
    return "human"


def build_context(database: Path, output_mode: OutputMode) -> CLIContext:
    return CLIContext(
        database=database,
        output_mode=output_mode,
        console=Console(
            width=100,
            color_system=None,
            force_terminal=False,
            highlight=False,
            soft_wrap=True,
        ),
    )


@contextmanager
def open_repository(database: Path, read_only: bool) -> Iterator[DataRepository]:
    if read_only and not database.exists():
        raise FileNotFoundError(f"database not found: {database}")
    repository = build_repository(database, read_only=read_only)
    try:
        yield repository
    finally:
        repository.close()
