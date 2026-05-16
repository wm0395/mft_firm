create schema if not exists mft;

create table if not exists mft.assets (
    asset_id text primary key,
    symbol text not null,
    name text not null,
    sector text,
    market text not null,
    is_active boolean not null,
    created_at timestamptz not null
);

create table if not exists mft.raw_market_data (
    id text primary key,
    asset_symbol text not null,
    timestamp timestamptz not null,
    open double precision not null,
    high double precision not null,
    low double precision not null,
    close double precision not null,
    volume double precision not null,
    unique (asset_symbol, timestamp)
);

create table if not exists mft.raw_data (
    data_id text primary key,
    asset_id text not null,
    timestamp timestamptz not null,
    data_type text not null,
    value_json text not null,
    source text not null,
    unique (asset_id, timestamp, data_type, source)
);

create table if not exists mft.signals (
    signal_id text primary key,
    asset_id text not null,
    timestamp timestamptz not null,
    signal_type text not null,
    raw_reference text not null,
    value double precision not null,
    metadata_json text,
    is_persistent boolean not null
);

create table if not exists mft.signal_registry (
    signal_type text primary key,
    category text not null,
    definition text not null,
    dependencies_json text,
    is_persistent boolean not null,
    version integer not null
);

create table if not exists mft.hypothesis_evaluations (
    evaluation_id text primary key,
    asset_id text not null,
    hypothesis_id text not null,
    hypothesis_version integer not null,
    timestamp timestamptz not null,
    direction text not null,
    confidence double precision not null,
    signals_snapshot_json text not null,
    explanation_json text not null,
    generated_trade_idea boolean not null,
    validation_result_json text,
    created_at timestamptz not null,
    experiment_id text,
    research_run_id text,
    dataset_snapshot_id text
);

create table if not exists mft.signal_evaluations (
    signal_id text primary key,
    hypothesis_id text not null,
    forward_return_1 double precision,
    forward_return_5 double precision,
    forward_return_20 double precision,
    evaluation_timestamp timestamptz not null
);

create table if not exists mft.backtests (
    backtest_id text primary key,
    hypothesis_id text not null,
    asset_id text not null,
    hypothesis_version integer not null,
    metrics_json text not null
);

create table if not exists mft.hypotheses (
    hypothesis_id text primary key,
    name text not null,
    version integer not null,
    definition_json text not null,
    explainability_level text,
    status text
);

create table if not exists mft.hypothesis_signal_map (
    hypothesis_id text not null,
    signal_type text not null,
    role text,
    primary key (hypothesis_id, signal_type)
);

create table if not exists mft.trade_ideas (
    trade_id text primary key,
    asset_id text not null,
    hypothesis_id text not null,
    version integer not null,
    direction text not null,
    confidence double precision not null,
    signals_snapshot_json text not null,
    timestamp timestamptz not null
);

create table if not exists mft.decisions (
    decision_id text primary key,
    trade_id text not null,
    action text not null,
    structured_reason text not null,
    notes text,
    created_at timestamptz not null
);

create table if not exists mft.positions (
    position_id text primary key,
    trade_id text not null,
    entry_price double precision not null,
    exit_price double precision,
    pnl double precision,
    status text not null
);
