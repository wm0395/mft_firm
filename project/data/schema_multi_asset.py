from __future__ import annotations


EXTRA_REQUIRED_TABLES = {
    "asset_class_registry",
    "canonical_ohlcv",
    "contract_metadata",
    "data_quality_reports",
    "data_source_registry",
    "macro_series",
    "industry_metadata_history",
    "instruments",
    "point_in_time_metadata_status",
    "source_raw_files",
    "symbol_mappings",
    "vwap_observations",
    "universe_memberships",
}


CONTRACT_SCHEMA_SQL: tuple[str, ...] = (
    """
    create table if not exists data_source_registry (
        source_id varchar primary key,
        name varchar not null,
        base_url varchar not null,
        asset_classes_json varchar not null,
        expected_fields_json varchar not null,
        frequency varchar not null,
        history_depth varchar not null,
        access_method varchar not null,
        free_or_paid varchar not null,
        license_status varchar not null,
        adapter_status varchar not null,
        data_quality_status varchar not null,
        notes varchar not null,
        owner_role varchar not null
    )
    """,
    """
    create table if not exists asset_class_registry (
        asset_class_id varchar primary key,
        description varchar not null,
        canonical_symbol_format varchar not null,
        source_priority_order_json varchar not null,
        trading_calendar varchar not null,
        price_type varchar not null,
        adjustment_policy varchar not null,
        liquidity_fields_json varchar not null,
        benchmark varchar not null,
        known_risks_json varchar not null
    )
    """,
    """
    create table if not exists instruments (
        asset_id varchar primary key,
        symbol varchar not null,
        source_symbol varchar not null,
        asset_class varchar not null,
        exchange varchar not null,
        sector varchar not null,
        industry varchar not null,
        country varchar not null,
        currency varchar not null,
        lot_size double,
        tick_size double,
        point_value double,
        is_active boolean not null,
        valid_from varchar not null,
        valid_to varchar,
        source_id varchar not null
    )
    """,
    """
    create table if not exists symbol_mappings (
        mapping_id varchar primary key,
        source_id varchar not null,
        asset_id varchar not null,
        asset_class varchar not null,
        source_symbol varchar not null,
        canonical_symbol varchar not null,
        valid_from varchar not null,
        valid_to varchar,
        mapping_status varchar not null
    )
    """,
    """
    create table if not exists contract_metadata (
        contract_id varchar primary key,
        asset_id varchar not null,
        source_id varchar not null,
        asset_class varchar not null,
        root varchar not null,
        expiry varchar,
        instrument_type varchar not null,
        roll_rule varchar not null,
        continuous_contract_method varchar not null,
        volume_oi_filter varchar not null,
        near_contract_policy varchar not null,
        source_symbol varchar not null,
        canonical_symbol varchar not null,
        valid_from varchar not null,
        valid_to varchar
    )
    """,
    """
    create table if not exists source_raw_files (
        raw_file_id varchar primary key,
        source_id varchar not null,
        asset_id varchar,
        asset_class varchar not null,
        source_url varchar not null,
        file_path varchar not null,
        file_format varchar not null,
        source_date varchar not null,
        fetched_at varchar not null,
        checksum varchar not null,
        byte_size bigint not null,
        freshness varchar not null,
        notes varchar not null
    )
    """,
    """
    create table if not exists vwap_observations (
        vwap_observation_id varchar primary key,
        source_id varchar not null,
        asset_id varchar not null,
        symbol varchar not null,
        asset_class varchar not null,
        timestamp timestamp not null,
        vwap double not null,
        vwap_kind varchar not null,
        vwap_method varchar not null,
        is_proxy boolean not null,
        currency varchar not null,
        raw_reference varchar not null,
        ingestion_timestamp varchar not null,
        unique(source_id, asset_id, timestamp, vwap_method, raw_reference)
    )
    """,
    """
    create table if not exists industry_metadata_history (
        industry_metadata_id varchar primary key,
        source_id varchar not null,
        asset_id varchar not null,
        symbol varchar not null,
        asset_class varchar not null,
        exchange varchar not null,
        classification_scheme varchar not null,
        sector varchar not null,
        industry varchar not null,
        sub_industry varchar,
        country varchar not null,
        as_of_date varchar not null,
        effective_from varchar not null,
        effective_to varchar,
        point_in_time_status varchar not null,
        source_snapshot_id varchar,
        raw_reference varchar not null,
        ingestion_timestamp varchar not null,
        unique(source_id, asset_id, as_of_date, classification_scheme, raw_reference)
    )
    """,
    """
    create table if not exists data_quality_reports (
        report_id varchar primary key,
        source_id varchar not null,
        asset_class varchar not null,
        dataset_snapshot_id varchar,
        status varchar not null,
        source_gap_count integer not null,
        asset_gap_count integer not null,
        field_gap_count integer not null,
        duplicate_timestamp_count integer not null,
        generated_at varchar not null,
        summary_json varchar not null,
        notes varchar not null
    )
    """,
    """
    create table if not exists universe_memberships (
        membership_id varchar primary key,
        universe_id varchar not null,
        asset_id varchar not null,
        asset_class varchar not null,
        source_id varchar not null,
        valid_from varchar not null,
        valid_to varchar,
        is_member boolean not null,
        notes varchar not null
    )
    """,
    """
    create table if not exists point_in_time_metadata_status (
        status_id varchar primary key,
        asset_id varchar not null,
        source_id varchar not null,
        metadata_type varchar not null,
        point_in_time_status varchar not null,
        valid_from varchar not null,
        valid_to varchar,
        notes varchar not null
    )
    """,
    """
    create table if not exists canonical_ohlcv (
        source_id varchar not null,
        asset_id varchar not null,
        symbol varchar not null,
        asset_class varchar not null,
        timestamp timestamp not null,
        open double not null,
        high double not null,
        low double not null,
        close double not null,
        volume double not null,
        vwap double,
        adjusted_close double,
        turnover double,
        delivery_volume double,
        open_interest double,
        contract_expiry varchar,
        instrument_type varchar,
        currency varchar not null,
        raw_reference varchar not null,
        ingestion_timestamp varchar not null,
        unique(source_id, asset_id, timestamp, raw_reference)
    )
    """,
    """
    create table if not exists macro_series (
        series_record_id varchar primary key,
        source_id varchar not null,
        asset_id varchar not null,
        symbol varchar not null,
        asset_class varchar not null,
        timestamp varchar not null,
        value double not null,
        frequency varchar not null,
        unit varchar not null,
        release_date varchar not null,
        revision_flag varchar not null,
        realtime_start varchar,
        realtime_end varchar,
        raw_reference varchar not null,
        ingestion_timestamp varchar not null,
        unique(source_id, asset_id, timestamp, raw_reference)
    )
    """,
)
