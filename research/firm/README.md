# Research Firm Control Room

The control room is the bounded operating surface for the research factory.
The canonical Alpha101 state is
`research/projects/alpha101_formulaic_alphas/research_state.json`.

## Current Alpha101 Snapshot

- Project: `alpha101-formulaic-alphas`
- Status: `draft`
- Phase: late-stage discovery and robustness triage
- Exact-OHLCV historical queue: `28`
- Batch-1 promotions: `11`
- Batch-2 near-misses: `17`
- Strict-liquidity baseline median active Sharpe: `-1.0911`
- Positive-Sharpe rate: `14.29%`
- Validation pass rate: `nan`
- Validation failures reported: `0`
- Focus queue: `alpha024`, `alpha018`, `alpha040`, `alpha023`
- Positive focus: `alpha024`, `alpha023`
- Borderline: `alpha018`
- Holdout: `alpha040`

## Canonical Files

- `daily_research_state.json`
- `research_queue.json`
- `vp_research_queue.md`
- `vp_data_platform_queue.md`
- `associate_data_sources_queue.md`
- `associate_asset_classes_queue.md`
- `associate_math_tools_queue.md`
- `associate_validation_ops_queue.md`
- `weekly_review_template.md`

## Rules

- Notebook output is exploratory until committed as a review pack.
- Blocked lanes stay blocked until the data contract changes.
- Promotion requires evidence, capacity, and an explicit review artifact.
