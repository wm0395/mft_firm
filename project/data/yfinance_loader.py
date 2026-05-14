from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import math
from typing import Any

from project.data.ingestion import build_raw_price_point
from project.data.repository import DataRepository
from project.data.validation import validate_historical_data


@dataclass(frozen=True)
class YFinanceAssetSpec:
    asset_symbol: str
    asset_name: str
    yahoo_symbols: tuple[str, ...]


@dataclass(frozen=True)
class YFinancePriceBatch:
    yahoo_symbol: str
    rows: tuple[tuple[datetime, float, float, float, float, float], ...]


DEFAULT_NIFTY_ASSET_SPECS = (
    YFinanceAssetSpec("NIFTY", "NIFTY 50", ("^NSEI",)),
    YFinanceAssetSpec("BANKNIFTY", "NIFTY BANK", ("^NSEBANK",)),
    YFinanceAssetSpec("FINNIFTY", "NIFTY FIN SERVICE", ("NIFTY_FIN_SERVICE.NS", "NIFTYFINSRV25_50.NS")),
    YFinanceAssetSpec("MIDCPNIFTY", "NIFTY MID SELECT", ("NIFTY_MID_SELECT.NS",)),
)


def load_default_yfinance_universe(
    repository: DataRepository,
    period: str = "6mo",
    interval: str = "1d",
) -> dict[str, object]:
    if interval != "1d":
        raise ValueError("yfinance universe loader only supports interval=1d")
    assets_loaded: list[str] = []
    rows_loaded: dict[str, int] = {}
    latest_timestamps: dict[str, str] = {}
    with repository.transaction():
        for spec in DEFAULT_NIFTY_ASSET_SPECS:
            batch = _download_price_batch(spec, period, interval)
            repository.add_asset(spec.asset_symbol, spec.asset_name, "index", "NSE")
            _ingest_price_batch(repository, spec.asset_symbol, batch)
            assets_loaded.append(spec.asset_symbol)
            rows_loaded[spec.asset_symbol] = len(batch.rows)
            latest_timestamps[spec.asset_symbol] = batch.rows[-1][0].isoformat()
    return {
        "assets": assets_loaded,
        "period": period,
        "interval": interval,
        "rows_loaded": rows_loaded,
        "latest_timestamps": latest_timestamps,
    }


def _download_price_batch(
    spec: YFinanceAssetSpec,
    period: str,
    interval: str,
) -> YFinancePriceBatch:
    try:
        import yfinance as yf  # type: ignore[import-untyped]
    except ImportError as error:
        raise RuntimeError("yfinance is required for the yfinance loader") from error
    errors: list[str] = []
    for yahoo_symbol in spec.yahoo_symbols:
        history = yf.Ticker(yahoo_symbol).history(period=period, interval=interval, auto_adjust=False)
        if getattr(history, "empty", True):
            errors.append(f"{yahoo_symbol}: no rows returned")
            continue
        rows = _history_rows(history)
        validation = validate_historical_data(list(rows))
        if validation.is_valid:
            return YFinancePriceBatch(yahoo_symbol=yahoo_symbol, rows=rows)
        errors.append(f"{yahoo_symbol}: {'; '.join(validation.errors)}")
    msg = f"yfinance returned no usable rows for {spec.asset_symbol}: {' | '.join(errors)}"
    raise ValueError(msg)


def _history_rows(history: Any) -> tuple[tuple[datetime, float, float, float, float, float], ...]:
    rows = []
    for row in history.itertuples():
        rows.append(
            (
                _normalize_timestamp(getattr(row, "Index")),
                _numeric_value(getattr(row, "Open"), "open"),
                _numeric_value(getattr(row, "High"), "high"),
                _numeric_value(getattr(row, "Low"), "low"),
                _numeric_value(getattr(row, "Close"), "close"),
                _volume_value(getattr(row, "Volume", 0.0)),
            )
        )
    return tuple(rows)


def _normalize_timestamp(value: Any) -> datetime:
    timestamp = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if not isinstance(timestamp, datetime):
        raise ValueError(f"expected datetime index, got {type(value)!r}")
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC).replace(microsecond=0)


def _numeric_value(value: Any, field_name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def _volume_value(value: Any) -> float:
    number = float(value)
    if math.isnan(number):
        return 0.0
    if not math.isfinite(number):
        raise ValueError("volume must be finite")
    return number


def _ingest_price_batch(
    repository: DataRepository,
    asset_symbol: str,
    batch: YFinancePriceBatch,
) -> None:
    asset_id = f"asset:{asset_symbol}"
    source = f"yfinance:{batch.yahoo_symbol}"
    for timestamp, open_p, high, low, close, volume in batch.rows:
        iso_timestamp = timestamp.isoformat()
        repository.ingest_raw(build_raw_price_point(asset_id, iso_timestamp, close, source))
        repository.ingest_market_data(asset_symbol, timestamp, open_p, high, low, close, volume)
