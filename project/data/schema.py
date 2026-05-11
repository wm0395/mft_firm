from __future__ import annotations


REQUIRED_TABLES = {
    "assets",
    "backtests",
    "decisions",
    "hypotheses",
    "hypothesis_evaluations",
    "hypothesis_signal_map",
    "positions",
    "raw_data",
    "raw_market_data",
    "signal_evaluations",
    "signal_registry",
    "signals",
    "trade_ideas",
}


SCHEMA_SQL = (
    """
    create table if not exists raw_market_data (
        id varchar primary key,
        asset_symbol text not null,
        timestamp timestamp not null,
        open double not null,
        high double not null,
        low double not null,
        close double not null,
        volume double not null,
        unique(asset_symbol, timestamp)
    )
    """,
    """
    create table if not exists raw_data (
        data_id varchar primary key,
        asset_id varchar not null,
        timestamp varchar not null,
        data_type varchar not null,
        value_json varchar not null,
        source varchar not null,
        unique(asset_id, timestamp, data_type, source)
    )
    """,
    """
    create table if not exists assets (
        asset_id varchar primary key,
        symbol varchar not null,
        name varchar not null,
        sector varchar,
        market varchar not null,
        is_active boolean not null,
        created_at varchar not null
    )
    """,
    """
    create table if not exists signals (
        signal_id varchar primary key,
        asset_id varchar not null,
        timestamp varchar not null,
        signal_type varchar not null,
        value double not null,
        metadata_json varchar,
        is_persistent boolean not null
    )
    """,
    """
    create table if not exists signal_registry (
        signal_type varchar primary key,
        category varchar not null,
        definition varchar not null,
        dependencies_json varchar,
        is_persistent boolean not null,
        version integer not null
    )
    """,
    """
    create table if not exists hypothesis_evaluations (
        evaluation_id varchar primary key,
        asset_id varchar not null,
        hypothesis_id varchar not null,
        hypothesis_version integer not null,
        timestamp varchar not null,
        direction varchar not null,
        confidence double not null,
        signals_snapshot_json varchar not null,
        explanation_json varchar not null,
        generated_trade_idea boolean not null,
        validation_result_json varchar,
        created_at varchar not null,
        experiment_id varchar,
        research_run_id varchar,
        dataset_snapshot_id varchar
    )
    """,
    """
    create table if not exists signal_evaluations (
        signal_id varchar primary key,
        hypothesis_id varchar not null,
        forward_return_1 double,
        forward_return_5 double,
        forward_return_20 double,
        evaluation_timestamp varchar not null
    )
    """,
    """
    create table if not exists backtests (
        backtest_id varchar primary key,
        hypothesis_id varchar not null,
        asset_id varchar not null,
        hypothesis_version integer not null,
        metrics_json varchar not null
    )
    """,
    """
    create table if not exists hypotheses (
        hypothesis_id varchar primary key,
        name varchar not null,
        version integer not null,
        definition_json varchar not null,
        explainability_level varchar,
        status varchar
    )
    """,
    """
    create table if not exists hypothesis_signal_map (
        hypothesis_id varchar not null,
        signal_type varchar not null,
        role varchar,
        primary key (hypothesis_id, signal_type)
    )
    """,
    """
    create table if not exists trade_ideas (
        trade_id varchar primary key,
        asset_id varchar not null,
        hypothesis_id varchar not null,
        version integer not null,
        direction varchar not null,
        confidence double not null,
        signals_snapshot_json varchar not null
    )
    """,
    """
    create table if not exists decisions (
        decision_id varchar primary key,
        trade_id varchar not null,
        action varchar not null,
        structured_reason varchar not null,
        notes varchar,
        created_at varchar not null
    )
    """,
    """
    create table if not exists positions (
        position_id varchar primary key,
        trade_id varchar not null,
        entry_price double not null,
        exit_price double,
        pnl double,
        status varchar not null
    )
    """,
)
