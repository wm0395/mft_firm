from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any
from project.cli.context import CLIContext, open_repository
from project.cli.errors import CliError, CommandOutcome
from project.data.quality import build_data_quality_report
from project.data.snapshot_builder import create_dataset_snapshot
from project.data.market_server_loader import sync_market_data


def quality(
    context: CLIContext,
    symbols: tuple[str, ...],
    resolution: str,
    max_staleness_days: int | None,
    strict: bool,
) -> CommandOutcome:
    if not context.database.exists():
        raise CliError(
            "Database is not initialized.",
            why="Data quality checks require the local schema.",
            next_action="Initialize the database.",
            command="mft setup init",
        )
    with open_repository(context.database, read_only=True) as repository:
        report = build_data_quality_report(
            repository,
            symbols,
            resolution,
            max_staleness_days,
        )
        payload: dict[str, Any] = asdict(report)
    payload.update(_next_step_for_quality(payload))
    return CommandOutcome(
        payload,
        status=str(payload["status"]),
        exit_code=1 if strict and payload["status"] == "fail" else 0,
    )


def sync(
    context: CLIContext,
    symbols: tuple[str, ...],
    resolution: str,
    market_db_url_env: str,
) -> CommandOutcome:
    if not context.database.exists():
        raise CliError(
            "Database is not initialized.",
            why="Market data sync persists rows into the local schema.",
            next_action="Initialize the database.",
            command="mft setup init",
        )
    with open_repository(context.database, read_only=False) as repository:
        payload = sync_market_data(repository, symbols, resolution, market_db_url_env)
    return CommandOutcome(payload, status="ok")


def snapshot_create(
    context: CLIContext,
    symbols: tuple[str, ...],
    market: str,
    data_start: str,
    data_end: str,
    resolution: str,
    description: str | None,
) -> CommandOutcome:
    if not context.database.exists():
        raise CliError(
            "Database is not initialized.",
            why="Snapshots are written into the local schema.",
            next_action="Initialize the database.",
            command="mft setup init",
        )
    with open_repository(context.database, read_only=False) as repository:
        try:
            result = create_dataset_snapshot(
                repository,
                name="research-snapshot",
                market=market,
                symbols=symbols,
                data_start=data_start,
                data_end=data_end,
                resolution=resolution,
                description=description,
            )
        except ValueError as error:
            raise CliError(
                str(error),
                why="Snapshots should be created only after data quality checks pass.",
                next_action="Inspect data quality.",
                command=f"mft data quality {' '.join(symbols)}",
            ) from error
    payload: dict[str, Any] = asdict(result)
    payload["quality_report"] = asdict(result.quality_report)
    payload["provenance"] = asdict(result.provenance)
    return CommandOutcome(payload, status=result.quality_status)


def _next_step_for_quality(payload: dict[str, Any]) -> dict[str, Any]:
    if payload["status"] == "fail":
        symbols = " ".join(symbol["symbol"] for symbol in payload["symbols"])
        return {
            "why": "Research snapshots should not be created from stale or invalid data.",
            "next_action": "Sync market data.",
            "next_command": f"mft data sync {symbols}",
            "problem": _primary_problem(payload),
        }
    symbols = " ".join(symbol["symbol"] for symbol in payload["symbols"])
    market = _market_from_report(payload)
    start, end = _coverage_bounds(payload)
    return {
        "why": "Clean data makes dataset snapshots reproducible.",
        "next_action": "Create dataset snapshot.",
        "next_command": (
            f"mft data snapshot create {symbols} --market {market} --from {start} --to {end}"
        ),
        "problem": "Data quality checks passed.",
    }


def _primary_problem(payload: dict[str, Any]) -> str:
    for symbol in payload["symbols"]:
        if symbol.get("errors"):
            return f"{symbol['symbol']}: {'; '.join(symbol['errors'])}"
    return "Data quality checks failed."


def _market_from_report(payload: dict[str, Any]) -> str:
    symbols = payload["symbols"]
    if not symbols:
        return "US"
    asset_id = symbols[0].get("asset_id")
    if isinstance(asset_id, str) and ":" in asset_id:
        return "NSE" if "NSE" in asset_id else "US"
    return "US"


def _coverage_bounds(payload: dict[str, Any]) -> tuple[str, str]:
    timestamps = [
        ts
        for symbol in payload["symbols"]
        for ts in (symbol.get("min_timestamp"), symbol.get("max_timestamp"))
        if isinstance(ts, str) and ts
    ]
    if not timestamps:
        today = datetime.now(UTC).date().isoformat()
        return today, today
    return min(timestamps), max(timestamps)
