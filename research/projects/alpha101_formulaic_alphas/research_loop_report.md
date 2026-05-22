# Alpha101 Research Loop Report

## Status

- Project status: `draft`
- State file: `research_state.json`
- Legacy state file: `alpha101_research_state.json` (superseded)
- Current phase: late-stage discovery and robustness triage
- Exact-OHLCV historical queue: `28`
- Batch-1 promotions: `11`
- Batch-2 near-misses: `17`

## Committed Review Packs

- Positive focus pack: `review_packs/positive_focus/alpha101_positive_focus_pack.md`
- Blocked lanes pack: `review_packs/blocked_lanes/alpha101_blocked_lanes_pack.md`

## Lane Artifacts

- Point-in-time industry lane: `point_in_time_industry_metadata_lane.md`
- Broad-universe bridge: `broad_universe_capacity_bridge.md`

## Current Metrics

- Strict-liquidity baseline median active Sharpe: `-1.0911`
- Strict-liquidity positive-Sharpe rate: `14.29%`
- Validation pass rate: `nan`
- Validation failures reported: `0`
- Source history floor: `1996-01-01`

## Focus Queue

- `alpha024`: positive, current strict-liquidity active Sharpe `0.8390`
- `alpha018`: borderline, current strict-liquidity active Sharpe `-0.0618`
- `alpha040`: holdout, current strict-liquidity active Sharpe `-0.7584`
- `alpha023`: positive, current strict-liquidity active Sharpe `0.2970`

## Blockers

- Proxy VWAP is blocked until real VWAP data exists.
- Snapshot-industry work is blocked until point-in-time industry metadata exists
  in `point_in_time_industry_metadata_lane.md`.
- Broad-universe work is blocked by degradation outside `high_vol_top100`, as
  documented in `broad_universe_capacity_bridge.md`.
- Review-pack packaging is resolved and captured in the committed packs.
- The remaining blockers stay explicit in the blocker review pack.

## Promotion Criteria

- Evidence pack exists.
- Capacity audit exists.
- Out-of-sample result exists.
- Transaction-cost stress is explicit.
- Blocker status is explicit.
- Review packs are committed and readable without notebooks.

## Next Actions

1. Keep the strict-liquidity focus queue explicit.
2. Review the committed positive-focus pack before any promotion discussion.
3. Review the committed blocked-lanes pack before any blocker update.
4. Keep proxy VWAP blocked.
5. Keep snapshot-industry metadata blocked until point-in-time history exists
   in `point_in_time_industry_metadata_lane.md`.
6. Keep broad-universe work blocked until the capacity bridge survives the
   broader universe via `broad_universe_capacity_bridge.md`.
