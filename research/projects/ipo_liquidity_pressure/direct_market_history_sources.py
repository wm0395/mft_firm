from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class DirectMarketSource:
    family: str
    archive_entry_point: str
    official_evidence: str
    target_fields: str
    research_use: str
    posture: str
    status: str


SOURCE_FAMILIES: tuple[DirectMarketSource, ...] = (
    DirectMarketSource(
        family="Business Growth Data across all segments",
        archive_entry_point="https://www.nseindia.com/national-stock-exchange/nse-volume-business-growth",
        official_evidence="https://www.nseindia.com/all-reports",
        target_fields="daily turnover, average daily turnover, trades, traded quantity, market capitalisation",
        research_use="market-liquidity baseline and pressure normalization",
        posture="restricted",
        status="identified",
    ),
    DirectMarketSource(
        family="Segment-wise Historical Reports - Capital Market",
        archive_entry_point="https://www.nseindia.com/static/regulations/segment-wise-historical-reports",
        official_evidence="https://www.nseindia.com/static/regulations/segment-wise-historical-reports",
        target_fields="exchange monthly report xlsx, transaction data, category turnover, mode of trading, top-N concentration, monthly definition files",
        research_use="monthly direct-market history for turnover, client-category flow, execution mode, and breadth concentration",
        posture="restricted",
        status="identified",
    ),
    DirectMarketSource(
        family="Security-wise Price Volume Archives (Equities)",
        archive_entry_point="https://www.nseindia.com/report-detail/eq_security",
        official_evidence="https://www.nseindia.com/static/regulations/segment-wise-historical-reports",
        target_fields="price, volume, turnover, deliverable quantity, deliverable percentage",
        research_use="direct historical equity price-volume archive for liquidity context",
        posture="restricted",
        status="identified",
    ),
    DirectMarketSource(
        family="Historical Reports - Capital Market",
        archive_entry_point="https://www.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives",
        official_evidence="https://www.nseindia.com/all-reports",
        target_fields="bhavcopy, market activity report, category-wise flows, internet trading statistics",
        research_use="archive entry point for daily cash-market histories",
        posture="restricted",
        status="identified",
    ),
    DirectMarketSource(
        family="CM - Market Activity Report",
        archive_entry_point="https://www.nseindia.com/all-reports",
        official_evidence="https://www.nseindia.com/all-reports",
        target_fields="number of trades, traded quantity, turnover, average daily turnover, share in total turnover",
        research_use="direct per-security turnover and activity control",
        posture="restricted",
        status="identified",
    ),
    DirectMarketSource(
        family="CM - Security-wise Delivery Positions",
        archive_entry_point="https://www.nseindia.com/all-reports",
        official_evidence="https://www.nseindia.com/all-reports",
        target_fields="delivery positions, quantity, security name, trade date",
        research_use="delivery-volume and liquidity-block proxy",
        posture="restricted",
        status="identified",
    ),
    DirectMarketSource(
        family="CM - Category-wise Turnover",
        archive_entry_point="https://www.nseindia.com/all-reports",
        official_evidence="https://www.nseindia.com/all-reports",
        target_fields="turnover by client category, share in total turnover, buy/sell/net breakdown",
        research_use="retail, HNI, and institutional flow decomposition",
        posture="restricted",
        status="identified",
    ),
    DirectMarketSource(
        family="CM - Mode of Trading",
        archive_entry_point="https://www.nseindia.com/all-reports",
        official_evidence="https://www.nseindia.com/all-reports",
        target_fields="trading mode trade counts, turnover share, and gross turnover by execution mode",
        research_use="market microstructure control for liquidity regime shifts",
        posture="restricted",
        status="identified",
    ),
    DirectMarketSource(
        family="FII/FPI and DII trading activity",
        archive_entry_point="https://www.nseindia.com/reports/foreign-investment-limits",
        official_evidence="https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Data%20list%20under%20NSE%20Data%20Sharing%20Policy%20for%20Research%20and%20Analysis_20250728.pdf",
        target_fields="foreign flow regime, FII/FPI and DII trading activity",
        research_use="cross-check whether IPO pressure aligns with foreign and domestic flow regimes",
        posture="restricted",
        status="identified",
    ),
    DirectMarketSource(
        family="Historical FII/FPI & DII trading activity on NSE, BSE and MSEI",
        archive_entry_point="https://www.nseindia.com/all-reports/historical-equities-fii-fpi-dii-trading-activity",
        official_evidence="https://www.nseindia.com/reports/fii-dii",
        target_fields="historical buy value, sell value, and net value for FII/FPI and DII",
        research_use="historical flow-regime conditioning and institutional pressure proxy",
        posture="restricted",
        status="identified",
    ),
)


def main() -> None:
    root = Path(__file__).resolve().parent
    data_path = root / "data" / "direct_market_history_sources.csv"
    report_path = root / "reports" / "direct_market_history_sources.md"
    _write_csv(data_path)
    report_path.write_text(_render_report(), encoding="utf-8")


def _write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(item) for item in SOURCE_FAMILIES]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _render_report() -> str:
    rows = [asdict(item) for item in SOURCE_FAMILIES]
    lines = [
        "# Direct Market History Sources",
        "",
        "## Objective",
        "",
        "Identify the official NSE archive families that can supply direct turnover, delivery, category-flow, and FII/DII history for the IPO liquidity study.",
        "",
        "## Evidence Basis",
        "",
        "- NSE's `all-reports` and regulations pages surface `CM - Market Activity Report`, `CM - Security-wise Delivery Positions`, `CM - Category-wise Turnover`, `CM - Mode of Trading`, the business-growth archive, and security-wise price-volume archives.",
        "- NSE's data-sharing policy PDF explicitly lists daily turnover / average daily turnover, daily market activity report archives, category-wise flows, internet trading statistics, and FII/FPI and DII trading activity.",
        "- The segment-wise historical reports page and the historical FII/FPI & DII page give additional archive entry points for monthly capital-market reports and historical flow-regime data.",
        "- The segment-wise capital-market workbook exposes a deterministic monthly schema with category-turnover, mode-of-trading, and top-N concentration sheets.",
        "- These are official NSE pages and archive entry points, but they remain review-only because the local cache still does not hold the corresponding direct series.",
        "",
        "## Source Families",
        "",
        _render_table(rows),
        "",
        "## Reading",
        "",
        "- These families are the next wiring target for the market-history layer.",
        "- The local cache still only provides price, index, and proxy turnover/breadth panels.",
        "- This inventory narrows the search space for direct turnover, delivery, category-flow, and flow-regime history without pretending the series are already ingested.",
    ]
    return "\n".join(lines)


def _render_table(rows: list[dict[str, str]]) -> str:
    columns = list(rows[0].keys())
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(row[column] for column in columns) + " |")
    return "\n".join([header, separator, *body])


if __name__ == "__main__":
    main()
