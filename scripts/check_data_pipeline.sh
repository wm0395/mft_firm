#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/check_data_pipeline.sh [--database PATH]

Checks:
- required commands are installed
- Python dependencies import cleanly
- the sibling collector checkout is present
- MARKET_DB_URL is set and Postgres is reachable
- market_raw.ohlcv and market_raw.ohlcv_deduplicated exist
- a local DuckDB mft database can be initialized

If --database is omitted, the script uses a temporary DuckDB path and removes it
on exit.
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COLLECTOR_DIR="${MARKET_COLLECTOR_DIR:-$HOME/Investment/market_collector}"
COLLECTOR_SRC="$COLLECTOR_DIR/src"
COLLECTOR_PYTHON="${MARKET_COLLECTOR_PYTHON:-$COLLECTOR_DIR/.env/bin/python}"
DB_PATH=""

while [ $# -gt 0 ]; do
  case "$1" in
    --database)
      [ $# -ge 2 ] || die "--database requires a path"
      DB_PATH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

command -v python >/dev/null 2>&1 || die "required command not found: python"
: "${MARKET_DB_URL:?MARKET_DB_URL is required}"
[ -x "$COLLECTOR_PYTHON" ] || die "collector Python not found: $COLLECTOR_PYTHON"
[ -d "$COLLECTOR_SRC/market_collector" ] || die "collector checkout not found: $COLLECTOR_DIR"

cleanup_dir=""
if [ -z "$DB_PATH" ]; then
  cleanup_dir="$(mktemp -d)"
  DB_PATH="$cleanup_dir/check_data_pipeline.duckdb"
fi
if [ -n "$cleanup_dir" ]; then
  trap 'rm -rf "$cleanup_dir"' EXIT
fi

cd "$ROOT_DIR"

PYTHONPATH="$COLLECTOR_SRC${PYTHONPATH:+:$PYTHONPATH}" \
  "$COLLECTOR_PYTHON" -m market_collector --help >/dev/null

python - "$DB_PATH" <<'PY'
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

try:
    import duckdb
    import psycopg
    from market_collector.offload.postgres_backend import PostgresOffloadBackend
    from project.data.schema import REQUIRED_TABLES
except ImportError as exc:  # pragma: no cover - environment guard
    raise RuntimeError(f"missing Python module: {exc.name}") from exc

db_path = Path(sys.argv[1])
market_db_url = os.environ["MARKET_DB_URL"]

proc = subprocess.run(
    [
        sys.executable,
        "project/main.py",
        "init-db",
        "--database",
        str(db_path),
    ],
    capture_output=True,
    text=True,
)
if proc.returncode != 0:
    raise RuntimeError(
        "failed to initialize local mft database:\n"
        + (proc.stderr.strip() or proc.stdout.strip() or "<no output>")
    )

db = duckdb.connect(str(db_path), read_only=True)
try:
    tables = {row[0] for row in db.execute("show tables").fetchall()}
finally:
    db.close()
missing_tables = sorted(REQUIRED_TABLES - tables)
if missing_tables:
    raise RuntimeError("mft database missing tables: " + ", ".join(missing_tables))

backend = PostgresOffloadBackend.open(market_db_url)
try:
    backend.ensure_schema()
finally:
    backend.close()

conn = psycopg.connect(market_db_url)
try:
    with conn.cursor() as cur:
        cur.execute(
            """
            select
                to_regclass('market_raw.ohlcv'),
                to_regclass('market_raw.ohlcv_deduplicated')
            """
        )
        ohlcv, dedup = cur.fetchone()
finally:
    conn.close()

if ohlcv != "market_raw.ohlcv":
    raise RuntimeError("missing Postgres relation market_raw.ohlcv")
if dedup != "market_raw.ohlcv_deduplicated":
    raise RuntimeError("missing Postgres relation market_raw.ohlcv_deduplicated")

print(
    json.dumps(
        {
            "database": str(db_path),
            "postgres": "market_raw.ohlcv_deduplicated",
            "status": "ok",
        },
        sort_keys=True,
    )
)
PY
