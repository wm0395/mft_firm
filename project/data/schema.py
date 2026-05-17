from __future__ import annotations


REQUIRED_TABLES = {
    "assets",
    "approval_events",
    "backtests",
    "decisions",
    "parameter_results",
    "parameter_sets",
    "hypotheses",
    "hypothesis_evaluations",
    "hypothesis_signal_map",
    "positions",
    "raw_data",
    "raw_market_data",
    "research_artifacts",
    "research_projects",
    "research_runs",
    "research_universes",
    "signal_evaluations",
    "signal_registry",
    "signals",
    "strategy_evidence_summaries",
    "strategy_candidates",
    "strategy_specs",
    "strategy_versions",
    "trade_ideas",
    "dataset_snapshots",
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
    create table if not exists research_universes (
        universe_id varchar primary key,
        name varchar not null,
        market varchar not null,
        description varchar not null,
        asset_ids_json varchar not null
    )
    """,
    """
    create table if not exists research_projects (
        project_id varchar primary key,
        name varchar not null,
        description varchar not null,
        status varchar not null,
        created_at varchar not null,
        updated_at varchar not null
    )
    """,
    """
    create table if not exists research_artifacts (
        artifact_id varchar primary key,
        project_id varchar not null,
        research_run_id varchar,
        artifact_type varchar not null,
        payload_json varchar not null,
        content_hash varchar not null,
        created_at varchar not null
    )
    """,
    """
    create table if not exists dataset_snapshots (
        dataset_snapshot_id varchar primary key,
        universe_id varchar not null,
        captured_at varchar not null,
        data_start varchar not null,
        data_end varchar not null,
        asset_ids_json varchar not null
    )
    """,
    """
    create table if not exists strategy_specs (
        strategy_spec_id varchar primary key,
        universe_id varchar not null,
        hypothesis_id varchar not null,
        hypothesis_version integer not null,
        name varchar not null,
        parameters_json varchar not null
    )
    """,
    """
    create table if not exists research_runs (
        research_run_id varchar primary key,
        strategy_spec_id varchar not null,
        dataset_snapshot_id varchar not null,
        started_at varchar not null,
        completed_at varchar,
        status varchar not null,
        notes varchar not null
    )
    """,
    """
    create table if not exists parameter_sets (
        parameter_set_id varchar primary key,
        project_id varchar not null,
        strategy_version_id varchar not null,
        parameters_json varchar not null,
        parameters_hash varchar not null,
        created_at varchar not null
    )
    """,
    """
    create table if not exists parameter_results (
        parameter_result_id varchar primary key,
        parameter_set_id varchar not null,
        metric_name varchar not null,
        metric_value double not null,
        created_at varchar not null
    )
    """,
    """
    create table if not exists strategy_versions (
        strategy_version_id varchar primary key,
        project_id varchar not null,
        version integer not null,
        definition_json varchar not null,
        status varchar not null,
        created_at varchar not null,
        updated_at varchar not null
    )
    """,
    """
    create table if not exists strategy_candidates (
        candidate_id varchar primary key,
        project_id varchar not null,
        strategy_version_id varchar not null,
        label varchar not null,
        status varchar not null,
        created_at varchar not null,
        promoted_at varchar
    )
    """,
    """
    create table if not exists approval_events (
        approval_event_id varchar primary key,
        project_id varchar not null,
        candidate_id varchar not null,
        event_type varchar not null,
        actor varchar not null,
        reason varchar not null,
        created_at varchar not null
    )
    """,
    """
    create table if not exists strategy_evidence_summaries (
        evidence_summary_id varchar primary key,
        strategy_spec_id varchar not null,
        research_run_id varchar not null,
        dataset_snapshot_id varchar not null,
        summary varchar not null,
        metrics_json varchar not null,
        created_at varchar not null
    )
    """,
    """
    create table if not exists signals (
        signal_id varchar primary key,
        asset_id varchar not null,
        timestamp varchar not null,
        signal_type varchar not null,
        raw_reference varchar not null,
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
        research_run_id varchar,
        strategy_spec_id varchar,
        dataset_snapshot_id varchar,
        hypothesis_id varchar not null,
        asset_id varchar not null,
        hypothesis_version integer not null,
        start_timestamp varchar,
        end_timestamp varchar,
        parameters_json varchar not null,
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
        signals_snapshot_json varchar not null,
        timestamp varchar not null
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


UPSERT_RESEARCH_UNIVERSE_SQL = """
insert into research_universes values (?, ?, ?, ?, ?)
on conflict(universe_id) do update set
    name = excluded.name,
    market = excluded.market,
    description = excluded.description,
    asset_ids_json = excluded.asset_ids_json
"""

UPSERT_RESEARCH_ARTIFACT_SQL = """
insert into research_artifacts values (?, ?, ?, ?, ?, ?, ?)
on conflict(artifact_id) do update set
    project_id = excluded.project_id,
    research_run_id = excluded.research_run_id,
    artifact_type = excluded.artifact_type,
    payload_json = excluded.payload_json,
    content_hash = excluded.content_hash,
    created_at = excluded.created_at
"""

UPSERT_DATASET_SNAPSHOT_SQL = """
insert into dataset_snapshots values (?, ?, ?, ?, ?, ?)
on conflict(dataset_snapshot_id) do update set
    universe_id = excluded.universe_id,
    captured_at = excluded.captured_at,
    data_start = excluded.data_start,
    data_end = excluded.data_end,
    asset_ids_json = excluded.asset_ids_json
"""


UPSERT_STRATEGY_SPEC_SQL = """
insert into strategy_specs values (?, ?, ?, ?, ?, ?)
on conflict(strategy_spec_id) do update set
    universe_id = excluded.universe_id,
    hypothesis_id = excluded.hypothesis_id,
    hypothesis_version = excluded.hypothesis_version,
    name = excluded.name,
    parameters_json = excluded.parameters_json
"""


UPSERT_RESEARCH_RUN_SQL = """
insert into research_runs values (?, ?, ?, ?, ?, ?, ?)
on conflict(research_run_id) do update set
    strategy_spec_id = excluded.strategy_spec_id,
    dataset_snapshot_id = excluded.dataset_snapshot_id,
    started_at = excluded.started_at,
    completed_at = excluded.completed_at,
    status = excluded.status,
    notes = excluded.notes
"""
UPSERT_STRATEGY_EVIDENCE_SUMMARY_SQL = """
insert into strategy_evidence_summaries values (?, ?, ?, ?, ?, ?, ?)
on conflict(evidence_summary_id) do update set
    strategy_spec_id = excluded.strategy_spec_id,
    research_run_id = excluded.research_run_id,
    dataset_snapshot_id = excluded.dataset_snapshot_id,
    summary = excluded.summary,
    metrics_json = excluded.metrics_json,
    created_at = excluded.created_at
"""


UPSERT_HYPOTHESIS_SQL = """
insert into hypotheses values (?, ?, ?, ?, ?, ?)
on conflict(hypothesis_id) do update set
    name = excluded.name,
    version = excluded.version,
    definition_json = excluded.definition_json,
    explainability_level = excluded.explainability_level,
    status = excluded.status
"""


UPSERT_SIGNAL_REGISTRY_SQL = """
insert into signal_registry values (?, ?, ?, ?, ?, ?)
on conflict(signal_type) do update set
    category = excluded.category,
    definition = excluded.definition,
    dependencies_json = excluded.dependencies_json,
    is_persistent = excluded.is_persistent,
    version = excluded.version
"""
