# Direct Market History Sources

## Objective

Identify the official NSE archive families that can supply direct turnover, delivery, category-flow, and FII/DII history for the IPO liquidity study.

## Evidence Basis

- NSE's `all-reports` and regulations pages surface `CM - Market Activity Report`, `CM - Security-wise Delivery Positions`, `CM - Category-wise Turnover`, `CM - Mode of Trading`, the business-growth archive, and security-wise price-volume archives.
- NSE's data-sharing policy PDF explicitly lists daily turnover / average daily turnover, daily market activity report archives, category-wise flows, internet trading statistics, and FII/FPI and DII trading activity.
- The segment-wise historical reports page and the historical FII/FPI & DII page give additional archive entry points for monthly capital-market reports and historical flow-regime data.
- The segment-wise capital-market workbook exposes a deterministic monthly schema with category-turnover, mode-of-trading, and top-N concentration sheets.
- These are official NSE pages and archive entry points, but they remain review-only because the local cache still does not hold the corresponding direct series.

## Source Families

| family | archive_entry_point | official_evidence | target_fields | research_use | posture | status |
| --- | --- | --- | --- | --- | --- | --- |
| Business Growth Data across all segments | https://www.nseindia.com/national-stock-exchange/nse-volume-business-growth | https://www.nseindia.com/all-reports | daily turnover, average daily turnover, trades, traded quantity, market capitalisation | market-liquidity baseline and pressure normalization | restricted | identified |
| Segment-wise Historical Reports - Capital Market | https://www.nseindia.com/static/regulations/segment-wise-historical-reports | https://www.nseindia.com/static/regulations/segment-wise-historical-reports | exchange monthly report xlsx, transaction data, category turnover, mode of trading, top-N concentration, monthly definition files | monthly direct-market history for turnover, client-category flow, execution mode, and breadth concentration | restricted | identified |
| Security-wise Price Volume Archives (Equities) | https://www.nseindia.com/report-detail/eq_security | https://www.nseindia.com/static/regulations/segment-wise-historical-reports | price, volume, turnover, deliverable quantity, deliverable percentage | direct historical equity price-volume archive for liquidity context | restricted | identified |
| Historical Reports - Capital Market | https://www.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives | https://www.nseindia.com/all-reports | bhavcopy, market activity report, category-wise flows, internet trading statistics | archive entry point for daily cash-market histories | restricted | identified |
| CM - Market Activity Report | https://www.nseindia.com/all-reports | https://www.nseindia.com/all-reports | number of trades, traded quantity, turnover, average daily turnover, share in total turnover | direct per-security turnover and activity control | restricted | identified |
| CM - Security-wise Delivery Positions | https://www.nseindia.com/all-reports | https://www.nseindia.com/all-reports | delivery positions, quantity, security name, trade date | delivery-volume and liquidity-block proxy | restricted | identified |
| CM - Category-wise Turnover | https://www.nseindia.com/all-reports | https://www.nseindia.com/all-reports | turnover by client category, share in total turnover, buy/sell/net breakdown | retail, HNI, and institutional flow decomposition | restricted | identified |
| CM - Mode of Trading | https://www.nseindia.com/all-reports | https://www.nseindia.com/all-reports | trading mode trade counts, turnover share, and gross turnover by execution mode | market microstructure control for liquidity regime shifts | restricted | identified |
| FII/FPI and DII trading activity | https://www.nseindia.com/reports/foreign-investment-limits | https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Data%20list%20under%20NSE%20Data%20Sharing%20Policy%20for%20Research%20and%20Analysis_20250728.pdf | foreign flow regime, FII/FPI and DII trading activity | cross-check whether IPO pressure aligns with foreign and domestic flow regimes | restricted | identified |
| Historical FII/FPI & DII trading activity on NSE, BSE and MSEI | https://www.nseindia.com/all-reports/historical-equities-fii-fpi-dii-trading-activity | https://www.nseindia.com/reports/fii-dii | historical buy value, sell value, and net value for FII/FPI and DII | historical flow-regime conditioning and institutional pressure proxy | restricted | identified |

## Reading

- These families are the next wiring target for the market-history layer.
- The local cache still only provides price, index, and proxy turnover/breadth panels.
- This inventory narrows the search space for direct turnover, delivery, category-flow, and flow-regime history without pretending the series are already ingested.