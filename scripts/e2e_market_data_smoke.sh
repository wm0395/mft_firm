#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/e2e_market_data_smoke.sh SYMBOL [RESOLUTION] [HYPOTHESIS_ID]

Defaults:
- RESOLUTION: 1d
- HYPOTHESIS_ID: hypothesis:rsi_mean_reversion

The script seeds a deterministic OHLCV blob into the real collector checkout,
invokes the collector CLI offload path into Postgres, syncs the rows into a
temporary mft_firm DuckDB database, runs the batch pipeline, and then runs one
backtest.

Override the collector checkout with MARKET_COLLECTOR_DIR if needed. The
default is ~/Investment/market_collector.
Override the collector Python with MARKET_COLLECTOR_PYTHON if needed. The
default is the venv interpreter in the collector checkout.
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

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
esac

SYMBOL="${1:-}"
RESOLUTION="${2:-1d}"
HYPOTHESIS_ID="${3:-hypothesis:rsi_mean_reversion}"

[ -n "$SYMBOL" ] || { usage >&2; exit 1; }
command -v python >/dev/null 2>&1 || die "required command not found: python"
: "${MARKET_DB_URL:?MARKET_DB_URL is required}"
[ -x "$COLLECTOR_PYTHON" ] || die "collector Python not found: $COLLECTOR_PYTHON"
[ -d "$COLLECTOR_SRC/market_collector" ] || die "collector checkout not found: $COLLECTOR_DIR"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

MFT_DB="$tmpdir/e2e_market_data_smoke.duckdb"
COLLECTOR_STATE="$tmpdir/collector_state"
COLLECTOR_CONFIG="$COLLECTOR_STATE/config.toml"

collector_cli() {
  PYTHONPATH="$COLLECTOR_SRC${PYTHONPATH:+:$PYTHONPATH}" \
    "$COLLECTOR_PYTHON" -m market_collector --config "$COLLECTOR_CONFIG" "$@"
}

cd "$ROOT_DIR"
"$ROOT_DIR/scripts/check_data_pipeline.sh" --database "$MFT_DB"

collector_cli init --yes --force

python - "$COLLECTOR_STATE" "$SYMBOL" "$RESOLUTION" <<'PY'
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
import sys

import duckdb

state_root = Path(sys.argv[1])
symbol = sys.argv[2].upper()
resolution = sys.argv[3]

object_id = f"smoke-{symbol.lower()}-{resolution}"
blob_path = state_root / "blobs" / object_id[:2] / f"{object_id}.parquet"
blob_path.parent.mkdir(parents=True, exist_ok=True)

config_path = state_root / "config.toml"
config_path.write_text(
    f"""[service]
name = "market-collector"
version = "1.0.0"
state_dir = "{state_root}"
log_level = "info"

[sources.yahoo]
enabled = true
base_url = "https://query1.finance.yahoo.com"
rate_limit_rps = 1.5
connect_timeout_sec = 10
read_timeout_sec = 30
max_retries = 3

[sources.alphavantage]
enabled = false
api_key_env = "ALPHAVANTAGE_API_KEY"
base_url = "https://www.alphavantage.co"
rate_limit_rps = 0.1
connect_timeout_sec = 10
read_timeout_sec = 30
max_retries = 3

[sources.polygon]
enabled = false
api_key_env = "POLYGON_API_KEY"
base_url = "https://api.polygon.io"
rate_limit_rps = 0.2
connect_timeout_sec = 10
read_timeout_sec = 30
max_retries = 3

[storage]
compress_raw = true
raw_retention_days = 7
blob_target_size_mb = 50
blob_max_size_mb = 100
blob_max_rows = 100000

[offload]
backend = "postgres"
db_path = "market.duckdb"
database_url_env = "MARKET_DB_URL"
retry_interval_sec = 300
max_retry_attempts = 10
batch_size = 1000
auto_cleanup_after_offload = false

[schedule]
default_fetch_time = "09:00"
timezone = "America/New_York"

[features]
enable_signing = false
enable_raw_storage = false
enable_metrics_export = false
""",
    encoding="utf-8",
)

