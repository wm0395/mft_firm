from __future__ import annotations


SCHEMA_SQL = (
    """
    create table if not exists assets (
        asset_id varchar primary key,
        symbol varchar not null unique,
        name varchar not null,
        sector varchar not null,
        market varchar not null,
        is_active boolean not null,
        created_at varchar not null
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
    create table if not exists signals (
        signal_id varchar primary key,
        asset_id varchar not null,
        timestamp varchar not null,
        signal_type varchar not null,
        value double not null,
        metadata_json varchar not null,
        is_persistent boolean not null,
        unique(asset_id, timestamp, signal_type)
    )
    """,
    """
    create table if not exists signal_registry (
        signal_type varchar primary key,
        category varchar not null,
        definition varchar not null,
        dependencies_json varchar not null,
        is_persistent boolean not null,
        version integer not null
    )
    """,
    """
    create table if not exists hypotheses (
        hypothesis_id varchar primary key,
        name varchar not null,
        version integer not null,
        definition_json varchar not null,
        explainability_level varchar not null,
        status varchar not null
    )
    """,
    """
    create table if not exists hypothesis_signal_map (
        hypothesis_id varchar not null,
        signal_type varchar not null,
        role varchar not null,
        primary key(hypothesis_id, signal_type)
    )
    """,
    """
    create table if not exists backtests (
        backtest_id varchar primary key,
        hypothesis_id varchar not null,
        hypothesis_version integer not null,
        metrics_json varchar not null
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
        created_at varchar not null
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
        notes varchar not null,
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


REQUIRED_TABLES = {
    "assets",
    "raw_data",
    "signals",
    "signal_registry",
    "hypotheses",
    "hypothesis_signal_map",
    "backtests",
    "hypothesis_evaluations",
    "trade_ideas",
    "decisions",
    "positions",
}
