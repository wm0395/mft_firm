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
- [data/ipo_events_seed.csv](./data/ipo_events_seed.csv)
- [data/ipo_event_windows_seed.csv](./data/ipo_event_windows_seed.csv)
- [data/ipo_pilot_event_study.csv](./data/ipo_pilot_event_study.csv)
- [data/ipo_pilot_event_study_controls.csv](./data/ipo_pilot_event_study_controls.csv)
- [data/index_prices.parquet](./data/index_prices.parquet)
- [data/market_liquidity.parquet](./data/market_liquidity.parquet)
- [data/market_history_symbol_coverage.csv](./data/market_history_symbol_coverage.csv)
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
includes twenty-eight official mainboard IPOs across extreme, high, medium,
and low pressure comparators, and the pilot event study is mixed: the local
market cache does not show a simple monotonic pull-and-release pattern.

The first pass should compare high-pressure IPOs against low-pressure IPOs and
measure whether the vulnerable baskets underperform before or during the
application window, then mean-revert after allotment. The follow-up control
panel keeps the sample in the volatile bucket, so the regime filter did not
yet explain the basket mix.

## Immediate Next Queue

1. Expand the seed sample into a broader historical mainboard IPO table.
2. Add more low and medium pressure comparators so the pressure gradient can be
   tested properly.
3. Re-run the regime-control panel on the broader table and check whether
   volatile, bull, bear, or calm conditioning changes the readout.
4. Test whether the weak pilot signal survives transaction-cost and regime
   filters.
5. Run the first full event study and classify pull/release cases.
6. Only after a reproducible mechanism and reversal appear, draft
   `ipo_liquidity_strategy_v0.md`.
