from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from project.cli_operator import _doctor_payload, _schema_initialized, _workflow_status_payload
from project.cli.context import CLIContext, open_repository
from project.cli.errors import CommandOutcome


def status(context: CLIContext, show_checks: bool = False) -> CommandOutcome:
    payload = build_status_payload(context.database, show_checks=show_checks)
    return CommandOutcome(payload, status=str(payload["status"]))


def next_action(context: CLIContext) -> CommandOutcome:
    payload = build_next_payload(context.database)
    return CommandOutcome(payload, status="ok")


def build_status_payload(database: Path, show_checks: bool = False) -> dict[str, object]:
    if not database.exists():
        return _missing_database_payload(show_checks)
    with open_repository(database, read_only=True) as repository:
        if not _schema_initialized(repository):
            return _uninitialized_payload(show_checks)
        doctor = cast(dict[str, Any], _doctor_payload(repository))
        workflow = cast(dict[str, Any], _workflow_status_payload(repository))
        next_payload = build_next_payload(database)
        return {
            "status": _overall_status(str(doctor["status"]), str(workflow["database"])),
            "database_status": workflow["database"],
            "database_message": "Schema initialized",
            "market_status": _market_status(cast(tuple[dict[str, Any], ...], doctor["checks"])),
            "market_message": _market_message(cast(tuple[dict[str, Any], ...], doctor["checks"])),
            "assets": workflow["assets"],
            "snapshots": workflow["dataset_snapshots"],
            "research_runs": _completed_runs(repository),
            "draft_hypotheses": workflow["draft_hypotheses"],
            "testing_hypotheses": workflow["testing_hypotheses"],
            "active_hypotheses": workflow["active_hypotheses"],
            "checks": doctor["checks"],
            "show_checks": show_checks,
            "next_action": next_payload["next_action"],
            "next_command": next_payload["next_command"],
            "state": next_payload["state"],
        }


def build_next_payload(database: Path) -> dict[str, object]:
    if not database.exists():
        return _next_payload(
            "Database not initialized",
            "Initialize database",
            "mft setup init",
            "Create the local schema before any data workflows.",
        )
    with open_repository(database, read_only=True) as repository:
        if not _schema_initialized(repository):
            return _next_payload(
                "Database initialized, schema missing",
                "Initialize database",
                "mft setup init",
                "Create the local schema before any data workflows.",
            )
        assets = repository.list_assets()
        if not assets:
            return _next_payload(
                "No assets loaded",
                "Load market data",
                "mft data sync NIFTY RELIANCE TCS",
                "Load a first asset set before quality, snapshot, and research workflows.",
            )
        market_rows = _market_rows(repository, assets)
        if not market_rows:
            symbols = _symbol_list(assets)
            return _next_payload(
                "Assets loaded, no market rows found",
                "Sync market data",
                f"mft data sync {symbols}",
                "Market data must exist before a dataset snapshot can be created.",
            )
        snapshots = repository.get_dataset_snapshots()
        if not snapshots:
            symbols = _symbol_list(assets)
            start, end = _market_range(repository, assets)
            market = assets[0].market or "US"
            return _next_payload(
                "Data loaded, no snapshot created",
                "Create dataset snapshot",
                f"mft data snapshot create {symbols} --market {market} --from {start} --to {end}",
                "Snapshots make research reproducible and keep the workflow deterministic.",
            )
        if not repository.get_research_runs():
            symbols = _symbol_list(assets[:1])
            return _next_payload(
                "Snapshot available, no research runs completed",
                "Run research",
                f"mft research run hypothesis:rsi_mean_reversion {symbols} --snapshot latest",
                "A research run turns the snapshot into hypothesis evidence.",
            )
        if not any(item.status in {"draft", "testing"} for item in repository.get_hypotheses()):
            return _next_payload(
                "Research evidence exists, no active hypothesis workflow",
                "Check hypothesis readiness",
                "mft hypothesis check hypothesis:rsi_mean_reversion",
                "Hypotheses should be reviewed before trade ideas are surfaced.",
            )
        return _next_payload(
            "Research workflow is active",
            "Review trade ideas",
            "mft ideas review",
            "Review open trade ideas before they reach the decision layer.",
        )


def _missing_database_payload(show_checks: bool) -> dict[str, object]:
    return {
        "status": "warn",
        "database_status": "warn",
        "database_message": "Database file not found",
        "market_status": "warn",
        "market_message": "No market data database available",
        "assets": 0,
        "snapshots": 0,
        "research_runs": 0,
        "draft_hypotheses": 0,
        "testing_hypotheses": 0,
        "active_hypotheses": 0,
        "checks": (),
        "show_checks": show_checks,
        **build_next_payload(Path("__missing__")),
    }


def _uninitialized_payload(show_checks: bool) -> dict[str, object]:
    return {
        "status": "warn",
        "database_status": "warn",
        "database_message": "Schema not initialized",
        "market_status": "warn",
        "market_message": "No market data database available",
        "assets": 0,
        "snapshots": 0,
        "research_runs": 0,
        "draft_hypotheses": 0,
        "testing_hypotheses": 0,
        "active_hypotheses": 0,
        "checks": (),
        "show_checks": show_checks,
        **build_next_payload(Path("__missing__")),
    }


def _overall_status(doctor_status: object, database_status: object) -> str:
    if str(database_status) == "warn" or str(doctor_status) == "warn":
        return "warn"
    return "ok"


def _market_status(checks: tuple[dict[str, object], ...]) -> str:
    for check in checks:
        if check.get("check") in {"market_db_url", "market_raw.ohlcv_deduplicated"}:
            return str(check.get("status", "warn"))
    return "warn"


def _market_message(checks: tuple[dict[str, object], ...]) -> str:
    for check in checks:
        if check.get("check") == "market_raw.ohlcv_deduplicated" and check.get("note"):
            return str(check["note"])
        if check.get("check") == "market_db_url" and check.get("status") != "ok":
            return "MARKET_DB_URL is not set"
    return "Market data available"


def _completed_runs(repository) -> int:
    return sum(1 for run in repository.get_research_runs() if run.status == "completed")


def _market_rows(repository, assets) -> int:
    return sum(len(repository.get_market_data(asset.symbol, None, None)) for asset in assets)


def _market_range(repository, assets) -> tuple[str, str]:
    timestamps = [
        row[0]
        for asset in assets
        for row in repository.get_market_data(asset.symbol, None, None)
    ]
    if not timestamps:
        now = datetime.now(UTC).date().isoformat()
        return now, now
    start = min(timestamps).date().isoformat()
    end = max(timestamps).date().isoformat()
    return start, end


def _symbol_list(assets) -> str:
    return " ".join(asset.symbol for asset in assets)


def _next_payload(
    state: str,
    next_action: str,
    next_command: str,
    why: str,
) -> dict[str, object]:
    return {
        "state": state,
        "next_action": next_action,
        "next_command": next_command,
        "why": why,
    }
