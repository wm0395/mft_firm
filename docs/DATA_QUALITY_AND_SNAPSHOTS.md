# Data Quality And Snapshots

Milestone 5 adds a deterministic trust gate before strategy research.
The goal is to answer two questions before any hypothesis run:

1. Do the loaded bars look internally consistent?
2. What exact dataset context will future research use?

The implementation uses the existing `research_universes` and
`dataset_snapshots` tables in `mft_firm`. It does not introduce a separate
tracking system.

## Workflow

```text
sync-market-data
        ↓
data-quality-report
        ↓
create-dataset-snapshot
        ↓
run-research-batch / backtest
```

## Data Quality Report

Inspect loaded data for one or more symbols:

```bash
python project/main.py data-quality-report --symbol AAPL --resolution 1d
```

The report reads from the `mft_firm` data layer only. It checks:

- row count
- min and max timestamp
- duplicate timestamp count
- missing OHLCV values
- invalid OHLC relations
- non-positive close values
- non-positive volume values
- large timestamp gaps
- source list
- latest timestamp staleness

The output is JSON with per-symbol `status` values:

- `ok`
- `warn`
- `fail`

Hard failures prevent the dataset from being considered trustworthy. Warnings
are informational and do not block later snapshot creation.

## Create Dataset Snapshot

Create a research universe and snapshot from known loaded data:

```bash
python project/main.py create-dataset-snapshot \
  --name "us-largecap-daily-v1" \
  --market US \
  --symbol AAPL \
  --symbol MSFT \
  --data-start 2024-01-01 \
  --data-end 2026-05-15 \
  --resolution 1d
```

This command:

- resolves the symbols to existing assets
- runs the data quality checks for the selected date range
- fails if hard data errors are present
- upserts `ResearchUniverse`
- upserts `DatasetSnapshot`
- returns the stored universe and snapshot identifiers

The date inputs are normalized to UTC day boundaries before persistence:

- `data-start` becomes `T00:00:00+00:00`
- `data-end` becomes `T23:59:59+00:00`

That keeps the dataset identity deterministic and makes provenance lookups
stable.

## What Gets Stored

`ResearchUniverse` stores the universe identity, market, description, and
asset ids.

`DatasetSnapshot` stores:

- universe id
- captured timestamp
- data start
- data end
- asset ids

The existing provenance helpers can reconstruct the source list and symbol
mapping from the stored snapshot and raw data.

## Why This Matters

This milestone creates a stable handoff between data ingestion and research.
Future backtests can attach to a known dataset snapshot instead of implicitly
using whatever data happens to be present at runtime. That makes research runs
auditable and repeatable.
