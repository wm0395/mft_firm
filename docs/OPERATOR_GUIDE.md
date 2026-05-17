# Operator Guide

This guide is the workflow-oriented entry point for operating `mft_project`.

## Start Here

1. `python project/main.py doctor`
2. `python project/main.py init-db`
3. `python project/main.py workflow-status`
4. `python project/main.py next-steps`

## Market Data Workflow

Preferred path when Postgres is available:

1. `sync-market-data`
2. `data-quality-report`
3. `create-dataset-snapshot`

If you already have a DuckDB export from a separate collector checkout, use:

1. `load-market-collector`
2. `data-quality-report`
3. `create-dataset-snapshot`

## Research Workflow

1. `run-strategy-research`
2. `hypothesis-readiness`
3. `promote-hypothesis`

Use `list-hypotheses`, `show-hypothesis`, and `validate-hypothesis` when you need the current registry state.

## Inspection Workflow

The inspection commands are read-only and emit the same JSON envelope as mutating commands:

- `show-trade-idea`
- `show-validation-path`
- `show-explanation`
- `show-validation-failures`
- `show-hypothesis-evaluations`
- `report-hypotheses`
- `backtest-results`
- `hypothesis-performance`
- `advanced-report`

## Data Quality

`data-quality-report` is an inspection command by default. It returns a JSON report and exits `0` unless the command itself fails.

Use `--strict` when you want the command to behave like a gate and return non-zero for a failing report.

## Workflow Status

`workflow-status` summarizes:

- database readiness
- asset count
- market row count
- dataset snapshot count
- active, testing, and draft hypothesis counts
- latest backtest and research run
- the next recommended command

## Doctor

`doctor` checks:

- schema initialization
- asset count
- raw market and raw data counts
- signal registry and hypothesis counts
- dataset snapshot count
- `MARKET_DB_URL` presence and Postgres visibility of `market_raw.ohlcv_deduplicated`

## Output Contract

Every CLI command emits:

```json
{
  "command": "...",
  "status": "ok|warn|fail|error",
  "result": {},
  "warnings": [],
  "error": null
}
```

## Troubleshooting

- If `doctor` reports `schema_initialized=fail`, run `init-db`.
- If `sync-market-data` fails, verify `MARKET_DB_URL` and the `market_raw.ohlcv_deduplicated` relation.
- If `data-quality-report` returns `fail`, inspect the symbol-level issues before snapshotting.
- If `hypothesis-readiness` returns `not_ready`, inspect the missing evidence list and the validation errors.
