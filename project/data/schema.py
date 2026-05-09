from __future__ import annotations


SCHEMA_SQL = (
    """
    create table if not exists raw_market_data (
        asset_symbol TEXT,
        timestamp TIMESTAMP,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume DOUBLE
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


