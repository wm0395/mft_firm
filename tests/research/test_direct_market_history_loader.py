from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
from zipfile import ZipFile
from xml.sax.saxutils import escape

import pandas as pd
import pytest

from research.projects.ipo_liquidity_pressure.direct_market_history_loader import (
    build_collection_manifest,
    load_direct_market_history_directory,
)


def test_direct_market_history_loader_manifest_and_parsers(tmp_path: Path) -> None:
    manifest = build_collection_manifest()
    assert len(manifest) == 10
    assert set(manifest["parser_status"]) == {"parser_ready", "manifest_only"}
    assert any(
        row["family"] == "CM - Market Activity Report"
        and row["parser_kind"] == "market_activity_csv"
        and row["parser_status"] == "parser_ready"
        for _, row in manifest.iterrows()
    )
    assert any(
        row["family"] == "Historical FII/FPI & DII trading activity on NSE, BSE and MSEI"
        and row["parser_kind"] == "fii_dii_csv"
        and row["parser_status"] == "parser_ready"
        for _, row in manifest.iterrows()
    )
    assert any(
        row["family"] == "Security-wise Price Volume Archives (Equities)"
        and row["parser_kind"] == "security_price_volume_csv"
        and row["parser_status"] == "parser_ready"
        for _, row in manifest.iterrows()
    )
    assert any(
        row["family"] == "Segment-wise Historical Reports - Capital Market"
        and row["parser_kind"] == "capital_market_monthly_xlsx"
        and row["parser_status"] == "parser_ready"
        for _, row in manifest.iterrows()
    )
    assert any(
        row["family"] == "CM - Category-wise Turnover"
        and row["parser_kind"] == "capital_market_monthly_xlsx"
        and row["parser_status"] == "parser_ready"
        for _, row in manifest.iterrows()
    )
    assert any(
        row["family"] == "CM - Mode of Trading"
        and row["parser_kind"] == "capital_market_monthly_xlsx"
        and row["parser_status"] == "parser_ready"
        for _, row in manifest.iterrows()
    )
    assert any(
        row["family"] == "Historical Reports - Capital Market"
        and row["parser_status"] == "manifest_only"
        for _, row in manifest.iterrows()
    )

    (tmp_path / "MA210526.csv").write_text(
        "\n".join(
            [
                "Security,No. of Trades,Traded Quantity (Lakh Shares),Turnover ( cr.),Average Daily Turnover ( cr.),Share in Total Turnover (%)",
                "Reliance Industries Ltd,3645395,1527,17037.47,851.87,2.84",
                "Yes Bank Limited,5903292,10943,19473.09,973.65,3.25",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "MA250924.csv").write_text(
        "\n".join(
            [
                ",25-Sep-2024",
                "The Nifty witnessed an intraday movement of about 161.45 points.",
                ", Traded Value (Rs. In Crores), 109967",
                ", Traded Quantity (in Lakhs), 49273.52",
                ", Number of Trades, 37853323",
                ", Total Market Capitalisation (Rs. Crores), 47127809.99",
                "",
                ",Securities Price Volume Data in Normal market",
                ",SYMBOL,SERIES,CLOSE PRICE,TRADED VALUE ,TRADED QUANTITY",
                ",20MICRONS,EQ,310.55,90374070.70,291221",
                ",3MINDIA,EQ,35216.15,150414989.10,4275",
                "",
                ",TOP 25 Securities Today :",
                ",SYMBOL,SERIES,PREV. CLOSE,CLOSE PRICE,%VAR, VALUE(Rs Crs)",
                ",EASEMYTRIP,EQ,40.98,34.32,-16.25,3027.7",
                ",HDFCBANK,EQ,1768.05,1779.10,0.62,2843.26",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "business_growth_160526.csv").write_text(
        "\n".join(
            [
                "Security,No. of Trades,Traded Quantity (Lakh Shares),Turnover ( cr.),Average Daily Turnover ( cr.),Share in Total Turnover (%)",
                "State Bank Of India,2380250,3209,11335.61,566.78,1.89",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "historical_fii_dii_20260520.csv").write_text(
        "\n".join(
            [
                "Category,Date,Buy Value(₹ Crores),Sell Value (₹ Crores),Net Value (₹ Crores)",
                "DII,20-May-2026,14045.18,12705.93,1339.25",
                "FII/FPI,20-May-2026,13179.93,14106.08,-926.15",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "MTO_21052026.DAT").write_text(
        "\n".join(
            [
                "Symbol | Date | Security Name | Quantity",
                "SBIN | 13-Jun-2018 | STATE BANK OF INDIA | 360000",
                "RELIANCE | 30-Jul-2018 | RELIANCE INDUSTRIES LIMITED | 279000",
            ]
        ),
        encoding="utf-8",
    )
    _write_capital_market_monthly_workbook(
        tmp_path / "Exchange_Data_CM_Segment_20260512103333.xlsx",
    )
    (tmp_path / "eq_security_sbin.csv").write_text(
        "\n".join(
            [
                "Symbol,Series,Date,Prev Close,Open Price,High Price,Low Price,Close Price,Total Traded Quantity,Total Traded Value in Rs.",
                "SBIN,EQ,20-May-2026,820.10,821.00,835.00,815.00,830.00,100000,10000000",
                "RELIANCE,EQ,20-May-2026,2500.00,2510.00,2525.00,2490.00,2515.00,250000,25000000",
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_direct_market_history_directory(tmp_path).sort_values(
        ["source_file", "source_row_index", "category"]
    )
    assert len(loaded) == 29
    assert set(loaded["parser_kind"]) == {
        "market_activity_csv",
        "fii_dii_csv",
        "security_price_volume_csv",
        "delivery_positions_dat",
        "capital_market_monthly_xlsx",
    }
    assert set(loaded["source_family"]) == {
        "Business Growth Data across all segments",
        "CM - Market Activity Report",
        "CM - Category-wise Turnover",
        "CM - Mode of Trading",
        "CM - Security-wise Delivery Positions",
        "Security-wise Price Volume Archives (Equities)",
        "Historical FII/FPI & DII trading activity on NSE, BSE and MSEI",
        "Segment-wise Historical Reports - Capital Market",
    }

    ma_row = loaded.loc[loaded["source_file"] == "MA210526.csv"].iloc[0]
    assert ma_row["trade_date"] == "2026-05-21"
    assert ma_row["entity"] == "Reliance Industries Ltd"
    assert ma_row["no_of_trades"] == 3645395
    assert ma_row["turnover_crore"] == 17037.47

    sectioned_summary_row = loaded.loc[
        (loaded["source_file"] == "MA250924.csv") & (loaded["category"] == "summary")
    ].iloc[0]
    assert sectioned_summary_row["trade_date"] == "2024-09-25"
    assert sectioned_summary_row["entity"] == "__market__"
    assert sectioned_summary_row["no_of_trades"] == 37853323
    assert sectioned_summary_row["turnover_crore"] == 109967.0

    sectioned_security_row = loaded.loc[
        (loaded["source_file"] == "MA250924.csv")
        & (loaded["category"] == "EQ")
        & (loaded["entity"] == "20MICRONS")
    ].iloc[0]
    assert sectioned_security_row["trade_date"] == "2024-09-25"
    assert sectioned_security_row["traded_quantity_lakh_shares"] == 2.91221
    assert sectioned_security_row["turnover_crore"] == pytest.approx(9.03740707)
    assert sectioned_security_row["share_in_total_turnover_pct"] == pytest.approx(
        0.008218290096119745
    )

    top_25_row = loaded.loc[
        (loaded["source_file"] == "MA250924.csv") & (loaded["category"] == "top_25")
    ].iloc[0]
    assert top_25_row["trade_date"] == "2024-09-25"
    assert top_25_row["entity"] == "__market__"
    assert top_25_row["turnover_crore"] == pytest.approx(5870.96)

    fii_row = loaded.loc[loaded["source_file"] == "historical_fii_dii_20260520.csv"].iloc[0]
    assert fii_row["trade_date"] == "2026-05-20"
    assert fii_row["category"] == "DII"
    assert fii_row["buy_value_crore"] == 14045.18
    assert pd.isna(fii_row["turnover_crore"])

    security_row = loaded.loc[loaded["source_file"] == "eq_security_sbin.csv"].iloc[0]
    assert security_row["trade_date"] == "2026-05-20"
    assert security_row["entity"] == "SBIN"
    assert security_row["category"] == "EQ"
    assert security_row["traded_quantity_lakh_shares"] == 1.0
    assert security_row["turnover_crore"] == 1.0
    assert pd.isna(security_row["no_of_trades"])

    delivery_row = loaded.loc[loaded["source_file"] == "MTO_21052026.DAT"].iloc[0]
    assert delivery_row["trade_date"] == "2018-06-13"
    assert delivery_row["entity"] == "SBIN"
    assert delivery_row["category"] == "STATE BANK OF INDIA"
    assert delivery_row["traded_quantity_lakh_shares"] == 3.6
    assert pd.isna(delivery_row["turnover_crore"])

    category_row = loaded.loc[
        (loaded["source_file"] == "Exchange_Data_CM_Segment_20260512103333.xlsx")
        & (loaded["source_family"] == "CM - Category-wise Turnover")
        & (loaded["category"] == "PROP")
    ].iloc[0]
    assert category_row["trade_date"] == "2026-04-01"
    assert category_row["entity"] == "Equity Segment"
    assert category_row["buy_value_crore"] == 1.0
    assert category_row["sell_value_crore"] == 2.0
    assert category_row["net_value_crore"] == 1.0

    mode_row = loaded.loc[
        (loaded["source_file"] == "Exchange_Data_CM_Segment_20260512103333.xlsx")
        & (loaded["source_family"] == "CM - Mode of Trading")
        & (loaded["category"] == "Algo")
    ].iloc[0]
    assert mode_row["trade_date"] == "2026-04-01"
    assert mode_row["no_of_trades"] == 10
    assert mode_row["turnover_crore"] == 1.0
    assert mode_row["share_in_total_turnover_pct"] == 10.0

    total_mode_row = loaded.loc[
        (loaded["source_file"] == "Exchange_Data_CM_Segment_20260512103333.xlsx")
        & (loaded["source_family"] == "CM - Mode of Trading")
        & (loaded["category"] == "Total")
    ].iloc[0]
    assert total_mode_row["no_of_trades"] == 280
    assert total_mode_row["turnover_crore"] == 28.0
    assert total_mode_row["share_in_total_turnover_pct"] == 100.0

    top_n_row = loaded.loc[
        (loaded["source_file"] == "Exchange_Data_CM_Segment_20260512103333.xlsx")
        & (loaded["source_family"] == "Segment-wise Historical Reports - Capital Market")
        & (loaded["category"] == "top_5")
    ].iloc[0]
    assert top_n_row["trade_date"] == "2026-04-01"
    assert top_n_row["share_in_total_turnover_pct"] == 11.0
    assert top_n_row["turnover_crore"] == 1.0


def _write_capital_market_monthly_workbook(path: Path) -> None:
    sheets = {
        "Category Data": [
            {},
            {},
            {
                "D": 46113,
                "F": "Equity Segment",
                "G": 10000000,
                "I": 20000000,
                "J": 10000000,
                "K": 30000000,
                "L": 12000000,
                "M": 18000000,
                "AX": 70000000,
                "AY": 65000000,
                "AZ": 5000000,
            },
        ],
        "Mode of Trading": [
            {},
            {},
            {
                "D": 46113,
                "F": "Equity Segment",
                "G": 10,
                "H": 20,
                "I": 30,
                "J": 40,
                "K": 50,
                "L": 60,
                "M": "-",
                "N": 70,
                "O": 280,
                "P": 10000000,
                "Q": 20000000,
                "R": 30000000,
                "S": 40000000,
                "T": 50000000,
                "U": 60000000,
                "V": "-",
                "W": 70000000,
                "X": 280000000,
                "Y": 10.0,
                "Z": 20.0,
                "AA": 30.0,
                "AB": 40.0,
                "AC": 50.0,
                "AD": 60.0,
                "AE": "-",
                "AF": 70.0,
            },
        ],
        "Top N Members": [
            {},
            {},
            {
                "D": 46113,
                "F": "Equity Segment",
                "G": 11.0,
                "H": 22.0,
                "I": 33.0,
                "J": 44.0,
                "K": 55.0,
                "L": 10000000,
            },
        ],
    }
    _write_xlsx(path, sheets)


def _write_xlsx(path: Path, sheets: Mapping[str, list[dict[str, Any]]]) -> None:
    strings = _collect_shared_strings(sheets)
    with ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", _content_types(list(sheets)))
        zf.writestr("_rels/.rels", _root_rels())
        zf.writestr("xl/workbook.xml", _workbook_xml(list(sheets)))
        zf.writestr("xl/_rels/workbook.xml.rels", _workbook_rels(list(sheets)))
        zf.writestr("xl/sharedStrings.xml", _shared_strings_xml(strings))
        for index, (sheet_name, rows) in enumerate(sheets.items(), start=1):
            zf.writestr(f"xl/worksheets/sheet{index}.xml", _sheet_xml(rows, strings, sheet_name))


def _collect_shared_strings(sheets: Mapping[str, list[dict[str, Any]]]) -> list[str]:
    values: list[str] = []
    for rows in sheets.values():
        for row in rows:
            for value in row.values():
                if isinstance(value, str) and value and value not in values:
                    values.append(value)
    return values


def _content_types(sheet_names: list[str]) -> str:
    sheet_overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index, _ in enumerate(sheet_names, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f"{sheet_overrides}"
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        "</Types>"
    )


def _root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def _workbook_xml(sheet_names: list[str]) -> str:
    sheets = "".join(
        f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, name in enumerate(sheet_names, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheets}</sheets>"
        "</workbook>"
    )


def _workbook_rels(sheet_names: list[str]) -> str:
    rels = "".join(
        f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        for index, _ in enumerate(sheet_names, start=1)
    )
    shared = (
        f'<Relationship Id="rId{len(sheet_names) + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" '
        'Target="sharedStrings.xml"/>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{rels}{shared}"
        "</Relationships>"
    )


def _shared_strings_xml(strings: list[str]) -> str:
    items = "".join(f"<si><t>{escape(value)}</t></si>" for value in strings)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">'
        f"{items}"
        "</sst>"
    )


def _sheet_xml(rows: list[dict[str, Any]], strings: list[str], sheet_name: str) -> str:
    del sheet_name
    serialized_rows = "".join(
        f'<row r="{index}">{_row_cells(row, strings, index)}</row>'
        for index, row in enumerate(rows, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{serialized_rows}</sheetData></worksheet>'
    )


def _row_cells(row: dict[str, Any], strings: list[str], row_index: int) -> str:
    cells = []
    for column in sorted(row, key=_column_sort_key):
        value = row[column]
        if value in {None, ""}:
            continue
        ref = f"{column}{row_index}"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            continue
        cells.append(f'<c r="{ref}" t="s"><v>{strings.index(str(value))}</v></c>')
    return "".join(cells)


def _column_sort_key(column: str) -> int:
    total = 0
    for character in column:
        total = total * 26 + ord(character.upper()) - 64
    return total
