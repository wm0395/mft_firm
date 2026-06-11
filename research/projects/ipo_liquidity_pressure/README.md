# IPO Liquidity Pressure

This project tracks the research plan for whether large Indian IPOs temporarily
reduce deployable secondary-market liquidity and whether post-allotment
unblocking creates mean reversion or renewed buying in vulnerable baskets.

## Objective

Validate the mechanism first, then test whether the mechanism creates a
repeatable and tradable pull-and-release effect in the secondary market.

## Scope

- Mainboard IPOs first.
- SME IPOs stay excluded until the mainboard mechanism is validated.
- Use the minimum event dates first: `ipo_open_date`, `ipo_close_date`,
  `allotment_date`, and `listing_date`.
- Treat ASBA blocking as a deployable-liquidity effect, not as a literal stock
  market cash transfer.
- Keep pull and release models separate. They are linked mechanically but they
  do not have to hit the same assets.

## Core Research Questions

1. Does a large IPO create measurable liquidity pressure in the secondary
   market?
2. Do vulnerable baskets underperform before or during the IPO application
   window?
3. Does that underperformance reverse after allotment or unblocking?
4. Does the effect survive market regime, sector, and stock-specific controls?

## Initial Data Requirements

- IPO-level data: issue size, price band, subscription by category, open and
  close dates, allotment date, listing date, and listing gain/loss.
- Market-level data: index returns, turnover, delivery volume, volatility, and
  market regime labels.
- Stock-level data: OHLCV, turnover, market cap, liquidity measures, momentum,
  and sector classification.

## First Event Windows

- Pre-preparation: price-band or RHP attention through the day before IPO open.
- Application: IPO open through IPO close.
- Blocking: IPO close + 1 through allotment - 1.
- Release: allotment through allotment + 5 trading days.
- Longer reversal: allotment through allotment + 20 trading days.

## Validation Gates

1. Mechanism gate: the IPO is large enough relative to market liquidity and the
   secondary market weakens around the event.
2. Pull gate: vulnerable baskets underperform during high-pressure IPO windows.
3. Release gate: prior underperformance mean-reverts after allotment.
4. Tradability gate: the signal is available without lookahead and survives
   costs.
5. Robustness gate: the effect survives time splits, basket changes, and
   market-regime controls.

## Initial Deliverables

- `ipo_events.csv`
- `data/ipo_events_seed.csv`
- `data/ipo_event_windows_seed.csv`
- `data/ipo_pilot_event_study.csv`
- `data/ipo_pilot_event_study_controls.csv`
- `stock_prices.parquet`
- `index_prices.parquet`
- `market_liquidity.parquet`
- `market_history_symbol_coverage.csv`
- `sector_history.parquet`
- `sector_history_coverage.csv`
- `ipo_sector_conditioned_event_study.csv`
- `ipo_sector_adjusted_basket_event_study.csv`
- `ipo_pressure_gradient_diagnostics.csv`
- `ipo_pressure_gradient_stability.csv`
- `ipo_event_windows.parquet`
- `ipo_baskets.parquet`
- `ipo_event_study_results.parquet`
- `ipo_event_study_summary.csv`
- `ipo_pull_release_classification.csv`
- `market_history_expansion.md`
- `sector_history_expansion.md`
- `sector_conditioned_event_study.md`
- `sector_adjusted_basket_event_study.md`
- `pressure_gradient_diagnostics.md`
- `ipo_liquidity_strategy_v0.md`

## Pilot Evidence

The project now has a source-backed seed sample from official exchange,
issuer, and merchant-banker documents for thirty-eight mainboard IPOs:

- Urban Company Limited
- Rubicon Research Limited
- Canara Robeco Asset Management Company Limited
- Canara HSBC Life Insurance Company Limited
- LG Electronics India Limited
- Medi Assist Healthcare Services Limited
- Euro Pratik Sales Limited
- Yatra Online Limited
- TruAlt Bioenergy Limited
- Saatvik Green Energy Limited
- Sudeep Pharma Limited
- OM Freight Forwarders Limited
- Brigade Hotel Ventures Limited
- Glottis Limited
- Fabtech Technologies Limited
- Lenskart Solutions Limited
- One 97 Communications Limited
- Delhivery Limited
- Niva Bupa Health Insurance Company Limited
- Sagility India Limited
- Ather Energy Limited
- Schloss Bangalore Limited
- HDB Financial Services Limited
- Travel Food Services Limited
- Aegis Vopak Terminals Limited
- Afcons Infrastructure Limited
- NTPC Green Energy Limited
- Vishal Mega Mart Limited
- Blue Jet Healthcare Limited
- Honasa Consumer Limited
- Chemplast Sanmar Limited
- Fino Payments Bank Limited
- Fedbank Financial Services Limited
- BlackBuck / Zinka Logistics Solutions Limited
- Bajaj Housing Finance Limited
- Tata Technologies Limited
- Waaree Energies Limited
- KRN Heat Exchanger and Refrigeration Limited

The seed sample supports mechanism plausibility only. The pilot event study is
mixed: it does not show a simple monotonic pull-and-release pattern in the
local market cache.

The follow-up regime-control panel keeps the basket study mixed after
conditioning on NIFTY regime, breadth, and turnover pressure. All focus
windows in the panel map to the volatile control bucket, so the regime split
does not explain away the basket-level mix.

## Market History Expansion

The first market-history expansion pass now writes a point-in-time daily
market-liquidity panel from the local wide OHLCV cache and the index history in
`project_mft.duckdb`:

