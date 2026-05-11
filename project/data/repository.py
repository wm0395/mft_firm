from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from project.backtesting.models import BacktestResult
from project.common.models import Asset, Position, RawDataPoint, Signal, TradeIdea, TradeOutcome, utc_now_iso
from project.data.db import DuckDBAccess
from project.data.models import HypothesisEvaluation, SignalEvaluation
from project.data.reporting_store import load_backtest_results, load_trade_outcomes, persist_backtest_result
from project.data.row_parsers import build_filters, raw_point_from_row, trade_idea_from_row


class DataRepository:
    def __init__(self, db: DuckDBAccess) -> None:
        self._db = db

    def initialize(self) -> None:
        self._db.initialize_schema()

    def ingest_market_data(
        self,
        asset_symbol: str,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ) -> None:
        market_id = f"market:{asset_symbol}:{timestamp.isoformat()}"
        self._db.execute(
            """
            insert into raw_market_data values (?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do nothing
            """,
            (market_id, asset_symbol, timestamp, open, high, low, close, volume),
        )

    def get_market_data(
        self,
        asset_symbol: str,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
    ) -> tuple[tuple, ...]:
        conditions = ["asset_symbol = ?"]
        params: list[object] = [asset_symbol]
        if start_timestamp is not None:
            conditions.append("timestamp >= ?")
            params.append(start_timestamp)
        if end_timestamp is not None:
            conditions.append("timestamp <= ?")
            params.append(end_timestamp)
        rows = self._db.fetch_all(
            f"""
            select timestamp, open, high, low, close, volume
            from raw_market_data
            where {" and ".join(conditions)}
            order by timestamp
            """,
            params,
        )
        return tuple(rows)

    def persist_signal_evaluation(self, evaluation: SignalEvaluation) -> None:
        self._db.execute(
            """
            insert into signal_evaluations values (?, ?, ?, ?, ?, ?)
            on conflict(signal_id) do update set
                hypothesis_id = excluded.hypothesis_id,
                forward_return_1 = excluded.forward_return_1,
                forward_return_5 = excluded.forward_return_5,
                forward_return_20 = excluded.forward_return_20,
                evaluation_timestamp = excluded.evaluation_timestamp
            """,
            (
                evaluation.signal_id,
                evaluation.hypothesis_id,
                evaluation.forward_return_1,
                evaluation.forward_return_5,
                evaluation.forward_return_20,
                evaluation.evaluation_timestamp,
            ),
        )

    def get_signal_evaluations(self) -> tuple[SignalEvaluation, ...]:
        rows = self._db.fetch_all(
            """
            select signal_id, hypothesis_id, forward_return_1, forward_return_5,
                   forward_return_20, evaluation_timestamp
            from signal_evaluations
            order by evaluation_timestamp, signal_id
            """
        )
        return tuple(SignalEvaluation(*row) for row in rows)

    def persist_backtest_result(self, result: BacktestResult) -> None:
        persist_backtest_result(self._db, result)

    def get_backtest_results(self) -> tuple[BacktestResult, ...]:
        return load_backtest_results(self._db)

    def add_asset(self, symbol: str, name: str, sector: str, market: str) -> Asset:
        if not symbol or not name or not market:
            raise ValueError("symbol, name, and market are required")
        asset = Asset(
            asset_id=f"asset:{symbol.upper()}",
            symbol=symbol.upper(),
            name=name,
            sector=sector,
            market=market,
            is_active=True,
            created_at=utc_now_iso(),
        )
        self._db.execute(
            """
            insert into assets values (?, ?, ?, ?, ?, ?, ?)
            on conflict(asset_id) do nothing
            """,
            (
                asset.asset_id,
                asset.symbol,
                asset.name,
                asset.sector,
                asset.market,
                asset.is_active,
                asset.created_at,
            ),
        )
        return asset

    def list_assets(self) -> tuple[Asset, ...]:
        rows = self._db.fetch_all(
            "select asset_id, symbol, name, sector, market, is_active, created_at from assets order by symbol"
        )
        return tuple(Asset(*row) for row in rows)

    def ingest_raw(self, point: RawDataPoint) -> None:
        self._db.execute(
            """
            insert into raw_data values (?, ?, ?, ?, ?, ?)
            on conflict(asset_id, timestamp, data_type, source) do nothing
            """,
            (
                point.data_id,
                point.asset_id,
                point.timestamp,
                point.data_type,
                json.dumps(point.value, sort_keys=True),
                point.source,
            ),
        )

    def read_raw_values(self, asset_id: str, data_type: str) -> tuple[RawDataPoint, ...]:
        rows = self._db.fetch_all(
            """
            select data_id, asset_id, timestamp, data_type, value_json, source
            from raw_data
            where asset_id = ? and data_type = ?
            order by timestamp
            """,
            (asset_id, data_type),
        )
        return tuple(raw_point_from_row(row) for row in rows)

    def persist_signal(self, signal: Signal) -> None:
        signal_id = f"signal:{signal.asset_id}:{signal.timestamp}:{signal.signal_type}"
        self._db.execute(
            """
            insert into signals values (?, ?, ?, ?, ?, ?, ?)
            on conflict(signal_id) do nothing
            """,
            (
                signal_id,
                signal.asset_id,
                signal.timestamp,
                signal.signal_type,
                signal.value,
                json.dumps(signal.metadata, sort_keys=True),
                signal.is_persistent,
            ),
        )

    def persist_trade_idea(self, trade: TradeIdea) -> None:
        self._db.execute(
            """
            insert into trade_ideas values (?, ?, ?, ?, ?, ?, ?)
            on conflict(trade_id) do nothing
            """,
            (
                trade.trade_id,
                trade.asset_id,
                trade.hypothesis_id,
                trade.version,
                trade.direction,
                trade.confidence,
                json.dumps(trade.signals_snapshot, sort_keys=True),
            ),
        )

    def get_trade_ideas(
        self,
        asset_id: str | None = None,
        hypothesis_id: str | None = None,
        direction: str | None = None,
    ) -> tuple[TradeIdea, ...]:
        where_clause, params = build_filters(
            [
                ("asset_id = ?", asset_id),
                ("hypothesis_id = ?", hypothesis_id),
                ("direction = ?", direction),
            ]
        )
        rows = self._db.fetch_all(
            f"""
            select trade_id, asset_id, hypothesis_id, version, direction, confidence, signals_snapshot_json
            from trade_ideas
            where {where_clause}
            order by trade_id
            """,
            params,
        )
        return tuple(trade_idea_from_row(row) for row in rows)

    def get_open_trade_ideas(
        self,
        asset_id: str | None = None,
        hypothesis_id: str | None = None,
        direction: str | None = None,
    ) -> tuple[TradeIdea, ...]:
        where_clause, params = build_filters(
            [
                ("ti.asset_id = ?", asset_id),
                ("ti.hypothesis_id = ?", hypothesis_id),
                ("ti.direction = ?", direction),
            ]
        )
        rows = self._db.fetch_all(
            f"""
            select ti.trade_id, ti.asset_id, ti.hypothesis_id, ti.version,
                   ti.direction, ti.confidence, ti.signals_snapshot_json
            from trade_ideas ti
            left join decisions d on ti.trade_id = d.trade_id
            where d.decision_id is null and {where_clause}
            order by ti.trade_id
            """,
            params,
        )
        return tuple(trade_idea_from_row(row) for row in rows)

    def persist_hypothesis_evaluation(self, evaluation: HypothesisEvaluation) -> None:
        self._db.execute(
            """
            insert into hypothesis_evaluations values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(evaluation_id) do update set
                direction = excluded.direction,
                confidence = excluded.confidence,
                signals_snapshot_json = excluded.signals_snapshot_json,
                explanation_json = excluded.explanation_json,
                generated_trade_idea = excluded.generated_trade_idea,
                validation_result_json = excluded.validation_result_json,
                created_at = excluded.created_at,
                experiment_id = excluded.experiment_id,
                research_run_id = excluded.research_run_id,
                dataset_snapshot_id = excluded.dataset_snapshot_id
            """,
            (
                evaluation.evaluation_id,
                evaluation.asset_id,
                evaluation.hypothesis_id,
                evaluation.hypothesis_version,
                evaluation.timestamp,
                evaluation.direction,
                evaluation.confidence,
                evaluation.signals_snapshot_json,
                evaluation.explanation_json,
                evaluation.generated_trade_idea,
                evaluation.validation_result_json,
                evaluation.created_at,
                evaluation.experiment_id,
                evaluation.research_run_id,
                evaluation.dataset_snapshot_id,
            ),
        )

    def get_hypothesis_evaluations(
        self,
        asset_id: str | None = None,
        hypothesis_id: str | None = None,
    ) -> tuple[HypothesisEvaluation, ...]:
        where_clause, params = build_filters(
            [("asset_id = ?", asset_id), ("hypothesis_id = ?", hypothesis_id)]
        )
        rows = self._db.fetch_all(
            f"""
            select evaluation_id, asset_id, hypothesis_id, hypothesis_version, timestamp,
                   direction, confidence, signals_snapshot_json, explanation_json,
                   generated_trade_idea, validation_result_json, created_at,
                   experiment_id, research_run_id, dataset_snapshot_id
            from hypothesis_evaluations
            where {where_clause}
            order by timestamp, evaluation_id
            """,
            params,
        )
        return tuple(HypothesisEvaluation(*row) for row in rows)

    def persist_position(self, position: Position) -> None:
        self._db.execute(
            """
            insert into positions values (?, ?, ?, ?, ?, ?)
            on conflict(position_id) do update set
                exit_price = excluded.exit_price,
                pnl = excluded.pnl,
                status = excluded.status
            """,
            (
                position.position_id,
                position.trade_id,
                position.entry_price,
                position.exit_price,
                position.pnl,
                position.status,
            ),
        )

    def get_positions(
        self,
        asset_id: str | None = None,
        hypothesis_id: str | None = None,
        direction: str | None = None,
        status: str | None = None,
    ) -> tuple[Position, ...]:
        where_clause, params = build_filters(
            [
                ("ti.asset_id = ?", asset_id),
                ("ti.hypothesis_id = ?", hypothesis_id),
                ("ti.direction = ?", direction),
                ("p.status = ?", status),
            ]
        )
        rows = self._db.fetch_all(
            f"""
            select p.position_id, p.trade_id, p.entry_price, p.exit_price, p.pnl, p.status
            from positions p
            join trade_ideas ti on p.trade_id = ti.trade_id
            where {where_clause}
            order by p.position_id
            """,
            params,
        )
        return tuple(Position(*row) for row in rows)

    def persist_decision(self, decision: Any) -> None:
        self._db.execute(
            """
            insert into decisions values (?, ?, ?, ?, ?, ?)
            on conflict(decision_id) do nothing
            """,
            (
                decision.decision_id,
                decision.trade_id,
                decision.action,
                decision.structured_reason,
                decision.notes,
                decision.created_at,
            ),
        )

    def get_decisions(self, trade_id: str | None = None) -> tuple[tuple, ...]:
        where_clause, params = build_filters([("trade_id = ?", trade_id)])
        return tuple(self._db.fetch_all(
            f"""
            select decision_id, trade_id, action, structured_reason, notes, created_at
            from decisions
            where {where_clause}
            order by created_at, decision_id
            """,
            params,
        ))

    def get_trade_outcomes(self) -> tuple[TradeOutcome, ...]:
        return load_trade_outcomes(self._db)
