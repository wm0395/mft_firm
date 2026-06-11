# IPO Liquidity Pressure Loop Report

## Objective

Validate whether large Indian IPOs temporarily reduce deployable
secondary-market liquidity and whether allotment-driven release creates
mean reversion in vulnerable baskets.

## Files

- [README.md](./README.md)
- [project.json](./project.json)
- [parameter-grid.json](./parameter-grid.json)
- [research_state.json](./research_state.json)
- [reports/source_inventory.md](./reports/source_inventory.md)
- [reports/pilot_evidence.md](./reports/pilot_evidence.md)
- [reports/pilot_event_study.md](./reports/pilot_event_study.md)
- [reports/pilot_regime_control_panel.md](./reports/pilot_regime_control_panel.md)
- [reports/market_history_expansion.md](./reports/market_history_expansion.md)
- [reports/direct_market_history_sources.md](./reports/direct_market_history_sources.md)
- [reports/direct_market_history_loader.md](./reports/direct_market_history_loader.md)
- [reports/sector_history_expansion.md](./reports/sector_history_expansion.md)
- [reports/sector_conditioned_event_study.md](./reports/sector_conditioned_event_study.md)
- [reports/sector_adjusted_basket_event_study.md](./reports/sector_adjusted_basket_event_study.md)
- [reports/pressure_gradient_diagnostics.md](./reports/pressure_gradient_diagnostics.md)
- [reports/pressure_gradient_stability.md](./reports/pressure_gradient_stability.md)
- [data/ipo_events_seed.csv](./data/ipo_events_seed.csv)
- [data/ipo_event_windows_seed.csv](./data/ipo_event_windows_seed.csv)
- [data/ipo_pilot_event_study.csv](./data/ipo_pilot_event_study.csv)
- [data/ipo_pilot_event_study_controls.csv](./data/ipo_pilot_event_study_controls.csv)
- [data/index_prices.parquet](./data/index_prices.parquet)
- [data/market_liquidity.parquet](./data/market_liquidity.parquet)
- [data/market_history_symbol_coverage.csv](./data/market_history_symbol_coverage.csv)
- [data/direct_market_history_sources.csv](./data/direct_market_history_sources.csv)
- [data/direct_market_history_collection_manifest.csv](./data/direct_market_history_collection_manifest.csv)
- [data/sector_history.parquet](./data/sector_history.parquet)
- [data/sector_history_coverage.csv](./data/sector_history_coverage.csv)
- [data/ipo_sector_conditioned_event_study.csv](./data/ipo_sector_conditioned_event_study.csv)
- [data/ipo_sector_adjusted_basket_event_study.csv](./data/ipo_sector_adjusted_basket_event_study.csv)
- [data/ipo_pressure_gradient_diagnostics.csv](./data/ipo_pressure_gradient_diagnostics.csv)
- [data/ipo_pressure_gradient_stability.csv](./data/ipo_pressure_gradient_stability.csv)
- [next_queue.md](./next_queue.md)

## Constraints

- Mainboard IPOs first.
- SME IPOs stay excluded in the first pass.
- Use the minimum event dates first: `ipo_open_date`, `ipo_close_date`,
  `allotment_date`, and `listing_date`.
- Treat ASBA as a deployable-liquidity block, not a literal equity cash
  transfer.
- Keep pull and release models separate.
- No lookahead in subscription, allotment, or classification features.

## Done Conditions

- A historical IPO event dataset exists with minimum required dates.
- Market, index, and stock history needed for event studies is identified.
- Event windows are deterministic and reusable.
- Basket definitions are explicit.
- Pull-window and release-window studies are defined before any trade rule.

## Current Reading

The research question is still unproven. The source-backed seed sample now
includes thirty-eight official mainboard IPOs across extreme, high, medium,
and low pressure comparators, the pilot event study is mixed, and the
market-history layer now includes both the local OHLCV/index cache panel and a
sector-return and sector-turnover proxy panel from the expanded-parent
industry map. The sector-conditioned same-sector peer pass now covers 26 of
the 38 seed IPO symbols and remains mixed after sector adjustment.
The broader sector-adjusted basket pass still leaves recent winners,
cash-source names, and the small/midcap baskets mixed across application and
release windows.
The pressure-gradient diagnostic adds one narrow sector-adjusted lead: the midcap150 basket in the release_5 window orders low to extreme with Spearman rho 1.0.
The pressure-gradient stability pass shows that the midcap150 sector-adjusted lead does not generalize to adjacent windows and that the release-window basket neighborhood remains mixed outside midcap150.

The current read is still that the first pass should compare high-pressure IPOs
against low-pressure IPOs and measure whether vulnerable baskets underperform
before or during the application window, then mean-revert after allotment. The
follow-up control panel keeps the sample in the volatile bucket, so the regime
filter still does not explain the basket mix. Direct turnover, delivery, and
exchange-stamped sector-flow history are now partly loaded through the
workbook-backed segment-wise monthly archive, and the raw NSE daily cache now
spans all 38 seed IPO event windows across 38 event directories and about 1.98
million parsed rows. The broad event-study chain is therefore no longer blocked
on raw-window availability, but the direct panel still needs to be consolidated
and rerun before any stronger claim is made. The direct NSE market-history
source inventory is now part of the project artifacts, and the loader now
normalizes the market-activity, security-wise price-volume, delivery-position,
FII/DII CSV families plus the segment-wise monthly workbook sections into a
local collection manifest. Only the umbrella Historical Reports - Capital
Market family remains manifest-only.

## Immediate Next Queue

1. Consolidate the 38-event raw NSE cache into a direct liquidity panel with
   turnover, delivery, and category-flow features aligned to the seed windows.
2. Re-run the pilot, regime-control, sector-conditioned, sector-adjusted,
   gradient, and stability passes on the direct panel.
3. Sample the remaining `Historical Reports - Capital Market` archive family or
   prove it should stay manifest-only.
4. Keep the thesis narrowed or rejected if the direct-data pass stays mixed,
   and leave `define_trade_rules` blocked until the validation gates and
   direct-window coverage pass.
