from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

import pandas as pd


NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

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

CATEGORY_BLOCKS = (
    ("PROP", "G", "I", "J"),
    ("FIIs", "K", "L", "M"),
    ("Mutual Funds", "N", "O", "P"),
    ("Bank", "Q", "R", "S"),
    ("Insurance", "T", "U", "V"),
    ("Other DFIs", "W", "X", "Y"),
    ("NPS", "Z", "AA", "AB"),
    ("Retail", "AC", "AD", "AE"),
    ("Partnership", "AF", "AG", "AH"),
    ("Trust", "AI", "AJ", "AK"),
    ("HUF", "AL", "AM", "AN"),
    ("NRIs", "AO", "AP", "AQ"),
    ("QFIs", "AR", "AS", "AT"),
    ("Others", "AU", "AV", "AW"),
    ("Total", "AX", "AY", "AZ"),
)

MODE_BLOCKS = (
    ("Algo", "G", "P", "Y"),
    ("Non-Algo", "H", "Q", "Z"),
    ("Direct Market Access", "I", "R", "AA"),
    ("Co-location", "J", "S", "AB"),
    ("Internet Based Trading", "K", "T", "AC"),
    ("Mobile", "L", "U", "AD"),
    ("BOW/NOW", "M", "V", "AE"),
    ("Smart Order Routing", "N", "W", "AF"),
)

TOP_N_COLUMNS = ("G", "H", "I", "J", "K")


@dataclass(frozen=True)
class WorkbookData:
    sheets: dict[str, list[dict[str, object]]]


def is_capital_market_monthly_xlsx(file_name: str) -> bool:
    lower = file_name.lower()
    return lower.endswith(".xlsx") and "segment" in lower and "exchange" in lower


def parse_capital_market_monthly_xlsx(path: Path) -> pd.DataFrame:
    workbook = _read_workbook(path)
    frames = [
        _parse_category_turnover(path, workbook),
        _parse_mode_of_trading(path, workbook),
        _parse_top_n_members(path, workbook),
    ]
    records: list[dict[str, object]] = []
    for frame in frames:
        if frame.empty:
            continue
        records.extend(frame.to_dict(orient="records"))
    if not records:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)


def _parse_category_turnover(path: Path, workbook: WorkbookData) -> pd.DataFrame:
    rows = workbook.sheets.get("Category Data", [])
    records = []
    for index, row in enumerate(rows[2:], start=2):
        trade_date = _excel_date(row.get("D"))
        if trade_date is None:
            continue
        for category, buy_col, sell_col, net_col in CATEGORY_BLOCKS:
            buy_value = _to_crore(row.get(buy_col))
            sell_value = _to_crore(row.get(sell_col))
            net_value = _to_crore(row.get(net_col))
            if all(value is None for value in (buy_value, sell_value, net_value)):
                continue
            records.append(
                {
                    "source_file": path.name,
                    "source_family": "CM - Category-wise Turnover",
                    "parser_kind": "capital_market_monthly_xlsx",
                    "trade_date": trade_date,
                    "entity": _text(row.get("F")),
                    "category": category,
                    "no_of_trades": pd.NA,
                    "traded_quantity_lakh_shares": pd.NA,
                    "turnover_crore": pd.NA,
                    "average_daily_turnover_crore": pd.NA,
                    "share_in_total_turnover_pct": pd.NA,
                    "buy_value_crore": buy_value,
                    "sell_value_crore": sell_value,
                    "net_value_crore": net_value,
                    "delivery_percentage": pd.NA,
                    "source_row_index": index,
                }
            )
    return _records_to_frame(records)


def _parse_mode_of_trading(path: Path, workbook: WorkbookData) -> pd.DataFrame:
    rows = workbook.sheets.get("Mode of Trading", [])
    records = []
    for index, row in enumerate(rows[2:], start=2):
        trade_date = _excel_date(row.get("D"))
        if trade_date is None:
            continue
        for mode_name, trade_col, turnover_col, share_col in MODE_BLOCKS:
            no_of_trades = _to_int(row.get(trade_col))
            turnover_crore = _to_crore(row.get(turnover_col))
            share_pct = _to_float(row.get(share_col))
            if all(value is None for value in (no_of_trades, turnover_crore, share_pct)):
                continue
            records.append(
                {
                    "source_file": path.name,
                    "source_family": "CM - Mode of Trading",
                    "parser_kind": "capital_market_monthly_xlsx",
                    "trade_date": trade_date,
                    "entity": _text(row.get("F")),
                    "category": mode_name,
                    "no_of_trades": no_of_trades,
                    "traded_quantity_lakh_shares": pd.NA,
                    "turnover_crore": turnover_crore,
                    "average_daily_turnover_crore": pd.NA,
                    "share_in_total_turnover_pct": share_pct,
                    "buy_value_crore": pd.NA,
                    "sell_value_crore": pd.NA,
                    "net_value_crore": pd.NA,
                    "delivery_percentage": pd.NA,
                    "source_row_index": index,
                }
            )
        total_trades = _to_int(row.get("O"))
        total_turnover = _to_crore(row.get("X"))
        if not all(value is None for value in (total_trades, total_turnover)):
            records.append(
                {
                    "source_file": path.name,
                    "source_family": "CM - Mode of Trading",
                    "parser_kind": "capital_market_monthly_xlsx",
                    "trade_date": trade_date,
                    "entity": _text(row.get("F")),
                    "category": "Total",
                    "no_of_trades": total_trades,
                    "traded_quantity_lakh_shares": pd.NA,
                    "turnover_crore": total_turnover,
                    "average_daily_turnover_crore": pd.NA,
                    "share_in_total_turnover_pct": 100.0,
                    "buy_value_crore": pd.NA,
                    "sell_value_crore": pd.NA,
                    "net_value_crore": pd.NA,
                    "delivery_percentage": pd.NA,
                    "source_row_index": index,
                }
            )
    return _records_to_frame(records)


