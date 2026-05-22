# Associate Data Source Queue

## Objective

Inventory free sources and prototype adapters one by one.

## Files

- `research/firm/research_queue.json`
- `research/firm/daily_research_state.json`
- `research/projects/alpha101_formulaic_alphas/research_state.json`

## Constraints

- Verify license and allowed use before adopting a source.
- No silent skips for missing fields.
- Quality reports are required for every source lane.
- Tests should not depend on live network calls by default.

## Done Conditions

- Source registry entries exist.
- Adapter status is explicit.
- Quality reports exist.
- Blocking reasons are explicit where adapters are not ready.

## Queue

1. Keep the source registry current.
2. Prototype NSE, MCX, and FRED adapters first.
3. Record quality gaps and field coverage for each source.
4. Flag any source that cannot be used as a sole production input.
