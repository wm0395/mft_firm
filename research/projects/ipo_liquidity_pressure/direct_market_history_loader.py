from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.projects.ipo_liquidity_pressure.capital_market_monthly_parser import (  # noqa: E402
    is_capital_market_monthly_xlsx,
    parse_capital_market_monthly_xlsx,
)
from research.projects.ipo_liquidity_pressure.delivery_positions_parser import (  # noqa: E402
    is_delivery_positions_file,
    parse_delivery_positions_dat,
)
from research.projects.ipo_liquidity_pressure.market_activity_report_parser import (  # noqa: E402
    is_market_activity_file,
    parse_market_activity_csv,
)


@dataclass(frozen=True)
class DirectMarketLoaderSpec:
    family: str
    parser_kind: str
    parser_status: str
    source_hint: str
    normalized_fields: str
    notes: str


LOADER_SPECS: tuple[DirectMarketLoaderSpec, ...] = (
    DirectMarketLoaderSpec(
        family="Business Growth Data across all segments",
        parser_kind="market_activity_csv",
        parser_status="parser_ready",
        source_hint="business growth / MA*.csv",
        normalized_fields="trade_date, entity, no_of_trades, traded_quantity_lakh_shares, turnover_crore, average_daily_turnover_crore, share_in_total_turnover_pct",
        notes="Shares the market-activity column shape and can be normalized locally.",
    ),
    DirectMarketLoaderSpec(
        family="CM - Market Activity Report",
        parser_kind="market_activity_csv",
        parser_status="parser_ready",
        source_hint="MA*.csv",
        normalized_fields="trade_date, entity, no_of_trades, traded_quantity_lakh_shares, turnover_crore, average_daily_turnover_crore, share_in_total_turnover_pct",
        notes="Daily market-activity reports use the same parser as business growth files.",
    ),
    DirectMarketLoaderSpec(
        family="FII/FPI and DII trading activity",
        parser_kind="fii_dii_csv",
        parser_status="parser_ready",
        source_hint="fii_dii*.csv",
        normalized_fields="trade_date, category, buy_value_crore, sell_value_crore, net_value_crore",
        notes="Daily category-flow CSVs can be normalized locally.",
    ),
    DirectMarketLoaderSpec(
        family="Historical FII/FPI & DII trading activity on NSE, BSE and MSEI",
        parser_kind="fii_dii_csv",
        parser_status="parser_ready",
        source_hint="historical fii/dii csv",
        normalized_fields="trade_date, category, buy_value_crore, sell_value_crore, net_value_crore",
        notes="Historical combined-flow CSVs use the same parser as the daily FII/DII file.",
    ),
    DirectMarketLoaderSpec(
        family="Security-wise Price Volume Archives (Equities)",
        parser_kind="security_price_volume_csv",
        parser_status="parser_ready",
        source_hint="eq_security / security-wise price volume csv",
        normalized_fields="trade_date, entity, category, traded_quantity_lakh_shares, turnover_crore",
        notes="Security-wise price-volume CSVs can be normalized locally with quantity and value scaled to the shared schema.",
    ),
    DirectMarketLoaderSpec(
        family="Historical Reports - Capital Market",
        parser_kind="manifest_only",
        parser_status="manifest_only",
        source_hint="archive entry point",
        normalized_fields="not yet normalized locally",
        notes="Archive umbrella remains a source-discovery reference only.",
    ),
    DirectMarketLoaderSpec(
        family="CM - Security-wise Delivery Positions",
        parser_kind="delivery_positions_dat",
        parser_status="parser_ready",
        source_hint="MTO_*.DAT",
        normalized_fields="trade_date, entity, category, traded_quantity_lakh_shares, delivery_percentage",
        notes="Security-wise delivery DATs can be normalized locally as a delivery-volume and delivery-ratio proxy.",
    ),
    DirectMarketLoaderSpec(
        family="CM - Category-wise Turnover",
        parser_kind="capital_market_monthly_xlsx",
        parser_status="parser_ready",
        source_hint="Exchange_Data_CM_Segment_*.xlsx / Category Data sheet",
        normalized_fields="trade_date, entity, category, buy_value_crore, sell_value_crore, net_value_crore",
        notes="The segment-wise monthly workbook exposes the category-turnover table as a deterministic sheet.",
    ),
    DirectMarketLoaderSpec(
        family="CM - Mode of Trading",
        parser_kind="capital_market_monthly_xlsx",
        parser_status="parser_ready",
        source_hint="Exchange_Data_CM_Segment_*.xlsx / Mode of Trading sheet",
        normalized_fields="trade_date, entity, category, no_of_trades, turnover_crore, share_in_total_turnover_pct",
        notes="The segment-wise monthly workbook exposes the mode-of-trading table as a deterministic sheet.",
    ),
    DirectMarketLoaderSpec(
        family="Segment-wise Historical Reports - Capital Market",
        parser_kind="capital_market_monthly_xlsx",
        parser_status="parser_ready",
        source_hint="Exchange_Data_CM_Segment_*.xlsx / monthly capital-market workbook",
        normalized_fields="trade_date, entity, category, no_of_trades, turnover_crore, share_in_total_turnover_pct, buy_value_crore, sell_value_crore, net_value_crore",
        notes="The workbook-backed parser covers the monthly archive and its section sheets, including the top-N concentration proxy.",
    ),
)

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


