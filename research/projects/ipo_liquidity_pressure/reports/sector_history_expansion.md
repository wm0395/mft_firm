# Sector History Expansion

## Objective

Build a point-in-time sector-return and sector-turnover proxy panel from the local expanded-universe OHLCV cache.

## Outputs

- `sector_history.parquet`: 167926 sector-day rows across the expanded universe.
- `sector_history_coverage.csv`: sector-level symbol coverage and date coverage.

## Panel Summary

| rows | sectors | date_start | date_end | mean_sector_return | mean_sector_turnover_crore |
| --- | --- | --- | --- | --- | --- |
| 167926 | 22 | 1996-01-01 | 2026-05-22 | 0.00158199 | 944.093 |

## Sector Coverage

| sector | symbol_count | rows | first_date | last_date | mean_sector_return | mean_turnover_crore |
| --- | --- | --- | --- | --- | --- | --- |
| Financial Services | 121 | 7633 | 1996-01-01 | 2026-05-22 | 0.00149022 | 5546.27 |
| Capital Goods | 110 | 7633 | 1996-01-01 | 2026-05-22 | 0.00173617 | 1640.25 |
| Healthcare | 71 | 7633 | 1996-01-01 | 2026-05-22 | 0.00185234 | 1287.41 |
| Automobile and Auto Components | 48 | 7633 | 1996-01-01 | 2026-05-22 | 0.00183847 | 1270.63 |
| Chemicals | 46 | 7633 | 1996-01-01 | 2026-05-22 | 0.00126812 | 578.344 |
| Consumer Services | 46 | 7633 | 1996-01-01 | 2026-05-22 | 0.00119905 | 720.376 |
| Fast Moving Consumer Goods | 45 | 7633 | 1996-01-01 | 2026-05-22 | 0.00137428 | 1032.72 |
| Consumer Durables | 41 | 7633 | 1996-01-01 | 2026-05-22 | 0.00186331 | 654.866 |
| Information Technology | 36 | 7633 | 1996-01-01 | 2026-05-22 | 0.00187662 | 1602.98 |
| Services | 27 | 7633 | 1996-01-01 | 2026-05-22 | 0.00100805 | 455.354 |
| Metals & Mining | 24 | 7633 | 1996-01-01 | 2026-05-22 | 0.00432586 | 1493.56 |
| Construction | 23 | 7633 | 1996-01-01 | 2026-05-22 | 0.00145643 | 551.594 |
| Power | 22 | 7633 | 1996-01-01 | 2026-05-22 | 0.00130828 | 722.851 |
| Oil Gas & Consumable Fuels | 19 | 7633 | 1996-01-01 | 2026-05-22 | 0.00184365 | 1542.61 |
| Construction Materials | 16 | 7633 | 1996-01-01 | 2026-05-22 | 0.00151009 | 400.912 |
| Realty | 16 | 7633 | 1996-01-01 | 2026-05-22 | 0.000572087 | 330.085 |
| Telecommunication | 12 | 7633 | 1996-01-01 | 2026-05-22 | 0.000753588 | 605.203 |
| Textiles | 12 | 7633 | 1996-01-01 | 2026-05-22 | 0.00144518 | 106.568 |
| Media Entertainment & Publication | 7 | 7633 | 1996-01-01 | 2026-05-22 | 0.00160871 | 182.745 |
| Diversified | 3 | 7633 | 1996-01-01 | 2026-05-22 | 0.00217316 | 18.6731 |

## Reading

- The sector panel is built from local OHLCV and the expanded-parent industry mapping, so it gives the IPO study a point-in-time sector-return and sector-turnover proxy without new external feeds.
- The panel is still proxy-based: it does not replace exchange-stamped delivery history or standalone cash-market turnover.
- The sector layer can now be used to test whether same-sector pull/release effects survive a sector-relative control.