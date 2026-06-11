from __future__ import annotations

import csv
import re
from datetime import datetime
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

SUMMARY_LABELS = {
    "tradedvaluersincrores": "turnover_crore",
    "tradedquantityinlakhs": "traded_quantity_lakh_shares",
    "numberoftrades": "no_of_trades",
    "totalmarketcapitalisationrscrores": "market_cap_crore",
}


def is_market_activity_file(file_name: str) -> bool:
    lower = file_name.lower()
    return lower.endswith(".csv") and (
        lower.startswith("ma") or "business" in lower or "marketactivity" in lower
    )


def parse_market_activity_csv(path: Path) -> pd.DataFrame:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if _has_sectioned_layout(lines):
        return _parse_sectioned_market_activity(path, lines)
    return _parse_flat_market_activity(path)


def _parse_flat_market_activity(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    renamed = _rename_columns(
        frame,
        {
            "security": "entity",
            "nooftrades": "no_of_trades",
            "tradedquantitylakhshares": "traded_quantity_lakh_shares",
            "turnovercr": "turnover_crore",
            "averagedailyturnovercr": "average_daily_turnover_crore",
            "shareintotalturnover": "share_in_total_turnover_pct",
        },
    )
    source_family = (
        "Business Growth Data across all segments"
        if "business" in path.stem.lower()
        else "CM - Market Activity Report"
    )
    trade_date = _parse_report_date_from_filename(path.name)
    out = renamed.assign(
        source_file=path.name,
        source_family=source_family,
        parser_kind="market_activity_csv",
        trade_date=trade_date,
        category=None,
        buy_value_crore=pd.NA,
        sell_value_crore=pd.NA,
        net_value_crore=pd.NA,
        delivery_percentage=pd.NA,
    )
    out["source_row_index"] = range(len(out))
    return out[list(OUTPUT_COLUMNS)]


def _parse_sectioned_market_activity(path: Path, lines: list[str]) -> pd.DataFrame:
    trade_date = _parse_trade_date(lines)
    metrics = _parse_summary_metrics(lines)
    summary_turnover = metrics.get("turnover_crore")
    records: list[dict[str, object]] = []
    if trade_date:
        records.append(_summary_record(path, trade_date, metrics))
    records.extend(_parse_security_rows(path, lines, trade_date, summary_turnover))
    top_25 = _parse_top_25_aggregate(path, lines, trade_date, summary_turnover)
    if top_25 is not None:
        if records:
            records.insert(1, top_25)
        else:
            records.append(top_25)
    return _records_to_frame(records)


def _summary_record(
    path: Path,
    trade_date: str | None,
    metrics: dict[str, object],
) -> dict[str, object]:
    return {
        "source_file": path.name,
        "source_family": "Business Growth Data across all segments"
        if "business" in path.stem.lower()
        else "CM - Market Activity Report",
        "parser_kind": "market_activity_csv",
        "trade_date": trade_date,
        "entity": "__market__",
        "category": "summary",
        "no_of_trades": metrics.get("no_of_trades"),
        "traded_quantity_lakh_shares": metrics.get("traded_quantity_lakh_shares"),
        "turnover_crore": metrics.get("turnover_crore"),
        "average_daily_turnover_crore": pd.NA,
        "share_in_total_turnover_pct": 100.0
        if metrics.get("turnover_crore") is not None
        else pd.NA,
        "buy_value_crore": pd.NA,
        "sell_value_crore": pd.NA,
        "net_value_crore": pd.NA,
        "delivery_percentage": pd.NA,
        "source_row_index": 0,
    }


def _parse_summary_metrics(lines: list[str]) -> dict[str, object]:
    metrics: dict[str, object] = {}
    for line in lines[:20]:
        cells = _csv_cells(line)
        if len(cells) < 2:
            continue
        key = _canonical_key(cells[0])
        if key in SUMMARY_LABELS:
            label = SUMMARY_LABELS[key]
            if label == "no_of_trades":
                metrics[label] = _to_int(cells[-1])
            else:
                metrics[label] = _to_float(cells[-1])
    return metrics


def _parse_security_rows(
    path: Path,
    lines: list[str],
    trade_date: str | None,
    summary_turnover: object,
) -> list[dict[str, object]]:
    start = _find_line(lines, "Securities Price Volume Data in Normal market")
    if start is None:
        return []
    records: list[dict[str, object]] = []
    for index, line in enumerate(lines[start + 1 :], start=start + 1):
        if not line.strip():
            break
        if _canonical_key(line).startswith("topfive"):
            break
        cells = _csv_cells(line)
        if len(cells) < 5 or _canonical_key(cells[0]) == "symbol":
            continue
        turnover_crore = _to_crore(cells[3])
        traded_quantity = _to_lakh_shares(cells[4])
        records.append(
            {
                "source_file": path.name,
                "source_family": "CM - Market Activity Report",
                "parser_kind": "market_activity_csv",
                "trade_date": trade_date,
                "entity": cells[0],
                "category": cells[1],
                "no_of_trades": pd.NA,
                "traded_quantity_lakh_shares": traded_quantity,
                "turnover_crore": turnover_crore,
                "average_daily_turnover_crore": pd.NA,
                "share_in_total_turnover_pct": _share_pct(
                    turnover_crore,
                    summary_turnover,
                ),
                "buy_value_crore": pd.NA,
                "sell_value_crore": pd.NA,
                "net_value_crore": pd.NA,
                "delivery_percentage": pd.NA,
                "source_row_index": index,
            }
        )
    return records


def _parse_top_25_aggregate(
    path: Path,
    lines: list[str],
    trade_date: str | None,
    summary_turnover: object,
) -> dict[str, object] | None:
    start = _find_line(lines, "TOP 25 Securities Today")
    if start is None:
        return None
    total_turnover = 0.0
    seen = 0
    for line in lines[start + 1 :]:
        if not line.strip():
            break
        if _canonical_key(line).startswith("topfive"):
            break
        cells = _csv_cells(line)
        if len(cells) < 6 or _canonical_key(cells[0]) == "symbol":
            continue
        value = _to_float(cells[-1])
        if value is None:
            continue
        total_turnover += value
        seen += 1
    if seen == 0:
        return None
    return {
        "source_file": path.name,
        "source_family": "CM - Market Activity Report",
        "parser_kind": "market_activity_csv",
        "trade_date": trade_date,
        "entity": "__market__",
        "category": "top_25",
        "no_of_trades": pd.NA,
        "traded_quantity_lakh_shares": pd.NA,
        "turnover_crore": total_turnover,
        "average_daily_turnover_crore": pd.NA,
        "share_in_total_turnover_pct": _share_pct(total_turnover, summary_turnover),
        "buy_value_crore": pd.NA,
        "sell_value_crore": pd.NA,
        "net_value_crore": pd.NA,
        "delivery_percentage": pd.NA,
        "source_row_index": start,
    }


def _has_sectioned_layout(lines: list[str]) -> bool:
    return any(
        "Securities Price Volume Data in Normal market".lower() in line.lower()
        for line in lines
    )


def _records_to_frame(records: list[dict[str, object]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)


def _csv_cells(line: str) -> list[str]:
    return [cell.strip() for cell in next(csv.reader([line], skipinitialspace=True)) if cell.strip()]


def _find_line(lines: list[str], marker: str) -> int | None:
    needle = marker.lower()
    for index, line in enumerate(lines):
        if needle in line.lower():
            return index
    return None


def _parse_trade_date(lines: list[str]) -> str | None:
    for line in lines[:5]:
        cells = _csv_cells(line)
        if not cells:
            continue
        parsed = pd.to_datetime(cells[0], errors="coerce", dayfirst=True)
        if pd.isna(parsed):
            continue
        return parsed.date().isoformat()
    return None


def _rename_columns(frame: pd.DataFrame, target_names: dict[str, str]) -> pd.DataFrame:
    columns = {_canonical_key(column): column for column in frame.columns}
    missing = [key for key in target_names if key not in columns]
    if missing:
        raise ValueError(f"missing expected columns: {missing}")
    rename_map = {columns[key]: target_name for key, target_name in target_names.items()}
    return frame.rename(columns=rename_map)


def _parse_report_date_from_filename(file_name: str) -> str | None:
    match = re.search(r"(\d{6})", file_name)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%d%m%y").date().isoformat()
    except ValueError:
        return None


def _to_float(value: object) -> float | None:
    parsed = pd.to_numeric(str(value).replace(",", ""), errors="coerce")
    return None if pd.isna(parsed) else float(parsed)


def _to_int(value: object) -> int | None:
    parsed = pd.to_numeric(str(value).replace(",", ""), errors="coerce")
    return None if pd.isna(parsed) else int(parsed)


def _to_crore(value: object) -> float | None:
    parsed = _to_float(value)
    return None if parsed is None else parsed / 10000000


def _to_lakh_shares(value: object) -> float | None:
    parsed = pd.to_numeric(str(value).replace(",", ""), errors="coerce")
    return None if pd.isna(parsed) else float(parsed) / 100000


def _canonical_key(text: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def _share_pct(value: object, total: object) -> object:
    parsed_value = _to_float(value)
    parsed_total = _to_float(total)
    if parsed_value is None or parsed_total is None:
        return pd.NA
    if parsed_total == 0:
        return pd.NA
    return parsed_value / parsed_total * 100
