# Deployment Contract

This document defines the Milestone 1 native Postgres deployment contract for `mft_firm`.
It adds a central PostgreSQL database without changing the existing DuckDB loader path yet.

## Scope

- Local deployment uses native WSL/Linux tooling.
- PostgreSQL is installed with system packages, not Docker.
- systemd manages the database and future automation.
- The first database is `mft_platform`.
- Android devices remain edge collector nodes only.
- `market_collector` remains the raw collection and lineage owner.
- `mft_firm` remains the research, signals, hypotheses, backtest, trade idea, and decision system.
- The current DuckDB import path stays supported until a later milestone.

## Files

- `infra/postgres/init/001_market_raw_schema.sql`
- `infra/postgres/init/002_mft_schema.sql`
- `infra/postgres/scripts/install_postgres_ubuntu.sh`
- `infra/postgres/scripts/init_database.sh`
- `infra/postgres/scripts/reset_local_database.sh`
- `infra/postgres/scripts/healthcheck.sh`
- `infra/postgres/README.md`
- `infra/systemd/market-data-import.service`
- `infra/systemd/market-data-import.timer`
- `infra/systemd/mft-research-worker.service`
- `infra/systemd/README.md`
- `.env.example`

## Local Startup

1. Enable systemd in WSL if needed:

```ini
[boot]
systemd=true
```

2. Restart WSL from Windows:

```powershell
wsl --shutdown
```

3. Install PostgreSQL with the helper script or the matching apt commands.
4. Copy `.env.example` to `.env`.
5. Initialize the database:

```bash
infra/postgres/scripts/init_database.sh
```

6. Run the healthcheck:

```bash
infra/postgres/scripts/healthcheck.sh
```

The init SQL runs only on first database creation. Use the reset script to rebuild a
local database:

```bash
RESET_CONFIRM=yes infra/postgres/scripts/reset_local_database.sh
```

## systemd Scope

Initial unit templates are limited to:

- `market-data-import.service`
- `market-data-import.timer`
- `mft-research-worker.service`

They are placeholders for future automation and are not wired into application code yet.

## Schema Ownership

### `market_raw`

This schema is the raw Postgres landing zone for collector output and import lineage.

Tables:

- `collector_nodes`
- `ingest_objects`
- `catalog_objects`
- `ohlcv`
- `import_runs`
- `import_errors`

View:

- `ohlcv_deduplicated`

`market_raw.ohlcv_deduplicated` returns the latest row for each
`(upper(symbol), upper(exchange), ts, resolution)` key.
It keeps the row with the newest `ingest_ts`, then the newest `object_id`.

### `mft`

This schema mirrors the current `mft_firm` core data model.

Tables:

- `assets`
- `raw_market_data`
- `raw_data`
- `signals`
- `signal_registry`
- `hypothesis_evaluations`
- `signal_evaluations`
- `backtests`
- `hypotheses`
- `hypothesis_signal_map`
- `trade_ideas`
- `decisions`
- `positions`

## Contract Rules

- Keep schema names explicit.
- Do not introduce Docker or Docker Compose.
- Do not introduce SQLAlchemy or a migration framework in this milestone.
- Do not add REST APIs.
- Do not add TimescaleDB.
- Do not remove DuckDB support.
- Do not change `market_collector` offload code yet.
- Do not change `mft_firm` loader code yet.

## Data Handling Notes

- Raw collector lineage lives in `market_raw`.
- Research and strategy artifacts live in `mft`.
- JSON payloads remain stored as serialized text in this phase to match the current application contract.
- Application code should use schema-qualified names when it starts reading from Postgres.

## Future Milestones

- `market_collector` will write to `market_raw.ohlcv`.
- `mft_firm` will read from `market_raw.ohlcv_deduplicated`.
- The existing DuckDB path remains available until that migration is complete.
