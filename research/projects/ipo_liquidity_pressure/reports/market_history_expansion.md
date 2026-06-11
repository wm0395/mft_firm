# Market History Expansion

## Objective

Turn the local price cache into a point-in-time daily market-liquidity panel that can condition the IPO pull/release study.

## Outputs

- `index_prices.parquet`: 7385 index rows from the local `project_mft.duckdb` cache.
- `market_liquidity.parquet`: 7633 daily rows keyed by trading date.
- `market_history_symbol_coverage.csv`: seed-IPO source coverage by local market-history store.

## Local Panel Summary

| panel | rows | symbols | date_start | date_end | seed_coverage |
| --- | --- | --- | --- | --- | --- |
| nifty500_high_vol | 7633 | 504 | 1996-01-01 | 2026-05-22 | 21 |
| expanded_high_vol_parent | 7633 | 749 | 1996-01-01 | 2026-05-22 | 26 |

## Index History Summary

| asset_symbol | rows | date_start | date_end |
| --- | --- | --- | --- |
| NIFTY | 2465 | 2016-05-22 | 2026-05-21 |
| BANKNIFTY | 2467 | 2016-05-22 | 2026-05-21 |
| FINNIFTY | 2452 | 2016-05-22 | 2026-05-21 |
| MIDCPNIFTY | 1 | 2026-05-21 | 2026-05-21 |

## Seed Coverage Summary

- `project_mft.duckdb` has direct market rows for 21 of the 38 seed IPO symbols.
- `nifty500_high_vol` covers 21 of the 38 seed IPO symbols.
- `expanded_high_vol_parent` covers 26 of the 38 seed IPO symbols.
- Missing from all three local price stores: Medi Assist Healthcare Services Limited, Euro Pratik Sales Limited, Yatra Online Limited, TruAlt Bioenergy Limited, Saatvik Green Energy Limited, Om Freight Forwarders Limited, Brigade Hotel Ventures Limited, Glottis Limited, Fabtech Technologies Limited, Chemplast Sanmar Limited, Fino Payments Bank Limited, KRN Heat Exchanger and Refrigeration Limited.

## Reading

- The price cache is broad enough to anchor the event study: the wide panels run from 1996-01-01 to 2026-05-22, and the index cache runs from 2016-05-22 to 2026-05-21.
- The bottleneck is still direct liquidity history. There is no local delivery-volume history or standalone cash-market turnover feed yet, but the repo now has a point-in-time sector-return and sector-turnover proxy panel.
- The new market-liquidity panel is proxy-based: it combines expanded-universe turnover, breadth, mean return, and NIFTY regime states into a daily table.
- That is enough to improve conditioning for the IPO hypothesis, but it is still not the final turnover-and-delivery data contract described in the project docs.