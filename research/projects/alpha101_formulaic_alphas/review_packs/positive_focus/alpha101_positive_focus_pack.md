# Alpha101 Positive Focus Review Pack

## Purpose

Committed review pack for the current strict-liquidity focus queue.

## Canonical Inputs

- `../research_state.json`
- `../research_loop_report.md`
- `../capacity_audit.md`
- `../blocked_lanes.md`
- `../next_queue.md`

## State Snapshot

- Project status: `draft`
- Promoted exact-OHLCV names: `28`
- Batch-1 promotions: `11`
- Batch-2 near-misses: `17`
- Strict-liquidity baseline median active Sharpe: `-1.0911`
- Positive-Sharpe rate: `14.29%`
- Validation pass rate: `nan`

## Focus Queue

| alpha_id | status | strict_liquidity_active_sharpe | note |
| --- | --- | --- | --- |
| alpha024 | positive | 0.8390 | Positive focus |
| alpha018 | borderline | -0.0618 | Borderline |
| alpha040 | holdout | -0.7584 | Holdout |
| alpha023 | positive | 0.2970 | Positive focus |

## Evidence Notes

- The current exact-OHLCV promotion ledger remains unchanged.
- `alpha024` and `alpha023` remain the only positive names in the strict-
  liquidity focus queue.
- `alpha018` remains borderline until the evidence changes.
- `alpha040` remains a holdout.
- No notebook-only claim is used as canonical status.

## Promotion Gate Check

- Evidence pack exists: yes.
- Capacity audit exists: yes.
- Out-of-sample result exists: yes, in the current state artifacts.
- Transaction-cost stress is explicit: yes, via the current capacity audit and
  loop report.
- Blocker status is explicit: yes.

## Decision

- Keep the current promotion counts unchanged.
- Keep the strict-liquidity focus queue explicit.
- Continue review only; do not promote on the basis of this pack alone.

