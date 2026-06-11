from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd


OUTPUT_COLUMNS = (
    "source_file",
    "source_family",
    "parser_kind",
    "trade_date",
    "entity",
    "category",
    "no_of_trades",
    "traded_quantity_lakh_shares",
    "turnover_crore",
    "average_daily_turnover_crore",
    "share_in_total_turnover_pct",
    "buy_value_crore",
    "sell_value_crore",
    "net_value_crore",
    "delivery_percentage",
    "source_row_index",
)


def is_delivery_positions_file(file_name: str) -> bool:
    lower = file_name.lower()
    return lower.startswith("mto_") or "delivery" in lower


def parse_delivery_positions_dat(path: Path) -> pd.DataFrame:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    trade_date = _parse_trade_date(lines)
    rows: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        record = _split_line(line, trade_date)
        if record is None:
            continue
        rows.append(
            {
                "source_file": path.name,
                "source_family": "CM - Security-wise Delivery Positions",
                "parser_kind": "delivery_positions_dat",
                "trade_date": record["trade_date"],
                "entity": record["entity"],
                "category": record["category"],
                "no_of_trades": pd.NA,
                "traded_quantity_lakh_shares": _to_lakh_shares(record["quantity"]),
                "turnover_crore": pd.NA,
                "average_daily_turnover_crore": pd.NA,
                "share_in_total_turnover_pct": pd.NA,
                "buy_value_crore": pd.NA,
                "sell_value_crore": pd.NA,
                "net_value_crore": pd.NA,
                "delivery_percentage": record["delivery_percentage"],
                "source_row_index": index,
            }
        )
    if not rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.DataFrame.from_records(rows, columns=OUTPUT_COLUMNS)


def _split_line(line: str, trade_date: str | None) -> dict[str, object] | None:
    text = line.strip()
    if not text:
        return None
    lower = text.lower()
    if lower.startswith("security wise delivery position"):
        return None
    if lower.startswith("trade date") or lower.startswith("record type") or lower.startswith("symbol"):
        return None
    if "|" in text:
        parts = [part.strip() for part in text.split("|") if part.strip()]
        if len(parts) != 4:
            return None
        return {
            "trade_date": _normalize_trade_date(parts[1]),
            "entity": parts[0],
            "category": parts[2],
            "quantity": parts[3],
            "delivery_percentage": pd.NA,
        }
    cells = [cell.strip() for cell in next(csv.reader([text], skipinitialspace=True)) if cell.strip()]
    if len(cells) < 7 or cells[0] != "20":
        return None
    return {
        "trade_date": trade_date,
        "entity": cells[2],
        "category": cells[3],
        "quantity": cells[5],
        "delivery_percentage": _to_float(cells[6]),
    }


def _parse_trade_date(lines: list[str]) -> str | None:
    for line in lines[:10]:
        match = re.search(r"Trade Date <([^>]+)>", line, flags=re.IGNORECASE)
        if match:
            return _normalize_trade_date(match.group(1))
    return None


def _normalize_trade_date(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    return None if pd.isna(parsed) else parsed.date().isoformat()


def _to_lakh_shares(value: object) -> float | None:
    parsed = pd.to_numeric(str(value).replace(",", ""), errors="coerce")
    return None if pd.isna(parsed) else float(parsed) / 100000


def _to_float(value: object) -> float | None:
    parsed = pd.to_numeric(str(value).replace(",", ""), errors="coerce")
    return None if pd.isna(parsed) else float(parsed)
