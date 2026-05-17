# Research Workspace

This workspace holds lightweight, deterministic files for research project
planning, run review, and pack export. Keep notebook use read-only and treat the
CLI as the canonical mutation path.

## Notebook-Safe Access

Notebooks may inspect:

- exported packs
- run manifests
- comparison summaries
- snapshot metadata

Notebooks should not:

- write to DuckDB
- bootstrap schema
- mutate raw or research tables
- call internal repository methods directly
- depend on live market state as implicit input

## Canonical CLI Flow

1. Build the dataset snapshot with `create-dataset-snapshot`.
2. Create the research project with `create-research-project`.
3. Run parameter sweeps with `run-parameter-research`.
4. Inspect runs with `list-research-runs` and `show-research-run`.
5. Compare runs with `compare-research-runs`.
6. Export a pack with `export-research-pack`.
7. Promote a candidate with `promote-strategy-candidate`.

The NIFTY50 starter workflow lives in
`research/examples/nifty50_two_strategy_research/`. It includes the YAML grid
files, the research-run config, and a short README with the exact command
sequence.

All commands emit the standard JSON envelope.

## Artifact Review

Review exported packs, manifests, and comparison outputs before promotion.
The pack should be treated as the reviewable record, not the notebook state.

## Workspace Tree

```text
research/
├── README.md
├── notebooks/
├── projects/
├── runs/
├── packs/
└── artifacts/
```
