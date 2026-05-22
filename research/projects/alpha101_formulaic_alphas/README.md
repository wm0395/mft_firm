# Alpha101 Formulaic Alphas

This project tracks the Alpha101 research loop for the India equity universes
already explored in the notebook workspace.

## Scope

- Exact-OHLCV Alpha101 formulas first
- Expanded high-volatility top-100 lane first
- Proxy-VWAP and snapshot-industry candidates stay research-only until the
  underlying data quality is upgraded
- Prioritize tradeability, cost sensitivity, and robustness over raw discovery
- Current robustness baseline is the strict-liquidity mask-fixed rescore of the
  promoted exact-OHLCV queue
- Committed review packs are required before any promotion update

## Source Of Truth

- `research/notebooks/alpha_001/alpha101_research_brief.md`
- `research/projects/alpha101_formulaic_alphas/alpha101_research_state.json`
- `research/notebooks/alpha_001/research/rebuild_alpha101.py`
- `research/notebooks/alpha_001/research/rebuild_alpha101_sources.py`
- `research/notebooks/alpha_001/research/alpha101_closed_loop.py`
- `research/notebooks/alpha_001/research/alpha101_engine.py`
- `research/notebooks/alpha_001/research/alpha101_formulas.py`
- `research/notebooks/alpha_001/research/alpha101_factory.py`
- `research/notebooks/alpha_001/research/alpha101_robustness.py`
- `research/notebooks/alpha_001/research/alpha101_strict_liquidity_batch_runner.py`

Current source cache span:
- `research/data/nifty500_high_vol/*.csv`
- `research/data/expanded_high_vol_parent/*.csv`
- Rebuilt from Yahoo/Nifty sources back to `1996-01-01` in this workspace

## Committed Review Packs

- [Positive focus pack](./review_packs/positive_focus/alpha101_positive_focus_pack.md)
- [Blocked lanes pack](./review_packs/blocked_lanes/alpha101_blocked_lanes_pack.md)
- [Point-in-time industry metadata lane](./point_in_time_industry_metadata_lane.md)
- [Broad-universe capacity bridge](./broad_universe_capacity_bridge.md)

## Current Queue

1. `alpha040`
2. `alpha026`
3. `alpha012`
4. `alpha024`
5. `alpha044`
6. `alpha018`
7. `alpha023`
8. `alpha051`
9. `alpha049`
10. `alpha016`

## Strict Liquidity Positive Focus

- `alpha024`
- `alpha018`
- `alpha040`
- `alpha023`

These are the only promoted exact-OHLCV names that remain positive under the
widened-history strict-liquidity mask-fixed rescore.

## Blockers

- Proxy VWAP inputs
- Snapshot industry metadata without point-in-time history
- Broad-universe degradation outside the high-vol top-100 lane
- Review packs are committed, and notebook-generated outputs remain
  non-canonical unless they are packed here

## Loop Report

- [research_loop_report.md](./research_loop_report.md)
- [point_in_time_industry_metadata_lane.md](./point_in_time_industry_metadata_lane.md)
- [broad_universe_capacity_bridge.md](./broad_universe_capacity_bridge.md)
