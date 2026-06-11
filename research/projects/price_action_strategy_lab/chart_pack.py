from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd

from project.ui.components.trading_view_chart import trading_view_chart


@dataclass(frozen=True)
class ChartSignal:
    date: datetime
    symbol: str
    signal_name: str
    side: str
    reason_code: str


@dataclass(frozen=True)
class ChartPackConfig:
    symbol: str
    output_dir: Path
    title: str = "Price Action Research Chart"


@dataclass(frozen=True)
class ChartPackResult:
    symbol: str
    html_path: Path
    signal_path: Path
    signal_count: int


def generate_chart_pack(
    ohlcv: pd.DataFrame,
    signals: tuple[ChartSignal, ...],
    config: ChartPackConfig,
) -> ChartPackResult:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    symbol_signals = tuple(item for item in signals if item.symbol == config.symbol)
    html_path = config.output_dir / f"{config.symbol}_chart.html"
    signal_path = config.output_dir / f"{config.symbol}_signals.csv"
    _write_signals(symbol_signals, signal_path)
    html_path.write_text(_chart_page(ohlcv, symbol_signals, config), encoding="utf-8")
    return ChartPackResult(
        symbol=config.symbol,
        html_path=html_path,
        signal_path=signal_path,
        signal_count=len(symbol_signals),
    )


def signals_from_positions(
    positions: pd.DataFrame,
    signal_name: str,
    reason_code: pd.Series,
) -> tuple[ChartSignal, ...]:
    rows: list[ChartSignal] = []
    for timestamp, row in positions.iterrows():
        active = row[row.ne(0.0)]
        for symbol, weight in active.items():
            rows.append(_chart_signal(timestamp, symbol, float(weight), signal_name, reason_code))
    return tuple(rows)


def _chart_signal(
    timestamp: object,
    symbol: object,
    weight: float,
    signal_name: str,
    reason_code: pd.Series,
) -> ChartSignal:
    date = pd.Timestamp(timestamp).to_pydatetime()
    side = "long" if weight > 0.0 else "short"
    reason = str(reason_code.get(timestamp, "active"))
    return ChartSignal(date, str(symbol), signal_name, side, reason)


def _chart_page(
    ohlcv: pd.DataFrame,
    signals: tuple[ChartSignal, ...],
    config: ChartPackConfig,
) -> str:
    chart = trading_view_chart(_ohlcv_rows(ohlcv))
    return "".join(
        [
            "<!doctype html><html><head><meta charset='utf-8'>",
            f"<title>{escape(config.title)} - {escape(config.symbol)}</title>",
            "</head><body style='font-family:ui-sans-serif,system-ui;padding:24px;'>",
            f"<h1>{escape(config.symbol)}</h1>",
            chart,
            _signal_table(signals),
            "</body></html>",
        ]
    )


def _ohlcv_rows(
    ohlcv: pd.DataFrame,
) -> list[tuple[datetime, float, float, float, float, float]]:
    rows = []
    for timestamp, row in ohlcv.iterrows():
        rows.append(
            (
                pd.Timestamp(timestamp).to_pydatetime(),
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                float(row["volume"]),
            )
        )
    return rows


def _write_signals(signals: tuple[ChartSignal, ...], path: Path) -> None:
    rows = [
        {
            "date": item.date.date().isoformat(),
            "symbol": item.symbol,
            "signal_name": item.signal_name,
            "side": item.side,
            "reason_code": item.reason_code,
        }
        for item in signals
    ]
    pd.DataFrame(rows).to_csv(path, index=False)


def _signal_table(signals: tuple[ChartSignal, ...]) -> str:
    if not signals:
        return "<h2>Signals</h2><p>No active signals.</p>"
    rows = "".join(_signal_row(signal) for signal in signals)
    return f"<h2>Signals</h2><table><tbody>{rows}</tbody></table>"


def _signal_row(signal: ChartSignal) -> str:
    return "".join(
        [
            "<tr>",
            f"<td>{escape(signal.date.date().isoformat())}</td>",
            f"<td>{escape(signal.signal_name)}</td>",
            f"<td>{escape(signal.side)}</td>",
            f"<td>{escape(signal.reason_code)}</td>",
            "</tr>",
        ]
    )
