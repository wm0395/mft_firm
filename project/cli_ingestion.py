from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from project.cli_support import emit_error, emit_response
from project.data.loader import load_ohlcv_csv
from project.data.market_collector_loader import load_market_collector_ohlcv
from project.data.market_server_loader import (
    sync_market_data as sync_market_data_loader,
)
from project.data.repository import DataRepository
from project.data.snapshot_builder import (
    create_dataset_snapshot as build_dataset_snapshot,
)
from project.data.yfinance_loader import load_default_yfinance_universe


def load_yfinance_universe(
    repository: DataRepository,
    period: str,
    interval: str,
) -> int:
    try:
        payload = load_default_yfinance_universe(repository, period, interval)
    except (RuntimeError, ValueError) as error:
        emit_error("load-yfinance-universe", error)
        return 1
    emit_response("load-yfinance-universe", payload)
    return 0


def load_market_collector(
    repository: DataRepository,
    source_database: str,
    symbols: list[str],
    resolution: str,
) -> int:
    try:
        payload = load_market_collector_ohlcv(
            repository,
            Path(source_database),
            tuple(symbols),
            resolution,
        )
    except (RuntimeError, ValueError) as error:
        emit_error("load-market-collector", error)
        return 1
    emit_response("load-market-collector", payload)
    return 0


def sync_market_data_command(
    repository: DataRepository,
    symbols: list[str],
    resolution: str,
    market_db_url_env: str,
) -> int:
    try:
        payload = sync_market_data_loader(
            repository,
            tuple(symbols),
            resolution,
            market_db_url_env,
        )
    except (RuntimeError, ValueError) as error:
        emit_error("sync-market-data", error)
        return 1
    emit_response("sync-market-data", payload)
    return 0


def load_ohlcv_csv_command(
    repository: DataRepository,
    file_path: str,
    asset_symbol: str,
) -> int:
    try:
        rows_loaded = load_ohlcv_csv(Path(file_path), asset_symbol, repository)
    except (OSError, RuntimeError, ValueError) as error:
        emit_error("load-ohlcv-csv", error)
        return 1
    emit_response(
        "load-ohlcv-csv",
        {
            "asset_symbol": asset_symbol.upper(),
            "file_path": file_path,
            "rows_loaded": rows_loaded,
        },
    )
    return 0


def create_dataset_snapshot_command(
    repository: DataRepository,
    name: str,
    market: str,
    symbols: list[str],
    data_start: str,
    data_end: str,
    resolution: str,
    description: str | None,
) -> int:
    try:
        result = build_dataset_snapshot(
            repository,
            name,
            market,
            tuple(symbols),
            data_start,
            data_end,
            resolution,
            description,
        )
    except (RuntimeError, ValueError) as error:
        emit_error("create-dataset-snapshot", error)
        return 1
    emit_response("create-dataset-snapshot", asdict(result))
    return 0
