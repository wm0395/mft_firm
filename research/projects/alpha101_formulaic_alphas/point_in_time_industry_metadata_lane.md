# Point-in-Time Industry Metadata Lane

## Objective

Replace snapshot industry metadata with point-in-time industry history before
any industry-neutral promotion is considered.

## Current State

- The current Alpha101 state still relies on snapshot industry metadata.
- No point-in-time industry history is committed in this research scope yet.
- The lane remains blocked and does not change the promotion ledger.

## Required Evidence

- Historical industry membership by date.
- Deterministic `valid_from` and `valid_to` joins.
- Explicit source and license notes for the metadata path.
- A reviewable pack that shows the lane is blocked for the right reason.

## Blocker

Point-in-time industry metadata is not available in the current contract.

## Unblock Conditions

- Point-in-time industry snapshots exist.
- The join logic is reproducible and documented.
- The evidence pack is committed alongside the loop report.

## Linked Artifacts

- `blocked_lanes.md`
- `research_loop_report.md`
- `review_packs/blocked_lanes/alpha101_blocked_lanes_pack.md`

