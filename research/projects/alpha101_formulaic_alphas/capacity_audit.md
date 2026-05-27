# Capacity Audit

## Baseline

- Mask: `high_vol_top100`
- Audit lane: `strict_liquidity_100m`
- Source history floor: `1996-01-01`

## Results

- Median active Sharpe: `-1.0911`
- Positive-Sharpe rate: `14.29%`
- Validation pass rate: `missing`
- Validation failures reported: `0`

## Bridge Artifacts

- `broad_universe_capacity_bridge.md`
- `review_packs/blocked_lanes/alpha101_blocked_lanes_pack.md`

## Focus Queue

- `alpha024`: positive
- `alpha023`: positive
- `alpha018`: positive
- `alpha040`: positive

## Interpretation

- The current data contract is close to saturation for exact-OHLCV alone.
- Broad-universe gains need more capacity evidence, not more formula churn.
- The bridge report records what evidence is missing; it does not claim
  broad-universe readiness.
- Further gains now depend on data quality, capacity modeling, and multi-asset coverage.
