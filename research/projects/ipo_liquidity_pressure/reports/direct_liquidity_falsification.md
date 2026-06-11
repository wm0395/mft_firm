# Direct Liquidity Falsification

## Objective

Move from proxy-based pilot evidence to a direct-market-data falsification pass and decide whether the IPO liquidity-pressure thesis should continue, narrow, or be rejected.

## Executive Verdict

Narrow.

The broad pull/release thesis is still not validated, but the direct-data layer is materially better than the proxy-only pass. The raw NSE daily archive cache now spans all 38 seed IPO event windows across 38 event directories and 740 files, with about 1.98 million parsed rows from market-activity and delivery-position files. The loader also parses the workbook-backed segment-wise capital-market archive into category-turnover, mode-of-trading, and top-N concentration rows, which removes one of the biggest direct-data gaps. Even so, the direct event-study chain has not yet been rerun on this panel, the event-study read remains mixed, the pressure gradient is still not monotonic, and the only clean sector-adjusted gradient is the isolated midcap150 release_5 case.

## What Changed Versus the Proxy-Only Pass

- Direct-loader coverage moved to 9 of 10 parser-ready families.
- The segment-wise capital-market workbook now yields direct category-turnover, mode-of-trading, and top-N concentration rows instead of leaving those sections as manifest-only.
- The remaining unsafe family is `Historical Reports - Capital Market`, which is still only an archive umbrella and has no safely sampled local file example.
- Direct category / mode / breadth data now sit beside the existing market-activity, delivery, and FII/DII parsers, so the liquidity-conditioning layer is less proxy-heavy.
- The raw NSE daily archive cache now spans all 38 seed IPO event windows, so the earlier direct-window gap has been closed locally for market-activity and delivery-position files.
- The broad result still does not resolve into a clean, tradable pull-and-release rule.

## Direct Sources Parsed

| family | parser status | direct rows exposed |
| --- | --- | --- |
| `Business Growth Data across all segments` | parser ready | daily turnover, trades, traded quantity, turnover share |
| `CM - Market Activity Report` | parser ready | daily turnover, trades, traded quantity, turnover share |
| `Security-wise Price Volume Archives (Equities)` | parser ready | equity price, volume, turnover, series |
| `CM - Security-wise Delivery Positions` | parser ready | delivered quantity proxy |
| `FII/FPI and DII trading activity` | parser ready | buy, sell, and net flow by category |
| `Historical FII/FPI & DII trading activity on NSE, BSE and MSEI` | parser ready | historical buy, sell, and net flow by category |
| `Segment-wise Historical Reports - Capital Market` | parser ready | monthly workbook sections, including top-N concentration proxy |
| `CM - Category-wise Turnover` | parser ready | buy, sell, and net turnover by client category |
| `CM - Mode of Trading` | parser ready | mode-level trades, gross turnover, and turnover share |
| `Historical Reports - Capital Market` | manifest only | archive umbrella only, no safe local sample yet |

## Direct Liquidity Feature Map

| feature | source family | raw mapping | normalization | missing-data behavior | usable window |
| --- | --- | --- | --- | --- | --- |
| total turnover | market-activity CSV, security price-volume CSV, segment workbook mode sheet | `Turnover ( cr.)`, `Total Turnover (Gross)`, `Turnover (in Rs)` | use reported crores or divide rupees by `10,000,000` | blank / `-` cells are dropped | before, during, and after |
| delivered quantity | delivery DAT | `Quantity` | divide by `100,000` to lakh shares | blank rows are dropped | during and after |
| category turnover | category-turnover sheet | `Buy`, `Sell`, `Net` | divide rupees by `10,000,000` | categories with all missing values are skipped | before and during |
| mode-of-trading mix | mode-of-trading sheet | trade counts, gross turnover, turnover share | counts stay raw; rupees divide by `10,000,000` | modes with all missing values are skipped | before and during |
| breadth proxy | top-N concentration sheet | top-5 / 10 / 25 / 50 / 100 share of turnover | share stays as reported; gross turnover divides by `10,000,000` | rows with all missing values are skipped | before and during |
| foreign/domestic flow | FII/DII CSV | buy, sell, net | values stay in crore INR | blank rows are dropped | before and during |

Issue-size-to-turnover and subscription-pressure-to-turnover remain IPO-event-layer ratios. The direct workbook-backed turnover and category-flow feeds improve the denominator and conditioning, but they do not replace the IPO subscription inputs.

## Gate Readout

| gate | verdict | evidence |
| --- | --- | --- |
| Mechanism | pass on plausibility | large IPOs still look large relative to market turnover, and the direct liquidity feeds now exist to test the stress channel more cleanly |
| Pull | fail | basket returns remain mixed across pressure buckets; the same-sector peer basket does not give a clean monotonic pull signal |
| Release | fail | the release window does not generalize; the narrow midcap150 release_5 lead is isolated |
| Pressure gradient | no | the only clean ordering is sector-adjusted midcap150 in release_5 |
| Narrow midcap150 release_5 signal | yes, but isolated | it survives as a narrow lead, not as a stable regime |
| Strategy | blocked | `define_trade_rules` stays blocked until the validation gates pass |

## Evidence Summary

- The same-sector peer basket remains mixed after sector adjustment.
- The broader sector-adjusted basket pass still leaves recent winners, cash-source names, and the small/midcap baskets mixed.
- The pressure-gradient diagnostic still finds only one non-mixed row: sector-adjusted / release_5 / midcap150.
- The stability pass shows that this lead does not generalize to adjacent windows or nearby basket definitions.
- The direct raw archive cache now covers the 38-event seed study, but the direct event-study chain still needs to be rerun on that panel before any stronger claim is made.

## Conclusion

The thesis is narrowed, not promoted. The direct-data expansion makes the falsification cleaner, but it does not rescue a broad pull/release rule. The surviving signal is too narrow and too unstable to unblock strategy work, and the direct raw cache still needs to be wired into the event-study chain before the direct-data falsification can be considered complete.

## Exact Next Queue

1. Consolidate the 38-event raw NSE cache into a direct liquidity panel with turnover, delivery, and category-flow features aligned to the seed windows.
2. Re-run the pilot, regime-control, sector-conditioned, sector-adjusted, gradient, and stability passes on that direct panel.
3. Sample the remaining `Historical Reports - Capital Market` archive family if a safe local example appears; otherwise keep it manifest-only.
4. Keep `define_trade_rules` blocked until pull, release, monotonicity, robustness, and direct-window coverage all pass.