def main() -> None:
    root = Path(__file__).resolve().parent
    manifest = build_collection_manifest()
    data_path = root / "data" / "direct_market_history_collection_manifest.csv"
    report_path = root / "reports" / "direct_market_history_loader.md"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(data_path, index=False)
    report_path.write_text(_render_report(manifest), encoding="utf-8")


def build_collection_manifest() -> pd.DataFrame:
    return pd.DataFrame([asdict(spec) for spec in LOADER_SPECS])


def load_direct_market_history_directory(raw_dir: Path) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for path in sorted(raw_dir.iterdir()):
        if not path.is_file():
            continue
        frame = load_direct_market_history_file(path)
        if frame.empty:
            continue
        records.extend(frame.to_dict(orient="records"))
    if not records:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)


def load_direct_market_history_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv" and is_market_activity_file(path.name):
        return parse_market_activity_csv(path)
    if suffix == ".dat" and is_delivery_positions_file(path.name):
        return parse_delivery_positions_dat(path)
    if suffix == ".xlsx" and is_capital_market_monthly_xlsx(path.name):
        return parse_capital_market_monthly_xlsx(path)
    if suffix != ".csv":
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    frame = pd.read_csv(path)
    parser_kind = _infer_parser_kind(path.name, frame.columns)
    if parser_kind == "security_price_volume_csv":
        return _parse_security_price_volume_csv(path, frame)
    if parser_kind == "market_activity_csv":
        return _parse_market_activity_csv(path, frame)
    if parser_kind == "fii_dii_csv":
        return _parse_fii_dii_csv(path, frame)
    return pd.DataFrame(columns=OUTPUT_COLUMNS)


def _parse_market_activity_csv(path: Path, frame: pd.DataFrame) -> pd.DataFrame:
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
    source_family = "Business Growth Data across all segments" if "business" in path.stem.lower() else "CM - Market Activity Report"
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


def _parse_security_price_volume_csv(path: Path, frame: pd.DataFrame) -> pd.DataFrame:
    renamed = _rename_columns(
        frame,
        {
            "symbol": "entity",
            "date": "trade_date",
            "prevclose": "prev_close",
            "openprice": "open_price",
            "highprice": "high_price",
            "lowprice": "low_price",
            "closeprice": "close_price",
            "totaltradedquantity": "traded_quantity_lakh_shares",
            "totaltradedvalueinrs": "turnover_crore",
        },
    )
    columns = {_canonical_key(column): column for column in frame.columns}
    out = pd.DataFrame(index=renamed.index)
    out["source_file"] = path.name
    out["source_family"] = "Security-wise Price Volume Archives (Equities)"
    out["parser_kind"] = "security_price_volume_csv"
    out["trade_date"] = pd.to_datetime(renamed["trade_date"], errors="coerce", dayfirst=True).dt.date.astype(str)
    out["entity"] = renamed["entity"]
    out["category"] = frame[columns["series"]] if "series" in columns else None
    out["no_of_trades"] = pd.NA
    out["traded_quantity_lakh_shares"] = _scale_to_lakh_shares(renamed["traded_quantity_lakh_shares"])
    out["turnover_crore"] = _scale_to_crore(renamed["turnover_crore"])
    out["average_daily_turnover_crore"] = pd.NA
    out["share_in_total_turnover_pct"] = pd.NA
    out["buy_value_crore"] = pd.NA
    out["sell_value_crore"] = pd.NA
    out["net_value_crore"] = pd.NA
    out["delivery_percentage"] = pd.NA
    out["source_row_index"] = range(len(out))
    return out[list(OUTPUT_COLUMNS)]


def _parse_fii_dii_csv(path: Path, frame: pd.DataFrame) -> pd.DataFrame:
    renamed = _rename_columns(
        frame,
        {
            "category": "category",
            "date": "trade_date",
            "buyvaluecrores": "buy_value_crore",
            "sellvaluecrores": "sell_value_crore",
            "netvaluecrores": "net_value_crore",
        },
    )
    source_family = (
        "Historical FII/FPI & DII trading activity on NSE, BSE and MSEI"
        if "historical" in path.stem.lower() or "combined" in path.stem.lower()
        else "FII/FPI and DII trading activity"
    )
    out = renamed.assign(
        source_file=path.name,
        source_family=source_family,
        parser_kind="fii_dii_csv",
        entity=lambda frame: frame["category"],
        no_of_trades=pd.NA,
        traded_quantity_lakh_shares=pd.NA,
        turnover_crore=pd.NA,
        average_daily_turnover_crore=pd.NA,
        share_in_total_turnover_pct=pd.NA,
        delivery_percentage=pd.NA,
    )
    out["trade_date"] = pd.to_datetime(out["trade_date"], errors="coerce", dayfirst=True).dt.date.astype(str)
    out["source_row_index"] = range(len(out))
    return out[list(OUTPUT_COLUMNS)]


