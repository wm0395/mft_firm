create schema if not exists market_raw;

create table if not exists market_raw.collector_nodes (
    node_id text primary key,
    node_name text not null,
    platform text not null,
    created_at timestamptz not null default now(),
    last_seen_at timestamptz,
    is_active boolean not null default true
);

create table if not exists market_raw.ingest_objects (
    object_id text primary key,
    node_id text not null references market_raw.collector_nodes(node_id),
    source text not null,
    resolution text not null,
    source_uri text,
    content_hash text,
    row_count integer not null default 0,
    status text not null,
    ingested_at timestamptz not null default now()
);

create table if not exists market_raw.catalog_objects (
    object_id text primary key references market_raw.ingest_objects(object_id),
    symbol text not null,
    exchange text not null,
    resolution text not null,
    cataloged_at timestamptz not null default now()
);

create table if not exists market_raw.ohlcv (
    object_id text not null references market_raw.ingest_objects(object_id),
    source_node_id text not null references market_raw.collector_nodes(node_id),
    symbol text not null,
    exchange text not null,
    ts timestamptz not null,
    open double precision not null,
    high double precision not null,
    low double precision not null,
    close double precision not null,
    volume double precision not null,
    source text not null,
    resolution text not null,
    ingest_ts timestamptz not null,
    primary key (object_id, symbol, exchange, ts, resolution)
);

create index if not exists ohlcv_dedup_lookup_idx
    on market_raw.ohlcv (upper(symbol), upper(exchange), ts, resolution, ingest_ts desc, object_id desc);

create table if not exists market_raw.import_runs (
    import_run_id text primary key,
    node_id text not null references market_raw.collector_nodes(node_id),
    source text not null,
    resolution text not null,
    started_at timestamptz not null,
    completed_at timestamptz,
    status text not null,
    rows_written integer not null default 0,
    notes text
);

create table if not exists market_raw.import_errors (
    import_error_id text primary key,
    import_run_id text not null references market_raw.import_runs(import_run_id),
    object_id text,
    symbol text,
    exchange text,
    ts timestamptz,
    error_code text not null,
    error_message text not null,
    created_at timestamptz not null default now()
);

create or replace view market_raw.ohlcv_deduplicated as
select
    object_id,
    source_node_id,
    symbol,
    exchange,
    ts,
    open,
    high,
    low,
    close,
    volume,
    source,
    resolution,
    ingest_ts
from (
    select
        o.*,
        row_number() over (
            partition by upper(o.symbol), upper(o.exchange), o.ts, o.resolution
            order by o.ingest_ts desc, o.object_id desc
        ) as rn
    from market_raw.ohlcv o
) deduplicated
where rn = 1;