- `index_prices.parquet`
- `market_liquidity.parquet`
- `market_history_symbol_coverage.csv`
- `market_history_expansion.md`
- `direct_market_history_sources.csv`
- `direct_market_history_sources.md`
- `direct_market_history_collection_manifest.csv`
- `direct_market_history_loader.md`

This is still proxy-based. Direct exchange delivery-volume history and
standalone cash-market turnover feeds are still missing, but the repo now has
explicit daily liquidity and regime inputs for the IPO study.

## Direct Market History Sources

The next wiring target is now explicit. Official NSE archive families have
been identified for direct turnover, delivery, category-flow, and FII/DII
history:

- `Business Growth Data across all segments`
- `Segment-wise Historical Reports - Capital Market`
- `Security-wise Price Volume Archives (Equities)`
- `Historical Reports - Capital Market`
- `CM - Market Activity Report`
- `CM - Security-wise Delivery Positions`
- `CM - Category-wise Turnover`
- `CM - Mode of Trading`
- `FII/FPI and DII trading activity`
- `Historical FII/FPI & DII trading activity on NSE, BSE and MSEI`

These sources remain review-only until a parser and quality pass exists.

## Direct Market Loader

The first local loader now covers the CSV-shaped direct market-history feeds:

- `market_activity_csv` for `Business Growth Data across all segments` and
  `CM - Market Activity Report`
- `security_price_volume_csv` for `Security-wise Price Volume Archives
  (Equities)`
- `delivery_positions_dat` for `CM - Security-wise Delivery Positions`
- `fii_dii_csv` for `FII/FPI and DII trading activity` and `Historical
  FII/FPI & DII trading activity on NSE, BSE and MSEI`

The loader writes a manifest for those parser-ready families and leaves the
remaining official archive families as manifest-only until a file-specific
parser is added.

## Sector History Expansion

The sector-history expansion pass now writes a point-in-time sector-return and
sector-turnover proxy panel from the expanded-parent industry map:

- `sector_history.parquet`
- `sector_history_coverage.csv`
- `sector_history_expansion.md`

This gives the IPO study a sector-relative conditioning layer without adding
new external feeds. It still does not replace exchange-stamped delivery
history or standalone cash-market turnover.

## Sector-Conditioned Event Study

The sector-conditioned event-study pass now uses the sector proxy panel to
test whether the same-sector peer signal survives a sector-return adjustment:

- `ipo_sector_conditioned_event_study.csv`
- `sector_conditioned_event_study.md`

The mapped subset covers 26 of the 38 seed IPO symbols. The sector-adjusted
same-sector peer averages remain mixed, so the sector layer does not rescue a
clean monotonic pull/release rule.

## Sector-Adjusted Basket Event Study

The broader sector-adjusted basket pass now tests every pilot basket against
the sector proxy layer:

- `ipo_sector_adjusted_basket_event_study.csv`
- `sector_adjusted_basket_event_study.md`

The sector-adjusted basket averages remain mixed across application and
release windows, including recent winners, cash-source names, and the
small/midcap baskets. That strengthens the falsification layer: sector drift
does not explain the mixed pilot readout.

## Pressure Gradient Diagnostics

The pressure-gradient diagnostic compares raw and sector-adjusted basket
returns across the ordered pressure buckets:

- `ipo_pressure_gradient_diagnostics.csv`
- `pressure_gradient_diagnostics.md`

It finds one narrow clean case: sector-adjusted `midcap150` in the
`release_5` window orders low -> medium -> high -> extreme with Spearman rho
`1.0`. The rest of the basket/window combinations stay mixed, so the
diagnostic still does not support a broad monotonic pressure gradient.

## Pressure Gradient Stability

The stability pass stress-tests that narrow lead against adjacent windows and
nearby basket definitions:

- `ipo_pressure_gradient_stability.csv`
- `pressure_gradient_stability.md`

The clean sector-adjusted `midcap150` `release_5` case does not generalize to
the adjacent windows, and the release-window basket neighborhood remains mixed
outside `midcap150`. That makes the one clean case look isolated rather than
structural.

## Reports

- [mechanism_and_hypotheses.md](./reports/mechanism_and_hypotheses.md)
- [data_contract.md](./reports/data_contract.md)
- [event_design.md](./reports/event_design.md)
- [validation_framework.md](./reports/validation_framework.md)
- [source_inventory.md](./reports/source_inventory.md)
- [pilot_evidence.md](./reports/pilot_evidence.md)
- [pilot_event_study.md](./reports/pilot_event_study.md)
- [pilot_regime_control_panel.md](./reports/pilot_regime_control_panel.md)
- [market_history_expansion.md](./reports/market_history_expansion.md)
- [direct_market_history_sources.md](./reports/direct_market_history_sources.md)
- [sector_history_expansion.md](./reports/sector_history_expansion.md)
- [sector_conditioned_event_study.md](./reports/sector_conditioned_event_study.md)
- [sector_adjusted_basket_event_study.md](./reports/sector_adjusted_basket_event_study.md)
- [pressure_gradient_diagnostics.md](./reports/pressure_gradient_diagnostics.md)
- [pressure_gradient_stability.md](./reports/pressure_gradient_stability.md)

## Loop Artifacts

- [research_loop_report.md](./research_loop_report.md)
- [next_queue.md](./next_queue.md)

## Review Pack

- [review_packs/README.md](./review_packs/README.md)
- [ipo_liquidity_pressure_pack.md](./review_packs/ipo_liquidity_pressure_pack.md)

## Status

Draft. This repository entry now includes a source-backed seed sample, a
pilot event study, and a regime-control panel, but the full historical
pull/release analysis is still pending.
