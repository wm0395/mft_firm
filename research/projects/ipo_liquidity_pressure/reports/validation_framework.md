# IPO Validation Framework

## Gates

1. Mechanism gate: the IPO must be large enough relative to market liquidity.
2. Pull gate: vulnerable baskets must underperform in high-pressure windows.
3. Release gate: prior underperformance must mean-revert after allotment.
4. Tradability gate: the signal must be observable without lookahead.
5. Robustness gate: the effect must survive regime and basket changes.

## Core Tests

- Event study by IPO pressure bucket.
- Windowed abnormal return comparison.
- Regression with pressure, vulnerability, regime, and interaction terms.
- Pre/post allotment reversal classification.

## Required Controls

- Market return.
- Sector return.
- Volatility regime.
- FII / DII flow regime if available.
- Stock-specific news or earnings flags.
- Concurrent IPOs.
- Major macro shocks.

## Output Contract

- A pull/release classification per IPO.
- Average abnormal return tables by window and basket.
- Regression outputs that separate pressure from market regime.
- A tradeable strategy only if the gates pass.

## Decision Rule

Case A is the only full-cycle candidate:
pull observed and release observed.
Case B is a pull-only failure or avoid/short candidate.
Case C is a release-only candidate.
Case D is no useful effect.
