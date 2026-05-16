# Native Postgres

This directory holds the native WSL/Linux deployment assets for the central Postgres path.

## Layout

- `init/001_market_raw_schema.sql`
- `init/002_mft_schema.sql`
- `scripts/install_postgres_ubuntu.sh`
- `scripts/init_database.sh`
- `scripts/reset_local_database.sh`
- `scripts/healthcheck.sh`

## Recommended WSL Setup

1. Enable systemd in WSL if it is not already active:

```ini
[boot]
systemd=true
```

2. Restart WSL from Windows:

```powershell
wsl --shutdown
```

3. Install PostgreSQL on Ubuntu:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

The helper script `scripts/install_postgres_ubuntu.sh` runs the same install steps.

## Database Contract

- Database name: `mft_platform`
- Schemas: `market_raw`, `mft`
- Raw lineage lives in `market_raw`
- Research and strategy data live in `mft`

## Bootstrap

Use `scripts/init_database.sh` after PostgreSQL is running.
The script creates the database and applies the committed SQL init files.

Use `scripts/healthcheck.sh` to verify that Postgres is reachable and that the
required schemas and `market_raw.ohlcv_deduplicated` view exist.

## Reset

`scripts/reset_local_database.sh` is destructive.
Set `RESET_CONFIRM=yes` before running it.
