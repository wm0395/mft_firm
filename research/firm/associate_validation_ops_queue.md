# Associate Validation Ops Queue

## Objective

Keep validation, review packs, and state files synchronized.

## Files

- `research/firm/research_queue.json`
- `research/firm/daily_research_state.json`
- `research/projects/alpha101_formulaic_alphas/research_state.json`
- `research/projects/alpha101_formulaic_alphas/review_packs/README.md`
- `research/projects/alpha101_formulaic_alphas/review_packs/positive_focus/alpha101_positive_focus_pack.md`
- `research/projects/alpha101_formulaic_alphas/review_packs/blocked_lanes/alpha101_blocked_lanes_pack.md`
- `research/projects/alpha101_formulaic_alphas/point_in_time_industry_metadata_lane.md`
- `research/projects/alpha101_formulaic_alphas/broad_universe_capacity_bridge.md`

## Constraints

- Notebook outputs are exploratory until committed as review packs.
- Review packs must be reviewable without opening notebooks.
- State files are canonical for machine-readable status.
- Reports should come from canonical files, not ad hoc notes.

## Done Conditions

- Review packs exist and are committed.
- State files stay current.
- Reports can be generated from canonical artifacts.
- Promotion and demotion evidence is explicit.

## Queue

1. Keep the review pack layout explicit.
2. Keep the loop report and capacity audit aligned with state.
3. Keep the next queue aligned with blockers and focus names.
4. Keep committed review packs visible in the control room.
