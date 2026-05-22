# Associate Asset Class Queue

## Objective

Define explicit universes, symbol mapping, calendars, and roll rules.

## Files

- `research/firm/research_queue.json`
- `research/firm/daily_research_state.json`
- `research/projects/alpha101_formulaic_alphas/research_state.json`

## Constraints

- Asset classes must have canonical symbol formats.
- Futures and commodity lanes need explicit roll rules.
- Benchmarks and liquidity fields stay documented.
- No asset-class claims without a source priority order.

## Done Conditions

- Asset-class registry exists.
- Symbol mapping is documented.
- Calendar and roll requirements are explicit.
- Benchmark mapping is explicit.

## Queue

1. Keep the Indian equity, ETF, index, and derivative lanes explicit.
2. Keep MCX futures and options roll requirements explicit.
3. Keep macro, FX proxy, and global proxy lanes explicit.
4. Document the source priority order for each asset class.