def _infer_parser_kind(file_name: str, columns: pd.Index) -> str:
    canonical_columns = {_canonical_key(column) for column in columns}
    if {
        "symbol",
        "date",
        "prevclose",
        "openprice",
        "highprice",
        "lowprice",
        "closeprice",
        "totaltradedquantity",
        "totaltradedvalueinrs",
    } <= canonical_columns:
        return "security_price_volume_csv"
    if {"category", "date", "buyvaluecrores", "sellvaluecrores", "netvaluecrores"} <= canonical_columns:
        return "fii_dii_csv"
    if {"security", "nooftrades", "tradedquantitylakshares", "turnovercr", "averagedailyturnovercr", "shareintotalturnover"} <= canonical_columns:
        return "market_activity_csv"
    lower_name = file_name.lower()
    if "fii" in lower_name and "dii" in lower_name:
        return "fii_dii_csv"
    if lower_name.startswith("ma") or "market activity" in lower_name or "business" in lower_name:
        return "market_activity_csv"
    return "manifest_only"


def _rename_columns(frame: pd.DataFrame, target_names: dict[str, str]) -> pd.DataFrame:
    columns = {_canonical_key(column): column for column in frame.columns}
    missing = [key for key in target_names if key not in columns]
    if missing:
        raise ValueError(f"missing expected columns: {missing}")
    rename_map = {columns[key]: target_name for key, target_name in target_names.items()}
    return frame.rename(columns=rename_map)


def _scale_to_lakh_shares(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(",", "", regex=False)
    return pd.to_numeric(cleaned, errors="coerce") / 100000


def _scale_to_crore(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(",", "", regex=False)
    return pd.to_numeric(cleaned, errors="coerce") / 10000000


def _parse_report_date_from_filename(file_name: str) -> str | None:
    match = re.search(r"(\d{6})", file_name)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%d%m%y").date().isoformat()
    except ValueError:
        return None


def _canonical_key(text: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def _render_report(manifest: pd.DataFrame) -> str:
    ready = manifest[manifest["parser_status"] == "parser_ready"]
    lines = [
        "# Direct Market Loader",
        "",
        "## Objective",
        "",
        "Provide local parsers for the direct NSE report families that already have stable CSV or workbook shapes in the research project.",
        "",
        "## Parser Coverage",
        "",
        f"- Parser-ready families: {len(ready)} of {len(manifest)}.",
        "- The market-activity parser covers `Business Growth Data across all segments` and `CM - Market Activity Report`.",
        "- The security-wise price-volume parser covers `Security-wise Price Volume Archives (Equities)`.",
        "- The delivery-position parser covers `CM - Security-wise Delivery Positions`.",
        "- The FII/DII parser covers `FII/FPI and DII trading activity` and `Historical FII/FPI & DII trading activity on NSE, BSE and MSEI`.",
        "- The capital-market monthly workbook parser covers `Segment-wise Historical Reports - Capital Market`, `CM - Category-wise Turnover`, and `CM - Mode of Trading` through the `Exchange_Data_CM_Segment_*.xlsx` sheet layout.",
        "- `Historical Reports - Capital Market` remains manifest-only because the umbrella archive is visible but no file-specific local example has been sampled safely.",
        "",
        "## Normalized Output",
        "",
        "- `source_file`",
        "- `source_family`",
        "- `parser_kind`",
        "- `trade_date`",
        "- `entity`",
        "- `category`",
        "- `no_of_trades`",
        "- `traded_quantity_lakh_shares`",
        "- `turnover_crore`",
        "- `average_daily_turnover_crore`",
        "- `share_in_total_turnover_pct`",
        "- `buy_value_crore`",
        "- `sell_value_crore`",
        "- `net_value_crore`",
        "- `delivery_percentage`",
        "",
        "## Loader Manifest",
        "",
        _render_table(manifest),
        "",
        "## Reading",
        "",
        "- This is the first local wiring step toward direct NSE market-history collection.",
        "- Raw downloads can now be normalized for the market-activity, security-wise price-volume, delivery-position, FII/DII, category-turnover, mode-of-trading, and segment-wise monthly workbook families without changing the rest of the research project.",
    ]
    return "\n".join(lines)


def _render_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(str(row[column]) for column in columns) + " |" for _, row in frame.iterrows()]
    return "\n".join([header, separator, *body])


if __name__ == "__main__":
    main()
