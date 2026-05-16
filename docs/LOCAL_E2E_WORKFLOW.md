# Local E2E Workflow

This workflow validates the market data path before strategy work depends on it.

## What It Covers

- Postgres is reachable and the `market_raw` schema is present.
- The collector offload backend can write OHLCV rows into Postgres.
- `mft_firm` can sync from `market_raw.ohlcv_deduplicated`.
- `mft_firm` can run batch signal evaluation and backtesting on the synced data.

## Repo Layout

- The collector application checkout lives in `~/Investment/market_collector`.
- Override that location with `MARKET_COLLECTOR_DIR` if needed.
- The smoke script uses `MARKET_COLLECTOR_PYTHON` or the default
  `~/Investment/market_collector/.env/bin/python`.
- This repo keeps the Postgres backend helpers for schema and validation logic.
- The smoke script shells into the real collector CLI in the sibling checkout
  and uses a deterministic local blob so it does not depend on live Android
  collector state.

## Required Environment

- `MARKET_DB_URL` must point at the local Postgres instance.
- `MARKET_COLLECTOR_PYTHON` should point at the collector venv interpreter if
  you do not want to use the default path.
- Python dependencies must be installed in the active environment.

## Validation Commands

Run the read-only pipeline check first:

```bash
./scripts/check_data_pipeline.sh
```

Run the full smoke test next:

```bash
./scripts/e2e_market_data_smoke.sh AAPL 1d
```

The smoke script uses these stages:

1. Verify the local environment and schema checks.
2. Initialize collector state with the real `market_collector` CLI.
3. Seed a deterministic OHLCV Parquet blob into the collector state.
4. Run collector `stocks add`, `healthcheck`, `verify`, and `offload`.
5. Confirm `market_raw.ohlcv_deduplicated` returns rows for the requested
   symbol and resolution.
6. Sync the data into a temporary `mft_firm` DuckDB database.
7. Run `run-batch` for the synced asset.
8. Run `backtest-hypothesis` for the default smoke hypothesis.

## How Android Collector State Fits In

The Android collector writes into the collector app's own state directory in the
sibling `market_collector` checkout. That state is what eventually produces the
Parquet blob that gets offloaded into Postgres.

This repo does not manage the Android state directory directly. It validates the
central Postgres landing zone and the `mft_firm` read path that depends on it.

## Verifying Each Step

- Offload verification: check that `market_raw.ohlcv_deduplicated` has rows for
  the chosen symbol and resolution after the smoke seed runs.
- Sync verification: `sync-market-data` should report the same row count that
  Postgres returned.
- Strategy verification: `run-batch` should report non-zero signals and trade
  ideas.
- Backtest verification: `backtest-hypothesis` should succeed for the synced
  asset and hypothesis.

## Common Failures

- `MARKET_DB_URL is required`
  - Export the Postgres connection string in the current shell before running
    the scripts.
- `missing Python module: psycopg` or `missing Python module: duckdb`
  - Install the project dependencies into the active virtual environment.
- `missing Postgres relation market_raw.ohlcv_deduplicated`
  - Re-run the Postgres bootstrap for the local database.
- `sync-market-data loaded 0 rows`
  - The symbol or resolution does not match the offloaded rows.
- `run-batch did not produce any trade ideas`
  - The synced dataset is too small or the strategy layer changed.