def _parse_top_n_members(path: Path, workbook: WorkbookData) -> pd.DataFrame:
    rows = workbook.sheets.get("Top N Members", [])
    records = []
    for index, row in enumerate(rows[2:], start=2):
        trade_date = _excel_date(row.get("D"))
        if trade_date is None:
            continue
        turnover_crore = _to_crore(row.get("L"))
        for label, column in zip(("5", "10", "25", "50", "100"), TOP_N_COLUMNS, strict=True):
            share_pct = _to_float(row.get(column))
            if share_pct is None and turnover_crore is None:
                continue
            records.append(
                {
                    "source_file": path.name,
                    "source_family": "Segment-wise Historical Reports - Capital Market",
                    "parser_kind": "capital_market_monthly_xlsx",
                    "trade_date": trade_date,
                    "entity": _text(row.get("F")),
                    "category": f"top_{label}",
                    "no_of_trades": pd.NA,
                    "traded_quantity_lakh_shares": pd.NA,
                    "turnover_crore": turnover_crore,
                    "average_daily_turnover_crore": pd.NA,
                    "share_in_total_turnover_pct": share_pct,
                    "buy_value_crore": pd.NA,
                    "sell_value_crore": pd.NA,
                    "net_value_crore": pd.NA,
                    "delivery_percentage": pd.NA,
                    "source_row_index": index,
                }
            )
    return _records_to_frame(records)


def _records_to_frame(records: list[dict[str, object]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)


def _read_workbook(path: Path) -> WorkbookData:
    with ZipFile(path) as zf:
        shared_strings = _read_shared_strings(zf)
        sheet_map = _sheet_map(zf)
        sheets = {
            name: _read_sheet_rows(zf, sheet_path, shared_strings)
            for name, sheet_path in sheet_map.items()
        }
    return WorkbookData(sheets=sheets)


def _read_shared_strings(zf: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    return ["".join(text.text or "" for text in item.findall(".//a:t", NS)) for item in root.findall("a:si", NS)]


def _sheet_map(zf: ZipFile) -> dict[str, str]:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    mapping: dict[str, str] = {}
    sheets = workbook.find("a:sheets", NS)
    if sheets is None:
        return mapping
    for sheet in sheets:
        rid = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        target = rel_map[rid]
        mapping[sheet.attrib["name"]] = target if target.startswith("xl/") else f"xl/{target}"
    return mapping


def _read_sheet_rows(zf: ZipFile, sheet_path: str, shared_strings: list[str]) -> list[dict[str, object]]:
    root = ET.fromstring(zf.read(sheet_path))
    rows: list[dict[str, object]] = []
    for row in root.findall(".//a:sheetData/a:row", NS):
        rows.append(_read_row(row, shared_strings))
    return rows


def _read_row(row: ET.Element, shared_strings: list[str]) -> dict[str, object]:
    values: dict[str, object] = {}
    for cell in row.findall("a:c", NS):
        ref = cell.attrib.get("r", "")
        value = _cell_value(cell, shared_strings)
        if ref:
            values[_column_letters(ref)] = value
    return values


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> object:
    kind = cell.attrib.get("t")
    raw = cell.findtext("a:v", default="", namespaces=NS)
    if kind == "s" and raw.isdigit():
        return shared_strings[int(raw)] if int(raw) < len(shared_strings) else ""
    if kind == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(".//a:t", NS))
    return raw


def _column_letters(cell_ref: str) -> str:
    return "".join(character for character in cell_ref if character.isalpha())


def _excel_date(value: object) -> str | None:
    number = _to_float(value)
    if number is None or not pd.notna(number):
        return None
    base = datetime(1899, 12, 30)
    return (base + timedelta(days=number)).date().isoformat()


def _to_crore(value: object) -> float | None:
    number = _to_float(value)
    return None if number is None else float(number) / 10_000_000.0


def _to_int(value: object) -> int | None:
    number = _to_float(value)
    return None if number is None else int(number)


def _to_float(value: object) -> float | None:
    text = _text(value)
    if text in {"", "-"}:
        return None
    cleaned = text.replace(",", "")
    parsed = pd.to_numeric(cleaned, errors="coerce")
    return None if pd.isna(parsed) else float(parsed)


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
