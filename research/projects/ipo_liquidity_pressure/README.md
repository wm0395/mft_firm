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
- `ipo_event_windows.parquet`
- `ipo_baskets.parquet`
- `ipo_event_study_results.parquet`
- `ipo_event_study_summary.csv`
- `ipo_pull_release_classification.csv`
- `ipo_liquidity_strategy_v0.md`

## Pilot Evidence

The project now has a source-backed seed sample from official exchange,
issuer, and merchant-banker documents for twenty-eight mainboard IPOs:

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

This is still proxy-based. Direct exchange delivery-volume history, cash-market
turnover feeds, and point-in-time sector return series are still missing, but
the repo now has explicit daily liquidity and regime inputs for the IPO study.

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