connection = duckdb.connect()
try:
    connection.execute(
        """
        create table rows (
            symbol varchar,
            exchange varchar,
            ts timestamp,
            open double,
            high double,
            low double,
            close double,
            volume double,
            source varchar,
            resolution varchar,
            ingest_ts timestamp
        )
        """
    )
    rows: list[tuple[object, ...]] = []
    start = datetime(2026, 5, 1)
    for index in range(21):
        ts = start + timedelta(days=index)
        close = 100.0 - index
        rows.append(
            (
                symbol,
                "NASDAQ",
                ts,
                close + 1.0,
                close + 2.0,
                close - 1.0,
                close,
                1000.0 + index,
                "yahoo",
                resolution,
                ts + timedelta(minutes=1),
            )
        )
    connection.executemany(
        "insert into rows values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    target = blob_path.as_posix().replace("'", "''")
    connection.execute(f"copy rows to '{target}' (format parquet)")
finally:
    connection.close()

created = {
    "event": "created",
    "object_id": object_id,
    "ts": datetime.now(UTC).replace(microsecond=0).isoformat(),
    "size_bytes": blob_path.stat().st_size,
    "symbols": [symbol],
    "date_range": {"start": "2026-05-01", "end": "2026-05-21"},
    "source": "yahoo",
    "resolution": resolution,
    "source_state_dir": str(state_root),
}
manifest_path = state_root / "manifest.jsonl"
with manifest_path.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(created, sort_keys=True) + "\n")
PY

collector_cli stocks add "$SYMBOL" --exchange NASDAQ
collector_cli healthcheck
collector_cli verify
collector_cli offload

python - "$ROOT_DIR" "$SYMBOL" "$RESOLUTION" "$HYPOTHESIS_ID" "$MFT_DB" <<'PY'
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import psycopg

root = Path(sys.argv[1])
symbol = sys.argv[2].upper()
resolution = sys.argv[3]
hypothesis_id = sys.argv[4]
mft_db = Path(sys.argv[5])
market_db_url = os.environ["MARKET_DB_URL"]


def run_main(*args: str) -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, "project/main.py", *args, "--database", str(mft_db)],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{' '.join(args)} failed:\n"
            + (proc.stderr.strip() or proc.stdout.strip() or "<no output>")
        )
    return json.loads(proc.stdout)


sync_result = run_main(
    "sync-market-data",
    "--symbol",
    symbol,
    "--resolution",
    resolution,
    "--market-db-url-env",
    "MARKET_DB_URL",
)
synced_rows = int(sync_result["result"]["rows_loaded"][symbol])
expected_rows = 21
if synced_rows != expected_rows:
    raise RuntimeError(f"sync-market-data loaded {synced_rows} rows, expected {expected_rows}")

with psycopg.connect(market_db_url) as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            select count(*), min(ts), max(ts)
            from market_raw.ohlcv_deduplicated
            where upper(symbol) = upper(%s) and resolution = %s
            """,
            (symbol, resolution),
        )
        count, start_ts, end_ts = cur.fetchone()

if count != expected_rows:
    raise RuntimeError(f"collector offload produced {count} rows, expected {expected_rows}")

run_batch_result = run_main("run-batch", symbol)
if int(run_batch_result["result"]["signals"]) <= 0:
    raise RuntimeError("run-batch did not produce any signals")
if int(run_batch_result["result"]["trade_ideas"]) <= 0:
    raise RuntimeError("run-batch did not produce any trade ideas")

start_date = start_ts.date().isoformat()
end_date = end_ts.date().isoformat()
backtest_result = run_main(
    "backtest-hypothesis",
    hypothesis_id,
    symbol,
    start_date,
    end_date,
)
if backtest_result["result"]["asset_id"] != f"asset:{symbol}":
    raise RuntimeError("backtest-hypothesis ran against the wrong asset")
if backtest_result["result"]["hypothesis_id"] != hypothesis_id:
    raise RuntimeError("backtest-hypothesis ran against the wrong hypothesis")

print(
    json.dumps(
        {
            "backtest_trades": backtest_result["result"]["total_trades"],
            "hypothesis_id": hypothesis_id,
            "offloaded_rows": count,
            "resolution": resolution,
            "signals": run_batch_result["result"]["signals"],
            "status": "ok",
            "symbol": symbol,
            "synced_rows": synced_rows,
            "trade_ideas": run_batch_result["result"]["trade_ideas"],
        },
        indent=2,
        sort_keys=True,
    )
)
PY
