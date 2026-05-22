# Blocked Lanes

## Current Blockers

| Lane | Status | Reason | Artifact | Unblock Condition |
| --- | --- | --- | --- | --- |
| `proxy_vwap` | blocked | Proxy-VWAP signals are research-only until real VWAP data exists. | `review_packs/blocked_lanes/alpha101_blocked_lanes_pack.md` | Real VWAP source and contract are documented. |
| `snapshot_industry_metadata` | blocked | Current industry metadata is snapshot-based, not point-in-time. | `point_in_time_industry_metadata_lane.md` | Point-in-time industry history is available. |
| `broad_universe_degradation` | blocked | Results degrade outside `high_vol_top100` under the current contract. | `broad_universe_capacity_bridge.md` | Capacity evidence survives the broader universe. |

## Legacy Lanes

- `missing_cap`: blocked in the legacy state and still untestable with the current cache.
- `baseline_alpha001`: reference only; retained for comparison only.

## Resolved Packaging Lane

- `review_pack_commitment`: resolved. The committed review packs now exist.
  - `review_packs/positive_focus/alpha101_positive_focus_pack.md`
  - `review_packs/blocked_lanes/alpha101_blocked_lanes_pack.md`
