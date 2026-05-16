# Research Runs

Milestone 6 makes strategy backtests auditable.
The research runner now binds every result to an explicit dataset snapshot,
strategy spec, and research run record instead of relying on whatever market
state happens to be present at runtime.

## Core Contract

Dataset snapshots are the data contract for research.
They define:

- `dataset_snapshot_id`
- `universe_id`
- `data_start`
- `data_end`
- `asset_ids`

Strategy research uses that snapshot as its fixed input boundary.

## Research Run Flow

`run-strategy-research` does the following:

1. Loads the requested dataset snapshot.
2. Verifies the requested asset is included in the snapshot.
3. Verifies the requested date range is inside the snapshot range.
4. Creates or upserts the matching `StrategySpec`.
5. Creates a `ResearchRun` with status `running`.
6. Runs the existing `BacktestEngine`.
7. Persists the backtest result with audit context.
8. Persists a `StrategyEvidenceSummary`.
9. Marks the `ResearchRun` as `completed`.

If a failure happens after the run is created, the runner marks that run as
`failed` and stores the failure notes where possible.

## Example

```bash
python project/main.py run-strategy-research \
  --dataset-snapshot-id dataset_snapshot:us-largecap-daily-v1:2024-01-01:2026-05-15 \
  --hypothesis-id hypothesis:rsi_mean_reversion \
  --asset-symbol AAPL \
  --start-date 2024-01-01 \
  --end-date 2026-05-15
```

Optional backtest controls:

- `--slippage-bps`
- `--position-size`
- `--exit-horizon`

## Persisted Audit Context

Successful runs now carry the full trace back to the dataset snapshot:

- `research_run_id`
- `strategy_spec_id`
- `dataset_snapshot_id`
- `hypothesis_id`
- `asset_id`
- date range
- backtest parameters

That makes the backtest result repeatable and inspectable without guessing
which data was in the database at the time of execution.
