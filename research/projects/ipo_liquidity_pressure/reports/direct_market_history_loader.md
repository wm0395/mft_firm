# Direct Market Loader

## Objective

Provide local parsers for the direct NSE report families that already have stable CSV or workbook shapes in the research project.

## Parser Coverage

- Parser-ready families: 9 of 10.
- The market-activity parser covers `Business Growth Data across all segments` and `CM - Market Activity Report`.
- The security-wise price-volume parser covers `Security-wise Price Volume Archives (Equities)`.
- The delivery-position parser covers `CM - Security-wise Delivery Positions`.
- The FII/DII parser covers `FII/FPI and DII trading activity` and `Historical FII/FPI & DII trading activity on NSE, BSE and MSEI`.
- The capital-market monthly workbook parser covers `Segment-wise Historical Reports - Capital Market`, `CM - Category-wise Turnover`, and `CM - Mode of Trading` through the `Exchange_Data_CM_Segment_*.xlsx` sheet layout.
- `Historical Reports - Capital Market` remains manifest-only because the umbrella archive is visible but no file-specific local example has been sampled safely.

## Normalized Output

- `source_file`
- `source_family`
- `parser_kind`
- `trade_date`
- `entity`
- `category`
- `no_of_trades`
- `traded_quantity_lakh_shares`
- `turnover_crore`
- `average_daily_turnover_crore`
- `share_in_total_turnover_pct`
- `buy_value_crore`
- `sell_value_crore`
- `net_value_crore`

## Loader Manifest

| family | parser_kind | parser_status | source_hint | normalized_fields | notes |
| --- | --- | --- | --- | --- | --- |
| Business Growth Data across all segments | market_activity_csv | parser_ready | business growth / MA*.csv | trade_date, entity, no_of_trades, traded_quantity_lakh_shares, turnover_crore, average_daily_turnover_crore, share_in_total_turnover_pct | Shares the market-activity column shape and can be normalized locally. |
| CM - Market Activity Report | market_activity_csv | parser_ready | MA*.csv | trade_date, entity, no_of_trades, traded_quantity_lakh_shares, turnover_crore, average_daily_turnover_crore, share_in_total_turnover_pct | Daily market-activity reports use the same parser as business growth files. |
| FII/FPI and DII trading activity | fii_dii_csv | parser_ready | fii_dii*.csv | trade_date, category, buy_value_crore, sell_value_crore, net_value_crore | Daily category-flow CSVs can be normalized locally. |
| Historical FII/FPI & DII trading activity on NSE, BSE and MSEI | fii_dii_csv | parser_ready | historical fii/dii csv | trade_date, category, buy_value_crore, sell_value_crore, net_value_crore | Historical combined-flow CSVs use the same parser as the daily FII/DII file. |
| Security-wise Price Volume Archives (Equities) | security_price_volume_csv | parser_ready | eq_security / security-wise price volume csv | trade_date, entity, category, traded_quantity_lakh_shares, turnover_crore | Security-wise price-volume CSVs can be normalized locally with quantity and value scaled to the shared schema. |
| Historical Reports - Capital Market | manifest_only | manifest_only | archive entry point | not yet normalized locally | Archive umbrella remains a source-discovery reference only. |
| CM - Security-wise Delivery Positions | delivery_positions_dat | parser_ready | MTO_*.DAT | trade_date, entity, category, traded_quantity_lakh_shares | Security-wise delivery DATs can be normalized locally as a delivery-volume proxy. |
| CM - Category-wise Turnover | capital_market_monthly_xlsx | parser_ready | Exchange_Data_CM_Segment_*.xlsx / Category Data sheet | trade_date, entity, category, buy_value_crore, sell_value_crore, net_value_crore | The segment-wise monthly workbook exposes the category-turnover table as a deterministic sheet. |
| CM - Mode of Trading | capital_market_monthly_xlsx | parser_ready | Exchange_Data_CM_Segment_*.xlsx / Mode of Trading sheet | trade_date, entity, category, no_of_trades, turnover_crore, share_in_total_turnover_pct | The segment-wise monthly workbook exposes the mode-of-trading table as a deterministic sheet. |
| Segment-wise Historical Reports - Capital Market | capital_market_monthly_xlsx | parser_ready | Exchange_Data_CM_Segment_*.xlsx / monthly capital-market workbook | trade_date, entity, category, no_of_trades, turnover_crore, share_in_total_turnover_pct, buy_value_crore, sell_value_crore, net_value_crore | The workbook-backed parser covers the monthly archive and its section sheets, including the top-N concentration proxy. |

## Reading

- This is the first local wiring step toward direct NSE market-history collection.
- Raw downloads can now be normalized for the market-activity, security-wise price-volume, delivery-position, FII/DII, category-turnover, mode-of-trading, and segment-wise monthly workbook families without changing the rest of the research project.