from __future__ import annotations

import os
from typing import Any, cast

from project.cli_support import emit_response
from project.data.repository import DataRepository
from project.data.schema import REQUIRED_TABLES


def doctor(repository: DataRepository) -> int:
    result = _doctor_payload(repository)
    emit_response("doctor", result, status=cast(str, result["status"]))
    return 0


def workflow_status(repository: DataRepository) -> int:
    result = _workflow_status_payload(repository)
    emit_response(
        "workflow-status",
        result,
        status=cast(str, result["database"]),
    )
    return 0


def next_steps(repository: DataRepository) -> int:
    emit_response("next-steps", {"steps": _next_steps_payload()})
    return 0


def _doctor_payload(repository: DataRepository) -> dict[str, object]:
    checks = _doctor_checks(repository)
    status = (
        "fail"
        if any(check["status"] == "fail" for check in checks)
        else "warn"
        if any(check["status"] == "warn" for check in checks)
        else "ok"
    )
    return {"status": status, "checks": checks}


def _doctor_checks(repository: DataRepository) -> list[dict[str, object]]:
    return [
        {
            "check": "schema_initialized",
            "status": "ok" if _schema_initialized(repository) else "fail",
        },
        {"check": "assets", **_count_check(repository, "assets")},
        {"check": "raw_market_data", **_count_check(repository, "raw_market_data")},
        {"check": "raw_data", **_count_check(repository, "raw_data")},
        {"check": "signals", **_count_check(repository, "signals")},
        {"check": "hypotheses", **_count_check(repository, "hypotheses")},
        {
            "check": "signal_registry",
            **_count_check(repository, "signal_registry"),
        },
        {
            "check": "dataset_snapshots",
            **_count_check(repository, "dataset_snapshots"),
        },
        *_market_server_checks(),
    ]


def _count_check(repository: DataRepository, table_name: str) -> dict[str, object]:
    count = _table_count(repository, table_name)
    return {"status": "ok" if count else "warn", "count": count}


def _workflow_status_payload(repository: DataRepository) -> dict[str, object]:
    hypotheses = repository.get_hypotheses()
    backtests = repository.get_backtest_results()
    research_runs = repository.get_research_runs()
    return {
        "database": "ok" if _schema_initialized(repository) else "warn",
        "assets": len(repository.list_assets()),
        "market_data_rows": _table_count(repository, "raw_market_data"),
        "dataset_snapshots": len(repository.get_dataset_snapshots()),
        "active_hypotheses": sum(1 for item in hypotheses if item.status == "active"),
        "testing_hypotheses": sum(1 for item in hypotheses if item.status == "testing"),
        "draft_hypotheses": sum(1 for item in hypotheses if item.status == "draft"),
        "latest_backtest": backtests[-1].__dict__ if backtests else None,
        "latest_research_run": research_runs[-1].__dict__ if research_runs else None,
        "next_recommended_command": _suggest_next_command(repository),
    }


def _next_steps_payload() -> list[dict[str, str]]:
    return [
        {"command": "init-db", "description": "Initialize or refresh the local schema"},
        {
            "command": "sync-market-data",
            "description": "Sync canonical market rows from Postgres",
        },
        {
            "command": "data-quality-report",
            "description": "Inspect data quality before snapshotting",
        },
        {
            "command": "create-dataset-snapshot",
            "description": "Create a reproducible research snapshot",
        },
        {
            "command": "run-strategy-research",
            "description": "Run the deterministic research batch",
        },
        {"command": "hypothesis-readiness", "description": "Check promotion readiness"},
        {
            "command": "promote-hypothesis",
            "description": "Move a hypothesis to the next status",
        },
    ]


def _suggest_next_command(repository: DataRepository) -> str:
    if not _schema_initialized(repository):
        return "init-db"
    if not repository.list_assets():
        return "sync-market-data"
    if not repository.get_dataset_snapshots():
        return "create-dataset-snapshot"
    if not repository.get_research_runs():
        return "run-strategy-research"
    return "hypothesis-readiness"


def _schema_initialized(repository: DataRepository) -> bool:
    tables = {row[0] for row in repository._db.fetch_all("show tables")}
    return REQUIRED_TABLES.issubset(tables)


def _table_count(repository: DataRepository, table_name: str) -> int:
    rows = repository._db.fetch_all(f"select count(*) from {table_name}")
    return int(rows[0][0]) if rows else 0


def _market_server_checks() -> list[dict[str, object]]:
    env_value = os.environ.get("MARKET_DB_URL")
    if not env_value:
        return [
            {"check": "market_db_url", "status": "warn"},
            {
                "check": "market_raw.ohlcv_deduplicated",
                "status": "warn",
                "note": "MARKET_DB_URL is not set",
            },
        ]
    psycopg = _import_psycopg()
    if psycopg is None:
        return [
            {"check": "market_db_url", "status": "warn"},
            {
                "check": "market_raw.ohlcv_deduplicated",
                "status": "warn",
                "note": "psycopg is not installed",
            },
        ]
    connection = _connect_psycopg(psycopg, env_value)
    if connection is None:
        return [
            {"check": "market_db_url", "status": "fail"},
            {
                "check": "market_raw.ohlcv_deduplicated",
                "status": "fail",
                "note": "Postgres connection failed",
            },
        ]
    try:
        relation_status = _market_relation_status(connection)
        return [
            {"check": "market_db_url", "status": "ok"},
            {"check": "market_raw.ohlcv_deduplicated", "status": relation_status},
        ]
    finally:
        connection.close()


def _import_psycopg() -> Any | None:
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError:
        return None
    return psycopg


def _connect_psycopg(psycopg: Any, env_value: str) -> Any | None:
    try:
        return psycopg.connect(env_value)
    except Exception:
        return None


def _market_relation_status(connection: Any) -> str:
    row = connection.execute(
        """
        select 1
        from information_schema.tables
        where table_schema = %s and table_name = %s
        """,
        ("market_raw", "ohlcv_deduplicated"),
    ).fetchone()
    return "ok" if row is not None else "fail"
