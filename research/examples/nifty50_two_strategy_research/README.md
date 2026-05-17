# NIFTY50 Two-Strategy Research

This example is the opinionated starter workflow for the first research pass.
It keeps the project code canonical and uses the CLI to run the actual
parameter sweep.

## Files

- `configs/universe.yaml`
- `configs/dataset_snapshot.yaml`
- `configs/momentum_continuation_grid.yaml`
- `configs/mean_reversion_grid.yaml`
- `configs/research_run.yaml`

## Quickstart

1. Initialize the database.
2. Load or sync the NIFTY50 fixture data.
3. Create the dataset snapshot referenced by `configs/dataset_snapshot.yaml`.
4. Create the research project.
5. Run the research pack:

```bash
python project/main.py run-parameter-research \
  --research-run-config research/examples/nifty50_two_strategy_research/configs/research_run.yaml \
  --database <path-to-duckdb>
```

6. Review the generated artifacts under `reports/research/<project_id>/<research_run_id>/`.
7. Promote the selected candidate with `promote-strategy-candidate`.
