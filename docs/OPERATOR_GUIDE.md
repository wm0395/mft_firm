# Operator Guide

This guide is the workflow-oriented entry point for operating `mft_project`
with the `mft` CLI and the Streamlit cockpit.

## Primary Surface

The default human operating layer is the Streamlit cockpit:

```bash
streamlit run project/ui/app.py
```

Use Mission Control first. It summarizes system health, data readiness,
research state, hypothesis readiness, trade ideas, and the next recommended
command.

If `streamlit-option-menu` is installed, the cockpit sidebar uses that modern
navigation widget and falls back to the built-in Streamlit radio when it is
not available.

## Start Here

1. `mft status`
2. `mft setup init`
3. `mft next`
4. `mft guide`

Use the cockpit for manual operation and the CLI for automation and
troubleshooting.

## Market Data Workflow

Preferred path when Postgres is available:

1. `mft data sync AAPL MSFT`
2. `mft data quality AAPL MSFT`
3. `mft data snapshot create AAPL MSFT --market US --from 2026-05-01 --to 2026-05-20`

If you already have a DuckDB export from a separate collector checkout, use the
compatibility CLI:

1. `load-market-collector`
2. `data-quality-report`
3. `create-dataset-snapshot`

## Research Workflow

1. `mft research run hypothesis:rsi_mean_reversion AAPL --snapshot latest`
2. `mft hypothesis check hypothesis:rsi_mean_reversion`
3. `mft hypothesis promote hypothesis:rsi_mean_reversion --to testing`

Use `mft hypothesis list`, `mft hypothesis check`, and `mft hypothesis validate`
when you need the current registry state.

For lifecycle work around research projects and candidates, use the
compatibility CLI commands documented in [research/README.md](../research/README.md):

- `create-research-project`
- `list-research-projects`
- `show-research-project`
- `run-parameter-research`
- `list-research-runs`
- `show-research-run`
- `compare-research-runs`
- `export-research-pack`
- `promote-strategy-candidate`

Notebook work is exploration-only. Use dataset snapshots and CLI runs as the
canonical source of truth, then review exported artifacts instead of mutating
the database from notebooks.

For the NIFTY50 starter workflow, use
`research/examples/nifty50_two_strategy_research/configs/research_run.yaml`
as the research-run entry point. It references the momentum continuation and
mean reversion grid files and keeps the CLI invocation short.

## Inspection Workflow

The inspection commands are read-only and emit the same JSON envelope as
mutating commands:

- `mft explain trade hypothesis:rsi_mean_reversion`
- `mft explain lineage --hypothesis-id hypothesis:rsi_mean_reversion`
- `mft explain signal AAPL`
- `mft report backtests`
- `mft report performance`
- `mft report rejected`
- `mft report dossier hypothesis:rsi_mean_reversion`

## Data Quality

`data-quality-report` is an inspection command by default. It returns a JSON report and exits `0` unless the command itself fails.

Use `--strict` when you want the command to behave like a gate and return non-zero for a failing report.

## Status

`mft status` summarizes:

- database readiness
- asset count
- market row count
- dataset snapshot count
- active, testing, and draft hypothesis counts
- latest backtest and research run
- the next recommended command

## Setup

`mft setup init` initializes the schema and makes the rest of the workflow
available.

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

- If the database is uninitialized, run `mft setup init`.
- If `mft data sync` fails, verify `MARKET_DB_URL` and the `market_raw.ohlcv_deduplicated` relation.
- If `mft data quality` returns `fail`, inspect the symbol-level issues before snapshotting.
- If `mft hypothesis check` returns `not_ready`, inspect the missing evidence list and the validation errors.
