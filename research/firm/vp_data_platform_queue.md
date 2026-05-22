# VP Data & Platform Queue

## Objective

Keep source readiness, contracts, and schema gates explicit.

## Files

- `research/firm/research_queue.json`
- `research/firm/daily_research_state.json`
- `research/projects/alpha101_formulaic_alphas/research_state.json`
- `research/projects/alpha101_formulaic_alphas/blocked_lanes.md`

## Constraints

- No source is marked production without a validated adapter.
- No lane is marked ready without a data contract.
- Point-in-time metadata is required where the lane needs it.
- Source legality and allowed use must stay explicit.

## Done Conditions

- Source registry status is explicit.
- Data contract gaps are explicit.
- Quality gates exist for every admitted lane.
- Multi-asset expansion can be blocked by data if needed.

## Queue

1. Own the source registry and lane readiness map.
2. Keep contract gaps visible for VWAP and point-in-time metadata.
3. Maintain source quality and adapter status in the control room.
4. Gate multi-asset lanes until the data contract is ready.
