# VP Research Queue

## Objective

Keep the Alpha101 promotion path explicit and bounded.

## Files

- `research/firm/research_queue.json`
- `research/firm/daily_research_state.json`
- `research/projects/alpha101_formulaic_alphas/research_state.json`
- `research/projects/alpha101_formulaic_alphas/research_loop_report.md`
- `research/projects/alpha101_formulaic_alphas/capacity_audit.md`
- `research/projects/alpha101_formulaic_alphas/blocked_lanes.md`
- `research/projects/alpha101_formulaic_alphas/point_in_time_industry_metadata_lane.md`
- `research/projects/alpha101_formulaic_alphas/broad_universe_capacity_bridge.md`
- `research/projects/alpha101_formulaic_alphas/review_packs/positive_focus/alpha101_positive_focus_pack.md`
- `research/projects/alpha101_formulaic_alphas/review_packs/blocked_lanes/alpha101_blocked_lanes_pack.md`

## Constraints

- Exact-OHLCV remains the active baseline.
- Proxy VWAP and snapshot-industry lanes remain blocked.
- Broad-universe degradation stays visible.
- Notebook outputs are not treated as canonical unless they are committed
  review packs.

## Done Conditions

- Focus queue stays explicit.
- Promotion criteria stay explicit.
- Blockers stay explicit.
- Review packs are committed before any promotion claim.

## Queue

1. Review the strict-liquidity focus queue through the committed positive-focus pack.
2. Keep `alpha024` and `alpha023` on the positive path.
3. Keep `alpha018` on the borderline path until it clears or fails.
4. Keep `alpha040` on holdout until the signal improves.
5. Keep proxy VWAP blocked until real VWAP exists.
6. Keep snapshot-industry work blocked until point-in-time history exists.
7. Keep broad-universe work blocked until the capacity bridge survives the broader universe.
8. Use the committed review packs before any promotion update.
