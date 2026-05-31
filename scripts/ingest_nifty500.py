from __future__ import annotations

from pathlib import Path
from datetime import datetime, UTC

import duckdb


DATA_DIR = Path("research/data/nifty500_high_vol")
DB_PATH = "project_mft.duckdb"
CSV_FILES = ["open", "high", "low", "close", "volume"]


def _get_double_cols(con: duckdb.DuckDBPyConnection, csv_path: str) -> list[str]:
    cols = con.execute(
        "select column_name, column_type "
        "from (describe select * from read_csv_auto(?))",
        (csv_path,),
    ).fetchall()
    return [c for c, t in cols if t == "DOUBLE"]


def main() -> None:
    con = duckdb.connect(DB_PATH)

    existing_market = con.execute("SELECT count(*) FROM raw_market_data").fetchone()[0]
    existing_raw = con.execute("SELECT count(*) FROM raw_data").fetchone()[0]
    existing_assets = con.execute("SELECT count(*) FROM assets").fetchone()[0]
    print(f"Existing DB — market_data: {existing_market:,}  raw_data: {existing_raw:,}  assets: {existing_assets}")

    # --- Get double columns from a reference CSV ---
    ref_csv = str((DATA_DIR / "open.csv").resolve())
    double_cols = _get_double_cols(con, ref_csv)
    cols_str = ", ".join(f'"{c}"' for c in double_cols)
    print(f"\nSymbol columns: {len(double_cols)} (non-DOUBLE skipped)")

    # --- Step 1: Build unpivoted views for each OHLCV field ---
    print("Building unpivoted market data in DuckDB...")
    for name in CSV_FILES:
        csv_path = str((DATA_DIR / f"{name}.csv").resolve())
        con.execute(f"""
            create or replace temp table raw_{name} as
            select * from read_csv_auto('{csv_path}', header=true, dateformat='%Y-%m-%d')
        """)
        con.execute(f"""
            create or replace temp view {name}_v as
            unpivot raw_{name}
            on {cols_str}
            into name symbol value {name}
        """)

    # Merge all 5 into a single clean long table
    con.execute("""
        create or replace temp view merged as
        select
            o."Date" as ts,
            o.symbol,
            o.open,
            h.high,
            l.low,
            c.close,
            v.volume
        from open_v o
        join high_v h   on o."Date" = h."Date" and o.symbol = h.symbol
        join low_v l    on o."Date" = l."Date" and o.symbol = l.symbol
        join close_v c  on o."Date" = c."Date" and o.symbol = c.symbol
        join volume_v v on o."Date" = v."Date" and o.symbol = v.symbol
    """)

    row_count = con.execute("select count(*) from merged").fetchone()[0]
    symbol_count = con.execute("select count(distinct symbol) from merged").fetchone()[0]
    date_range = con.execute("select min(ts), max(ts) from merged").fetchone()
    print(f"  Merged: {row_count:,} rows  {symbol_count} symbols")
    print(f"  Date range: {date_range[0]} to {date_range[1]}")

    # --- Step 2: Register assets ---
    print("\nRegistering assets...")
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    con.execute("begin")
    try:
        con.execute(f"""
            insert into assets (asset_id, symbol, name, sector, market, is_active, created_at)
            select distinct
                'asset:' || symbol,
                symbol,
                symbol,
                'equity',
                'NSE',
                true,
                '{now}'
            from merged
            on conflict(asset_id) do nothing
        """)
        con.execute("commit")
    except Exception:
        con.execute("rollback")
        raise
    new_asset_count = con.execute("SELECT count(*) FROM assets").fetchone()[0]
    print(f"  Total assets: {new_asset_count}  (added {new_asset_count - existing_assets})")

    # --- Step 3: Bulk insert raw_market_data ---
    print(f"\nIngesting raw_market_data ({row_count:,} rows)...")
    con.execute("begin")
    try:
        con.execute("""
            insert into raw_market_data
                (id, asset_symbol, timestamp, open, high, low, close, volume)
            select
                'market:' || symbol || ':' || ts::varchar,
                symbol,
                ts,
                open,
                high,
                low,
                close,
                volume
            from merged
            where open > 0 and high > 0 and low > 0 and close > 0 and volume > 0
            on conflict(id) do nothing
        """)
        con.execute("commit")
    except Exception:
        con.execute("rollback")
        raise
    new_market = con.execute("SELECT count(*) FROM raw_market_data").fetchone()[0]
    print(f"  raw_market_data now: {new_market:,}  (added {new_market - existing_market:,})")

    # --- Step 4: Bulk insert raw_data (close prices) ---
    print(f"\nIngesting raw_data close prices...")
    con.execute("begin")
    try:
        con.execute("""
            insert into raw_data
                (data_id, asset_id, timestamp, data_type, value_json, source)
            select
                'raw:asset:' || symbol || ':' || ts::varchar || ':price:nifty500_high_vol',
                'asset:' || symbol,
                ts::varchar,
                'price',
                '{"close": ' || close::varchar || '}',
                'csv:nifty500_high_vol'
            from merged
            where close > 0
            on conflict(asset_id, timestamp, data_type, source) do nothing
        """)
        con.execute("commit")
    except Exception:
        con.execute("rollback")
        raise
    new_raw = con.execute("SELECT count(*) FROM raw_data").fetchone()[0]
    print(f"  raw_data now: {new_raw:,}  (added {new_raw - existing_raw:,})")

    # --- Summary ---
    symbols_in_db = con.execute(
        "SELECT count(DISTINCT asset_symbol) FROM raw_market_data"
    ).fetchone()[0]
    total_market = con.execute("SELECT count(*) FROM raw_market_data").fetchone()[0]
    total_raw = con.execute("SELECT count(*) FROM raw_data").fetchone()[0]
    total_assets = con.execute("SELECT count(*) FROM assets").fetchone()[0]
    print(f"\n{'='*50}")
    print(f"Final summary:")
    print(f"  assets:           {total_assets}")
    print(f"  raw_market_data:  {total_market:,} rows ({symbols_in_db} symbols)")
    print(f"  raw_data:         {total_raw:,} rows")
    print(f"{'='*50}")
    con.close()


if __name__ == "__main__":
    main()
