from __future__ import annotations

from dataclasses import asdict
from project.backtesting.models import BacktestConfig
from project.backtesting.research_runner import run_strategy_research
from project.cli_commands import _ensure_default_hypothesis_catalog
from project.cli.context import CLIContext, open_repository
from project.cli.errors import CliError, CommandOutcome


def run(
    context: CLIContext,
    hypothesis_id: str,
    symbol: str,
    snapshot: str,
    include_testing: bool,
    include_draft: bool,
) -> CommandOutcome:
    if not context.database.exists():
        raise CliError(
            "Database is not initialized.",
            why="Research runs require the local schema and a dataset snapshot.",
            next_action="Initialize the database.",
            command="mft setup init",
        )
    with open_repository(context.database, read_only=False) as repository:
        _ensure_default_hypothesis_catalog(repository)
        snapshot_id, start_date, end_date = _resolve_snapshot(repository, symbol, snapshot)
        try:
            result = run_strategy_research(
                repository,
                snapshot_id,
                hypothesis_id,
                symbol,
                start_date,
                end_date,
                BacktestConfig(),
                include_testing=include_testing,
                include_draft=include_draft,
            )
        except ValueError as error:
            raise CliError(
                str(error),
                why="Research runs need a valid snapshot that covers the requested symbol.",
                next_action="Create a dataset snapshot.",
                command=_snapshot_hint(repository, symbol),
            ) from error
    payload = asdict(result)
    payload["asset_symbol"] = symbol
    payload["snapshot_id"] = snapshot_id
    payload["start_date"] = start_date
    payload["end_date"] = end_date
    return CommandOutcome(payload, status="ok")


def _resolve_snapshot(
    repository,
    symbol: str,
    snapshot_selector: str,
) -> tuple[str, str, str]:
    snapshots = repository.get_dataset_snapshots()
    if snapshot_selector != "latest":
        for snapshot in snapshots:
            if snapshot.dataset_snapshot_id == snapshot_selector:
                return snapshot.dataset_snapshot_id, snapshot.data_start, snapshot.data_end
        raise CliError(
            f"Dataset snapshot {snapshot_selector} not found.",
            why="The requested research snapshot must exist before running research.",
            next_action="Create or select an existing snapshot.",
            command=_snapshot_hint(repository, symbol),
        )
    matching = [
        snapshot
        for snapshot in snapshots
        if _asset_symbol_in_snapshot(repository, snapshot.dataset_snapshot_id, symbol)
    ]
    if not matching:
        raise CliError(
            "No dataset snapshot found.",
            why="Research runs require a snapshot before a hypothesis can be evaluated.",
            next_action="Create a dataset snapshot.",
            command=_snapshot_hint(repository, symbol),
        )
    snapshot = max(matching, key=lambda item: item.captured_at)
    return snapshot.dataset_snapshot_id, snapshot.data_start, snapshot.data_end


def _asset_symbol_in_snapshot(repository, snapshot_id: str, symbol: str) -> bool:
    assets = {asset.asset_id: asset.symbol for asset in repository.list_assets()}
    for snapshot in repository.get_dataset_snapshots():
        if snapshot.dataset_snapshot_id != snapshot_id:
            continue
        return symbol.upper() in {
            assets.get(asset_id, asset_id).upper() for asset_id in snapshot.asset_ids
        }
    return False


def _snapshot_hint(repository, symbol: str) -> str:
    rows = repository.get_market_data(symbol.upper(), None, None)
    if not rows:
        return f"mft data sync {symbol.upper()}"
    start = rows[0][0].date().isoformat()
    end = rows[-1][0].date().isoformat()
    market = _asset_market(repository, symbol)
    return (
        f"mft data snapshot create {symbol.upper()} --market {market} "
        f"--from {start} --to {end}"
    )


def _asset_market(repository, symbol: str) -> str:
    for asset in repository.list_assets():
        if asset.symbol == symbol.upper():
            return asset.market
    return "US"
